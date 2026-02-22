from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.graph import Recommendation
from app.services.graph.recommendations import get_recommendations_for_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=List[Recommendation],
    summary="Discover unexplored knowledge paths based on your interests",
)
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of recommendations to return"),
    user: Dict[str, Any] = Depends(get_current_user),
) -> List[Recommendation]:
    """
    Uses Neo4j graph pathfinding to surface entities the user has *not* yet
    explored but are reachable from their known interests via the master
    knowledge graph.

    The algorithm:
    1. Identifies the user's top 5 highest-weight entities as starting points.
    2. Traverses RELATED_TO edges 2–4 hops away.
    3. Filters out entities the user already has an INTERESTED_IN relationship with.
    4. Ranks by graph distance (closer = more directly related).
    5. Returns the top `limit` results with explanatory metadata.
    """
    user_id: str = user["sub"]
    try:
        recs = await get_recommendations_for_user(user_id, limit=limit)
    except Exception as exc:
        logger.error("Failed to generate recommendations for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not generate recommendations. Please try again.",
        ) from exc

    return recs
