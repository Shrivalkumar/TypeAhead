import asyncio
import csv
import time
import zipfile
import io
from collections import defaultdict

from src.db.connection import create_pool, close_pool
from src.utils.logger import get_logger

logger = get_logger("seed")

DATASET_ZIP = "data/dataset.zip"
DATASET_TXT = "dataset.txt"

async def main():
    logger.info("seed_starting", dataset=DATASET_ZIP)
    start_time = time.perf_counter()

    # 1. Read and aggregate counts in memory
    logger.info("reading_dataset_and_aggregating")
    counts = defaultdict(int)
    
    try:
        with zipfile.ZipFile(DATASET_ZIP, "r") as zf:
            with zf.open(DATASET_TXT, "r") as f:
                text_file = io.TextIOWrapper(f, encoding="utf-8")
                reader = csv.reader(text_file, delimiter="\t")
                
                # Skip header
                try:
                    next(reader)
                except StopIteration:
                    logger.error("dataset_empty")
                    return

                for row in reader:
                    if len(row) < 2:
                        continue
                    query = row[1].strip().lower()
                    if query and query != "-":
                        counts[query] += 1
    except FileNotFoundError:
        logger.error("dataset_zip_not_found")
        return

    total_unique = len(counts)
    logger.info("aggregation_complete", unique_queries=total_unique)

    if total_unique == 0:
        logger.error("no_queries_found")
        return

    # Prepare records for asyncpg copy_records_to_table
    # The table schema is: id (serial), query, count, updated_at
    # copy_records_to_table accepts a list of tuples matching the columns exactly.
    # We can omit id and updated_at if we specify the columns.
    records = [(q, c) for q, c in counts.items()]

    # 2. Insert into PostgreSQL
    pool = await create_pool()
    logger.info("checking_postgres_state")
    
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM queries;")
        if count > 0:
            logger.info("database_already_seeded", current_count=count)
        else:
            logger.info("inserting_into_postgres")
            # Fast bulk insert
            await conn.copy_records_to_table(
                "queries",
                columns=["query", "count"],
                records=records
            )

    await close_pool()
    
    duration = time.perf_counter() - start_time
    logger.info(
        "seed_complete",
        rows_inserted=total_unique,
        duration_seconds=round(duration, 2)
    )

if __name__ == "__main__":
    asyncio.run(main())
