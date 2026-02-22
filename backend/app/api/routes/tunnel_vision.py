from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.tunnel_vision import TunnelVisionReport
from app.services.gdelt.world_today import fetch_world_today_events
from app.services.graph.tunnel_vision import (
    compute_tunnel_vision_score,
    refresh_world_today_in_neo4j,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# How many World Today events to fetch from GDELT on each refresh.
_WORLD_TODAY_MAX = 50


@router.get(
    "/score",
    response_model=TunnelVisionReport,
    summary="Get the user's Tunnel Vision Score",
)
async def get_tunnel_vision_score(
    user: Dict[str, Any] = Depends(get_current_user),
) -> TunnelVisionReport:
    """
    Returns the authenticated user's **Tunnel Vision Score** — a measure of
    how disconnected the user is from the 50 major global events currently
    happening in the world (sourced from GDELT).

    A score of **0** means the user is connected to every active world event.
    A score of **100** means the user is connected to none of them.

    The response also includes:
    - The list of events the user *is* connected to.
    - The events the user is *missing*.
    - **Learning bridges** — shortest associative paths from the user's known
      interests to the events they are missing, with human-readable
      explanations.

    **Note:** The World Today nodes must be refreshed first via
    ``POST /tunnel-vision/refresh`` before scores are meaningful.
    """
    user_id: str = user["sub"]
    try:
        report = await compute_tunnel_vision_score(user_id)
    except Exception as exc:
        logger.error("Failed to compute Tunnel Vision Score for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not compute Tunnel Vision Score. Please try again.",
        ) from exc

    return report


@router.post(
    "/refresh",
    summary="Refresh the World Today nodes from GDELT",
    response_description="Number of WorldEvent nodes written to Neo4j",
)
async def refresh_world_today(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Fetches the **50 most prominent global news events** from the GDELT Doc
    API (last 24 hours) and upserts them as ``WorldEvent`` nodes in Neo4j.

    For each new event the service also:
    - Creates ``COVERS`` edges to matching ``Category`` nodes (using keyword
      analysis of the article title).
    - Creates ``ABOUT`` edges from any existing ``Entity`` nodes whose names
      appear in the article title.

    This operation is **idempotent** — re-running it only updates timestamps
    on existing nodes and does not create duplicates.

    Typically called once per day by a scheduled job, or manually triggered
    before requesting a score.
    """
    try:
        articles = await fetch_world_today_events(max_events=_WORLD_TODAY_MAX)
    except Exception as exc:
        logger.error("Failed to fetch World Today events from GDELT: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch events from GDELT. Please try again later.",
        ) from exc

    if not articles:
        return {"written": 0, "message": "GDELT returned no articles."}

    try:
        written = await refresh_world_today_in_neo4j(articles)
    except Exception as exc:
        logger.error("Failed to write World Today events to Neo4j: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not persist World Today events. Please try again.",
        ) from exc

    logger.info(
        "World Today refresh triggered by user %s: %d events written",
        user["sub"],
        written,
    )
    return {
        "written": written,
        "message": f"Successfully refreshed {written} World Today events.",
    }
