from pydantic import BaseModel, Field

class SuggestionItem(BaseModel):
    query: str
    count: int
    recent_count: int | None = None
    trending_score: float | None = None

class SuggestResponse(BaseModel):
    prefix: str
    ranking_mode: str = "all_time"
    suggestions: list[SuggestionItem]

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)

class SearchResponse(BaseModel):
    message: str = "Searched"

class CacheDebugResponse(BaseModel):
    prefix: str
    cache_node: str
    hit: bool
    cached_at: str | None = None
    ttl_remaining_seconds: int | None = None
    total_hits: int | None = None
    total_misses: int | None = None
    hit_rate: str | None = None
