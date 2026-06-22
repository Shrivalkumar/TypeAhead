"""Type-safe configuration loaded from .env via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — every value can be overridden via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # PostgreSQL
    database_url: str = "postgresql://typeahead:typeahead@localhost:5432/typeahead"
    db_pool_min: int = 5
    db_pool_max: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Cache
    cache_node_count: int = 3
    cache_vnodes: int = 150
    cache_ttl_seconds: int = 300

    # Batch Writer
    batch_flush_interval_seconds: float = 5.0
    batch_max_buffer_size: int = 100

    # Trending
    trending_enabled: bool = True
    trending_window_minutes: int = 60
    trending_alpha: float = 0.3
    trending_beta: float = 0.7
    trending_cleanup_interval_seconds: int = 300


settings = Settings()
