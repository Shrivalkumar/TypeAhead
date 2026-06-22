from fastapi import APIRouter, Query
from src.schemas.models import SuggestResponse
from src.services.suggestion_service import get_suggestions

router = APIRouter()

@router.get("/suggest", response_model=SuggestResponse)
async def suggest(q: str = Query(default="", description="The prefix to suggest for")):
    """Fetch top 10 suggestions matching the prefix."""
    ranking_mode, suggestions = await get_suggestions(q)
    return SuggestResponse(
        prefix=q,
        ranking_mode=ranking_mode,
        suggestions=suggestions
    )
