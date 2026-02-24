from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from neo4j.exceptions import Neo4jError

from app.core.neo4j_client import get_driver, get_session_kwargs
from app.models.entities import ExtractionResult
from app.models.gdelt import GDELTArticle
from app.models.graph import GraphData, GraphEdge, GraphNode, GraphStats

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


async def ingest_user_entities(user_id: str, result: ExtractionResult) -> None:
    """
    Persist an :class:`ExtractionResult` into Neo4j using the
    **Shared Master Node** architecture:

    - Entity nodes are global (shared across all users).  Two users who both
      follow "Python" point to the *same* Entity node — this enables
      cross-user pathfinding for recommendations.
    - User→Entity edges carry a personal ``weight`` that reflects how
      prominently that topic appears in *this* user's data.
    - Category nodes are also global; Entity→Category edges are shared.
    - MERGE is used throughout so the function is fully idempotent — calling
      it multiple times with the same data produces exactly one node/edge.
    """
    driver = get_driver()
    async with driver.session(**get_session_kwargs()) as session:
        # 1. Upsert the User node
        await session.run(
            """
            MERGE (u:User {id: $user_id})
            SET u.last_updated = datetime()
            """,
            user_id=user_id,
        )

        # 2. Upsert each Entity (global) + personal INTERESTED_IN edge
        for entity in result.entities:
            await session.run(
                """
                MERGE (e:Entity {name: $name, type: $type})
                  ON CREATE SET e.created = datetime()
                SET e.last_seen = datetime()

                WITH e
                MATCH (u:User {id: $user_id})
                MERGE (u)-[r:INTERESTED_IN]->(e)
                SET r.weight    = $weight,
                    r.mentions  = $mentions,
                    r.updated   = datetime()
                """,
                name=entity.name,
                type=entity.type,
                weight=entity.weight,
                mentions=entity.mentions,
                user_id=user_id,
            )

        # 3. Upsert each Category (global) + personal EXPLORES edge
        #    + Entity→Category edges for entities in this category
        for category in result.categories:
            await session.run(
                """
                MERGE (c:Category {name: $name})
                  ON CREATE SET c.created = datetime()

                WITH c
                MATCH (u:User {id: $user_id})
                MERGE (u)-[r:EXPLORES]->(c)
                SET r.weight  = $weight,
                    r.updated = datetime()
                """,
                name=category.name,
                weight=category.weight,
                user_id=user_id,
            )

            # Link entities to their category
            for entity_name in category.entities:
                await session.run(
                    """
                    MATCH (e:Entity {name: $entity_name})
                    MATCH (c:Category {name: $cat_name})
                    MERGE (e)-[:BELONGS_TO]->(c)
                    """,
                    entity_name=entity_name,
                    cat_name=category.name,
                )

    logger.info(
        "Neo4j ingestion complete for user %s: %d entities, %d categories",
        user_id,
        len(result.entities),
        len(result.categories),
    )


# ---------------------------------------------------------------------------
# Graph retrieval
# ---------------------------------------------------------------------------


