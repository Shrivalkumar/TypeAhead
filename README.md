# TypeAhead: Distributed Search Suggestion Engine

TypeAhead is a lightning-fast, highly scalable search suggestion system built to handle real-time prefix matching, trending searches, and high-throughput query logging. 

This project was built to satisfy the **Search Typeahead System Assignment** requirements, demonstrating advanced backend data-system design, distributed caching, and optimized database reads/writes.

<img width="1469" height="833" alt="Screenshot 2026-06-22 at 8 22 46 AM" src="https://github.com/user-attachments/assets/55f6e1db-ebfc-4287-a9da-681315d47136" />




## 🚀 Features & Architecture Overview

The system is fully containerized and consists of four main services:

1. **Frontend (React + Vite)**: A minimalist, responsive UI featuring search debouncing, fallback states, and trending search pills.
2. **Backend API (FastAPI + Python 3.12)**: A high-performance async API serving suggestions and logging searches.
3. **Primary Data Store (PostgreSQL)**: Stores over 1.2 million real-world queries. Optimized with `gin_trgm_ops` and `text_pattern_ops` indexes for sub-millisecond prefix text searches.
4. **Distributed Cache (Redis)**: Caches suggestion responses. Implements **Consistent Hashing** to distribute load across multiple logical cache nodes.

---

## 🎯 How It Solves the Assignment Objectives

This project implements all core functional requirements, as well as the advanced 20% bonus tasks:

### 1. Fast Prefix Suggestions (`GET /suggest?q=...`)
Suggestions are fetched using a combination of a Redis Cache layer and highly-indexed PostgreSQL queries. The database leverages B-Tree indexes for exact prefix matching and GIN indexes for fuzzy lookups. The API returns the top 10 results sorted by count.

### 2. Distributed Caching with Consistent Hashing
To ensure horizontal scalability, the caching layer (`Backend/src/cache/cache_manager.py`) simulates a distributed cache topology. It uses the `uhashring` library to map search prefixes to specific virtual nodes, ensuring an even distribution of keys and minimizing cache-miss stampedes when nodes are added or removed.

### 3. Trending Searches (Recency Ranking logic)
The system satisfies the advanced ranking requirement by combining historical popularity with recent activity. 
- Searches submitted via `POST /search` are recorded in an append-only `recent_searches` table.
- A background worker periodically purges searches older than the rolling window (e.g., 60 minutes).
- The `trending_score` is calculated on-the-fly using a weighted formula: `(All_Time_Count * Alpha) + (Recent_Count * Beta)`. This ensures viral short-term trends surface quickly without permanently overwriting historically dominant searches.

### 4. High-Throughput Batch Writes
To prevent database lock contention during traffic spikes, the `POST /search` endpoint does not write directly to the database. Instead, it pushes queries into an async **Batch Writer** (`Backend/src/db/batch_writer.py`). 
The writer buffers requests in memory and aggregates repeated queries before executing a bulk `UPSERT` to PostgreSQL. It flushes periodically based on a configurable time interval or max buffer size.

---

## 🛠️ Quick Start Guide (Zero Setup)

The entire application is fully automated via Docker Compose. You do not need to manually configure Python, Node, or extract the massive dataset.

### Prerequisites
- Docker and Docker Compose installed.

### Run the Application
Simply run the following command in the root directory:
```bash
docker-compose up -d
```

### What happens under the hood?
1. Docker spins up the PostgreSQL and Redis containers.
2. The Backend container waits for the database to become healthy.
3. Once healthy, the Backend automatically runs Alembic database migrations.
4. **Auto-Seeding:** The Backend automatically unzips `dataset.zip` entirely in-memory and bulk-loads 1,244,495 unique queries into PostgreSQL (this takes about 10-20 seconds).
5. The API starts accepting traffic on port `8000`.
6. The Frontend starts serving the UI on port `5173`.

### Access the App
- **Web UI:** [http://localhost:5173](http://localhost:5173)
- **API Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/suggest?q=<prefix>` | Returns up to 10 prefix-matching suggestions sorted by trending score. |
| `POST` | `/search` | Logs a submitted search query to the batch writer buffer. |
| `GET` | `/cache/debug?prefix=<prefix>` | Debugs the consistent hashing logic, showing which cache node owns the key. |
| `GET` | `/health` | Basic API health check. |

## 🧪 Measuring Performance

To test the cache hit rates and system performance, you can monitor the Docker logs:
```bash
docker logs typeahead-backend-1 -f
```
The application features structured logging that outputs `cache_hit`, `cache_miss`, `db_read_latency`, and `batch_flush_metrics`.

## 🧹 Cleanup
To stop the services and remove the volumes (including wiping the seeded database):
```bash
docker-compose down -v
```
