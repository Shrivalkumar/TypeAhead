from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Query(Base):
    """Core table storing all-time query counts."""
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String, nullable=False, unique=True)
    count = Column(BigInteger, nullable=False, default=1)
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=text("NOW()")
    )

    __table_args__ = (
        # GIN trigram index for fast fuzzy/prefix matching
        Index(
            "idx_queries_query_trgm",
            text("query gin_trgm_ops"),
            postgresql_using="gin",
        ),
        # B-Tree index with text_pattern_ops for fast exact prefix LIKE 'foo%' queries
        Index(
            "idx_queries_query_btree",
            text("query text_pattern_ops"),
        ),
        # Index for ORDER BY count DESC
        Index("idx_queries_count_desc", count.desc()),
    )


class RecentSearch(Base):
    """Append-only table tracking recent searches for trending logic."""
    __tablename__ = "recent_searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String, nullable=False)
    searched_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=text("NOW()")
    )

    __table_args__ = (
        Index("idx_recent_searched_at", searched_at),
        Index("idx_recent_query", query),
    )