async def get_user_graph(user_id: str) -> Optional[GraphData]:
    """
    Return all nodes and edges that make up the user's personal knowledge graph.

    Nodes:
      - The user's Entity nodes (via INTERESTED_IN)
      - The Category nodes (via EXPLORES)

    Edges:
      - INTERESTED_IN (User → Entity)
      - EXPLORES (User → Category)
      - BELONGS_TO (Entity → Category)
    """
    driver = get_driver()
    nodes: Dict[str, GraphNode] = {}
    links: List[GraphEdge] = []

    async with driver.session(**get_session_kwargs()) as session:
        # Fetch User → Entity relationships
        result = await session.run(
            """
            MATCH (u:User {id: $user_id})-[r:INTERESTED_IN]->(e:Entity)
            RETURN e.name AS name, e.type AS type,
                   r.weight AS weight, r.mentions AS mentions
            ORDER BY r.weight DESC
            LIMIT 200
            """,
            user_id=user_id,
        )
        async for record in result:
            node_id = f"{record['name']}::{record['type']}"
            nodes[node_id] = GraphNode(
                id=node_id,
                label=record["name"],
                type="Entity",
                weight=float(record["weight"] or 0),
                properties={"entity_type": record["type"], "mentions": record["mentions"]},
            )
            links.append(
                GraphEdge(
                    source=f"user::{user_id}",
                    target=node_id,
                    relationship="INTERESTED_IN",
                    weight=float(record["weight"] or 0),
                )
            )

        # Fetch User → Category relationships
        result = await session.run(
            """
            MATCH (u:User {id: $user_id})-[r:EXPLORES]->(c:Category)
            RETURN c.name AS name, r.weight AS weight
            ORDER BY r.weight DESC
            LIMIT 50
            """,
            user_id=user_id,
        )
        async for record in result:
            node_id = f"category::{record['name']}"
            nodes[node_id] = GraphNode(
                id=node_id,
                label=record["name"],
                type="Category",
                weight=float(record["weight"] or 0),
            )
            links.append(
                GraphEdge(
                    source=f"user::{user_id}",
                    target=node_id,
                    relationship="EXPLORES",
                    weight=float(record["weight"] or 0),
                )
            )

        # Fetch Entity → Category edges for entities already in our node set
        if nodes:
            entity_names = [
                n.label for n in nodes.values() if n.type == "Entity"
            ]
            result = await session.run(
                """
                MATCH (e:Entity)-[:BELONGS_TO]->(c:Category)
                WHERE e.name IN $entity_names
                RETURN e.name AS entity_name, e.type AS entity_type, c.name AS cat_name
                """,
                entity_names=entity_names,
            )
            async for record in result:
                src_id = f"{record['entity_name']}::{record['entity_type']}"
                tgt_id = f"category::{record['cat_name']}"
                if src_id in nodes:
                    links.append(
                        GraphEdge(
                            source=src_id,
                            target=tgt_id,
                            relationship="BELONGS_TO",
                            weight=1.0,
                        )
                    )

    # Add the user node itself
    user_node_id = f"user::{user_id}"
    nodes[user_node_id] = GraphNode(
        id=user_node_id,
        label="You",
        type="User",
        weight=1.0,
    )

    return GraphData(
        nodes=list(nodes.values()),
        links=links,
        user_id=user_id,
    )


async def get_graph_stats(user_id: str) -> GraphStats:
    """Return lightweight aggregate stats for the dashboard summary cards."""
    driver = get_driver()

    async with driver.session(**get_session_kwargs()) as session:
        result = await session.run(
            """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[ri:INTERESTED_IN]->(e:Entity)
            OPTIONAL MATCH (u)-[re:EXPLORES]->(c:Category)
            RETURN
              count(DISTINCT e) AS total_entities,
              count(DISTINCT c) AS total_categories,
              count(DISTINCT ri) + count(DISTINCT re) AS total_relationships
            """,
            user_id=user_id,
        )
        record = await result.single()
        if record is None:
            return GraphStats(user_id=user_id)

        total_entities = record["total_entities"] or 0
        total_categories = record["total_categories"] or 0
        total_relationships = record["total_relationships"] or 0

        # Top 5 entities by weight
        top_ent_result = await session.run(
            """
            MATCH (u:User {id: $user_id})-[r:INTERESTED_IN]->(e:Entity)
            RETURN e.name AS name, e.type AS type, r.weight AS weight
            ORDER BY r.weight DESC LIMIT 5
            """,
            user_id=user_id,
        )
        top_entities = [
            {"name": r["name"], "type": r["type"], "weight": float(r["weight"] or 0)}
            async for r in top_ent_result
        ]

        # Top 5 categories by weight
        top_cat_result = await session.run(
            """
            MATCH (u:User {id: $user_id})-[r:EXPLORES]->(c:Category)
            RETURN c.name AS name, r.weight AS weight
            ORDER BY r.weight DESC LIMIT 5
            """,
            user_id=user_id,
        )
        top_categories = [
            {"name": r["name"], "weight": float(r["weight"] or 0)}
            async for r in top_cat_result
        ]

    return GraphStats(
        user_id=user_id,
        total_entities=total_entities,
        total_categories=total_categories,
        total_relationships=total_relationships,
        top_entities=top_entities,
        top_categories=top_categories,
    )


# ---------------------------------------------------------------------------
# GDELT article ingestion
# ---------------------------------------------------------------------------


