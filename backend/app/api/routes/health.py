from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.neo4j_client import health_check

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Full health check")
async def health() -> dict:
    """
    Returns the overall service health including Neo4j connectivity.
    Suitable for uptime monitors that need real dependency checks.
    """
    neo4j_ok = await health_check()
    return {
        "status": "ok",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "neo4j": "ok" if neo4j_ok else "error",
        "version": "1.0.0",
    }


@router.get("/health/ping", summary="Lightweight ping (cron keep-alive)")
async def ping() -> dict:
    """
    Instant response with no external calls.
    Use this endpoint for free-tier cron-job keep-alives to avoid
    incurring unnecessary Neo4j connection overhead.
    """
    return {"pong": True}
