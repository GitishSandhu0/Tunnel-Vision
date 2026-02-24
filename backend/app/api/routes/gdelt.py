from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.gdelt import GDELTEnrichResponse, GDELTNewsResponse
from app.services.gdelt.client import GDELTClient
from app.services.graph.neo4j_ingestion import (
    get_graph_stats,
    ingest_gdelt_articles,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum articles fetched from GDELT per entity during graph enrichment.
_ENRICH_MAX_RECORDS = 5
# Maximum entities taken from the user's graph for enrichment.
_ENRICH_TOP_N = 5
# Maximum articles returned by the /news endpoint.
_NEWS_MAX_RECORDS = 10


@router.get(
    "/news",
    response_model=GDELTNewsResponse,
    summary="Search GDELT for recent news about an entity",
)
async def get_gdelt_news(
    entity: str = Query(..., min_length=1, max_length=200, description="Entity name to search for"),
    max_records: int = Query(default=_NEWS_MAX_RECORDS, ge=1, le=50, description="Max articles to return"),
    user: Dict[str, Any] = Depends(get_current_user),
) -> GDELTNewsResponse:
    """
    Proxy the GDELT Doc API v2 to return recent news articles that mention
    the requested entity.

    This endpoint does **not** write anything to Neo4j; it is a real-time
    read-only search suitable for the frontend news sidebar.
    """
    async with GDELTClient() as client:
        try:
            articles = await client.search_articles(entity, max_records=max_records)
        except Exception as exc:
            logger.error("GDELT news search failed for entity '%s': %s", entity, exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not reach the GDELT API. Please try again later.",
            ) from exc

    return GDELTNewsResponse(
        entity_name=entity,
        articles=articles,
        total=len(articles),
    )


@router.post(
    "/enrich",
    response_model=GDELTEnrichResponse,
    summary="Enrich the user's knowledge graph with real-time GDELT news",
)
async def enrich_graph_with_gdelt(
    user: Dict[str, Any] = Depends(get_current_user),
) -> GDELTEnrichResponse:
    """
    Fetch recent GDELT news articles for the user's top interest entities and
    persist them into Neo4j as ``GDELTArticle`` nodes linked via
    ``MENTIONED_IN`` edges.

    This enriches the knowledge graph with real-world context, allowing future
    queries to surface articles relevant to the user's interests.

    The operation is fully idempotent: re-running it updates existing article
    nodes without creating duplicates.
    """
    user_id: str = user["sub"]

    # Retrieve the user's top entities from Neo4j stats
    try:
        stats = await get_graph_stats(user_id)
    except Exception as exc:
        logger.error("Failed to fetch graph stats for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GDELT - Could not retrieve graph data. Please try again.",
        ) from exc

    top_entities = [e["name"] for e in stats.top_entities[:_ENRICH_TOP_N]]
    if not top_entities:
        return GDELTEnrichResponse()

    enriched_entities: List[str] = []
    total_articles = 0

    async with GDELTClient() as client:
        for entity_name in top_entities:
            try:
                articles = await client.search_articles(
                    entity_name, max_records=_ENRICH_MAX_RECORDS
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "GDELT fetch failed for entity '%s' (user %s): %s",
                    entity_name,
                    user_id,
                    exc,
                )
                continue

            if not articles:
                continue

            written = await ingest_gdelt_articles(entity_name, articles)
            if written:
                enriched_entities.append(entity_name)
                total_articles += written

    logger.info(
        "GDELT enrichment complete for user %s: %d entities, %d articles",
        user_id,
        len(enriched_entities),
        total_articles,
    )

    return GDELTEnrichResponse(
        enriched_entities=enriched_entities,
        total_articles_ingested=total_articles,
    )