async def ingest_gdelt_articles(entity_name: str, articles: List[GDELTArticle]) -> int:
    """
    Persist GDELT news articles into Neo4j and link them to an existing Entity node.

    For each article a ``GDELTArticle`` node is upserted (keyed by URL) and a
    ``MENTIONED_IN`` edge is created from the matching :Entity node.

    Returns:
        The number of articles successfully written/updated.
    """
    if not articles:
        return 0

    driver = get_driver()
    written = 0

    async with driver.session(**get_session_kwargs()) as session:
        # Verify the Entity node exists before attempting to link articles to it.
        entity_check = await session.run(
            "MATCH (e:Entity {name: $name}) RETURN count(e) AS cnt",
            name=entity_name,
        )
        record = await entity_check.single()
        if not record or record["cnt"] == 0:
            logger.warning(
                "GDELT ingestion skipped: no Entity node found for '%s'", entity_name
            )
            return 0

        for article in articles:
            if not article.url:
                continue
            try:
                await session.run(
                    """
                    MERGE (a:GDELTArticle {url: $url})
                      ON CREATE SET
                        a.title          = $title,
                        a.domain         = $domain,
                        a.seen_date      = $seen_date,
                        a.language       = $language,
                        a.source_country = $source_country,
                        a.social_image   = $social_image,
                        a.created        = datetime()
                      ON MATCH SET
                        a.title          = $title,
                        a.last_refreshed = datetime()

                    WITH a
                    MATCH (e:Entity {name: $entity_name})
                    MERGE (e)-[:MENTIONED_IN]->(a)
                    """,
                    url=article.url,
                    title=article.title,
                    domain=article.domain,
                    seen_date=article.seen_date,
                    language=article.language,
                    source_country=article.source_country,
                    social_image=article.social_image,
                    entity_name=entity_name,
                )
                written += 1
            except Neo4jError as exc:
                logger.warning(
                    "Failed to ingest GDELT article '%s' for entity '%s': %s",
                    article.url,
                    entity_name,
                    exc,
                )

    logger.info(
        "GDELT ingestion for entity '%s': %d/%d articles written",
        entity_name,
        written,
        len(articles),
    )
    return written


# ---------------------------------------------------------------------------
# Pathfinding for recommendations
# ---------------------------------------------------------------------------


async def get_recommendations_from_neo4j(
    user_id: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Use Neo4j graph traversal to surface entities reachable from the user's
    top interests that the user has NOT yet explored.

    Algorithm:
    1. Start from the user's top-5 highest-weight entities.
    2. Walk RELATED_TO edges 2–4 hops outward.
    3. Filter out entities the user already has an INTERESTED_IN edge to.
    4. Rank by closeness (lower hop count = higher relevance).
    5. Return up to `limit` records with path metadata.
    """
    driver = get_driver()
    rows: List[Dict[str, Any]] = []

    async with driver.session(**get_session_kwargs()) as session:
        # Avoid running relationship-specific path queries when the user has
        # no graph footprint yet; this keeps startup UX quiet and fast.
        preflight = await session.run(
            """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[r]->(:Entity)
            RETURN count(r) AS rel_count
            """,
            user_id=user_id,
        )
        preflight_record = await preflight.single()
        if not preflight_record or int(preflight_record["rel_count"] or 0) == 0:
            return rows

        result = await session.run(
            """
            MATCH (u:User {id: $user_id})-[ri:INTERESTED_IN]->(e:Entity)
            WITH u, e ORDER BY ri.weight DESC LIMIT 5

            MATCH path = (e)-[:RELATED_TO*2..4]->(target:Entity)
            WHERE NOT (u)-[:INTERESTED_IN]->(target)
              AND target <> e

            OPTIONAL MATCH (target)-[:BELONGS_TO]->(c:Category)

            WITH target,
                 c,
                 length(path)            AS distance,
                 [n IN nodes(path)
                    WHERE n:Entity AND n <> target | n.name]  AS bridge_entities,
                 count(path)             AS path_count

            RETURN
              target.name   AS entity_name,
              target.type   AS entity_type,
              c.name        AS category,
              distance,
              bridge_entities,
              path_count
            ORDER BY distance ASC, path_count DESC
            LIMIT $limit
            """,
            user_id=user_id,
            limit=limit,
        )
        async for record in result:
            rows.append(dict(record))

    return rows
