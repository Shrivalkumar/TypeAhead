from fastapi import APIRouter
from src.schemas.models import SearchRequest, SearchResponse
from src.services.search_service import submit_search

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Submit a search query and record it."""
    return await submit_search(request.query)
