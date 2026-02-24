from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.graph import GraphData, GraphStats
from app.services.graph.neo4j_ingestion import get_user_graph, get_graph_stats

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/data",
    response_model=GraphData,
    summary="Get the authenticated user's knowledge graph",
)
async def get_graph_data(
    user: Dict[str, Any] = Depends(get_current_user),
) -> GraphData:
    """
    Returns all graph nodes and directed links for the current user.

    Nodes include:
    - The user's interest entities (PERSON, ORG, TECH, TOPIC, PLACE …)
    - Broad knowledge categories they've been mapped to

    Links represent INTERESTED_IN and EXPLORES relationships.
    Suitable for direct consumption by a D3 / Three.js force-directed graph.
    """
    user_id: str = user["sub"]
    try:
        graph_data = await get_user_graph(user_id)
    except Exception as exc:
        logger.error("Failed to fetch graph data for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph - Could not retrieve graph data. Please try again.",
        ) from exc

    if graph_data is None:
        return GraphData(nodes=[], links=[], user_id=user_id)

    return graph_data


@router.get(
    "/stats",
    response_model=GraphStats,
    summary="Get aggregate statistics for the user's knowledge graph",
)
async def get_stats(
    user: Dict[str, Any] = Depends(get_current_user),
) -> GraphStats:
    """
    Returns lightweight count statistics and top-N entities/categories.
    Used for dashboard summary cards without transmitting the full graph.
    """
    user_id: str = user["sub"]
    try:
        stats = await get_graph_stats(user_id)
    except Exception as exc:
        logger.error("Failed to fetch graph stats for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not retrieve graph statistics. Please try again.",
        ) from exc

    return stats
