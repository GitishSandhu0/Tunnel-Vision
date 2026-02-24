from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from neo4j.exceptions import Neo4jError

from app.core.neo4j_client import get_driver, get_session_kwargs
from app.models.gdelt import GDELTArticle
from app.models.tunnel_vision import LearningBridge, TunnelVisionReport, WorldEvent
from app.services.gdelt.world_today import _extract_categories

logger = logging.getLogger(__name__)

# How many of the top missed events to generate bridges for.
_MAX_BRIDGES = 10
# Minimum entity name length to match against article titles (avoids noise).
_MIN_ENTITY_NAME_LENGTH = 4


# ---------------------------------------------------------------------------
# Severity helpers
# ---------------------------------------------------------------------------

def _score_to_severity(score: int) -> str:
    """Map a numeric Tunnel Vision Score to a human-readable severity label."""
    if score <= 20:
        return "Aware"
    if score <= 40:
        return "Moderate"
    if score <= 60:
        return "Narrowing"
    if score <= 80:
        return "High"
    return "Critical"


# ---------------------------------------------------------------------------
# WorldEvent ingestion
# ---------------------------------------------------------------------------


async def refresh_world_today_in_neo4j(articles: List[GDELTArticle]) -> int:
    """
    Persist a list of GDELT articles as ``WorldEvent`` nodes in Neo4j and wire
    them into the global knowledge graph:

    1. MERGE each ``WorldEvent`` node (keyed by URL) — idempotent.
    2. Create ``COVERS`` edges to matching ``Category`` nodes based on keyword
       analysis of the article title.
    3. Create ``ABOUT`` edges from existing ``Entity`` nodes whose names appear
       verbatim in the article title (case-insensitive substring match).

    Returns:
        Number of WorldEvent nodes successfully written/updated.
    """
    if not articles:
        return 0

    driver = get_driver()
    written = 0

    async with driver.session(**get_session_kwargs()) as session:
        for article in articles:
            if not article.url:
                continue
            try:
                # 1. Upsert the WorldEvent node
                await session.run(
                    """
                    MERGE (w:WorldEvent {url: $url})
                      ON CREATE SET
                        w.name       = $name,
                        w.domain     = $domain,
                        w.seen_date  = $seen_date,
                        w.fetched_at = datetime()
                      ON MATCH SET
                        w.name       = $name,
                        w.fetched_at = datetime()
                    """,
                    url=article.url,
                    name=article.title,
                    domain=article.domain,
                    seen_date=article.seen_date,
                )

                # 2. Link to matching Category nodes (keyword-based)
                for cat_name in _extract_categories(article.title):
                    await session.run(
                        """
                        MATCH (c:Category {name: $cat})
                        MATCH (w:WorldEvent {url: $url})
                        MERGE (w)-[:COVERS]->(c)
                        """,
                        cat=cat_name,
                        url=article.url,
                    )

                # 3. Link to existing Entity nodes whose names appear in the title
                await session.run(
                    """
                    MATCH (e:Entity)
                    WHERE size(e.name) >= $min_len
                      AND toLower($title) CONTAINS toLower(e.name)
                    MATCH (w:WorldEvent {url: $url})
                    MERGE (e)-[:ABOUT]->(w)
                    """,
                    min_len=_MIN_ENTITY_NAME_LENGTH,
                    title=article.title,
                    url=article.url,
                )

                written += 1
            except Neo4jError as exc:
                logger.warning("Failed to write WorldEvent '%s': %s", article.url, exc)

    logger.info("WorldEvent refresh: %d/%d events written to Neo4j", written, len(articles))
    return written


# ---------------------------------------------------------------------------
# Learning bridge finder
# ---------------------------------------------------------------------------


async def _find_learning_bridge(
    session: Any,
    user_id: str,
    event: Dict[str, Any],
) -> Optional[LearningBridge]:
    """
    Try three progressively broader graph queries to find a bridge between
    the user's known interests and a WorldEvent they are missing.

    Priority (shortest / most specific path first):
    1. Entity-level bridge: user's INTERESTED_IN entity belongs to a Category
       that the WorldEvent also COVERS.
    2. Category-level bridge: user directly EXPLORES a Category that the
       WorldEvent COVERS (no specific entity anchor).

    Returns ``None`` if no bridge can be found.
    """
    event_url: str = event["url"]
    event_name: str = event["name"]

    # --- Bridge 1: entity → shared category ← world event ---
    result = await session.run(
        """
        MATCH (w:WorldEvent {url: $url})-[:COVERS]->(c:Category)
        MATCH (u:User {id: $user_id})-[:INTERESTED_IN]->(e:Entity)-[:BELONGS_TO]->(c)
        RETURN e.name AS anchor, c.name AS category
        LIMIT 1
        """,
        url=event_url,
        user_id=user_id,
    )
    record = await result.single()
    if record:
        anchor: str = record["anchor"]
        category: str = record["category"]
        return LearningBridge(
            world_event_name=event_name,
            world_event_url=event_url,
            user_anchor_entity=anchor,
            via_category=category,
            explanation=(
                f"You follow \"{anchor}\" (in {category}). "
                f"This global event also falls under {category} — "
                "expanding here broadens your world view."
            ),
            distance=3,
        )

    # --- Bridge 2: user's explored category ← world event ---
    result = await session.run(
        """
        MATCH (w:WorldEvent {url: $url})-[:COVERS]->(c:Category)
        MATCH (u:User {id: $user_id})-[:EXPLORES]->(c)
        RETURN c.name AS category
        LIMIT 1
        """,
        url=event_url,
        user_id=user_id,
    )
    record = await result.single()
    if record:
        category = record["category"]
        return LearningBridge(
            world_event_name=event_name,
            world_event_url=event_url,
            user_anchor_entity="",
            via_category=category,
            explanation=(
                f"You already explore {category}. "
                "This event is happening right now in that domain — "
                "following it keeps you grounded in current global reality."
            ),
            distance=2,
        )

    return None


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------


async def compute_tunnel_vision_score(user_id: str) -> TunnelVisionReport:
    """
    Compute the Tunnel Vision Score for a user.

    Algorithm:
    1. Load the 50 most-recently fetched WorldEvent nodes from Neo4j.
    2. Determine which events the user is already connected to via:
       a. ``(User)-[:INTERESTED_IN]->(Entity)-[:ABOUT]->(WorldEvent)``
       b. ``(User)-[:EXPLORES]->(Category)<-[:COVERS]-(WorldEvent)``
    3. Score = round((missed / total) × 100).   Higher → more tunnel vision.
    4. For the top unconnected events, find learning bridges.

    Returns a :class:`~app.models.tunnel_vision.TunnelVisionReport`.
    """
    driver = get_driver()

    async with driver.session(**get_session_kwargs()) as session:
        # 1. All WorldEvent nodes (most recent first, cap at 50)
        all_events_result = await session.run(
            """
            MATCH (w:WorldEvent)
            RETURN w.name     AS name,
                   w.url      AS url,
                   w.domain   AS domain,
                   w.seen_date AS seen_date
            ORDER BY w.fetched_at DESC
            LIMIT 50
            """
        )
        all_events: List[Dict[str, Any]] = [
            dict(r) async for r in all_events_result
        ]

        if not all_events:
            logger.info("No WorldEvent nodes found – score defaults to 0 for user %s", user_id)
            return TunnelVisionReport(
                user_id=user_id,
                score=0,
                severity="Aware",
                total_world_events=0,
                connected_count=0,
            )

        # 2. Connected WorldEvent URLs for this user (either path)
        connected_result = await session.run(
            """
            MATCH (u:User {id: $user_id})-[:INTERESTED_IN]->(e:Entity)-[:ABOUT]->(w:WorldEvent)
            RETURN DISTINCT w.url AS url
            UNION
            MATCH (u:User {id: $user_id})-[:EXPLORES]->(c:Category)<-[:COVERS]-(w:WorldEvent)
            RETURN DISTINCT w.url AS url
            """,
            user_id=user_id,
        )
        connected_urls: Set[str] = {r["url"] async for r in connected_result}

        # 3. Score
        total = len(all_events)
        connected_count = sum(1 for e in all_events if e["url"] in connected_urls)
        missed_events_raw = [e for e in all_events if e["url"] not in connected_urls]

        score = round(((total - connected_count) / total) * 100) if total > 0 else 0
        severity = _score_to_severity(score)

        # 4. Learning bridges for top missed events
        bridges: List[LearningBridge] = []
        for event in missed_events_raw[:_MAX_BRIDGES]:
            bridge = await _find_learning_bridge(session, user_id, event)
            if bridge:
                bridges.append(bridge)

    logger.info(
        "Tunnel Vision Score for user %s: %d/100 (%s) – %d/%d events connected, %d bridges",
        user_id, score, severity, connected_count, total, len(bridges),
    )

    return TunnelVisionReport(
        user_id=user_id,
        score=score,
        severity=severity,
        total_world_events=total,
        connected_count=connected_count,
        connected_event_names=[
            e["name"] for e in all_events if e["url"] in connected_urls
        ],
        missed_events=[WorldEvent(**e) for e in missed_events_raw],
        learning_bridges=bridges,
    )
