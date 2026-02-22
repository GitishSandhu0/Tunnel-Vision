from __future__ import annotations

import logging
from typing import List

from app.models.graph import Recommendation
from app.services.graph.neo4j_ingestion import get_recommendations_from_neo4j

logger = logging.getLogger(__name__)


async def get_recommendations_for_user(
    user_id: str,
    limit: int = 10,
) -> List[Recommendation]:
    """
    Retrieve pathfinding-based recommendations for a user and convert the raw
    Neo4j rows into typed :class:`~app.models.graph.Recommendation` objects.

    Confidence is estimated from two signals:
    - Path distance  (2 hops → high confidence, 4 hops → lower confidence)
    - Path count     (more independent paths to the same target → higher confidence)

    The reason string is generated from the bridge entities so the frontend
    can show a human-readable explanation (e.g. "Because you follow Python and
    Machine Learning, you might enjoy TensorFlow").
    """
    raw_rows = await get_recommendations_from_neo4j(user_id, limit=limit)

    recommendations: List[Recommendation] = []
    for row in raw_rows:
        entity_name: str = row.get("entity_name", "")
        entity_type: str = row.get("entity_type", "TOPIC")
        distance: int = int(row.get("distance", 4))
        bridge_entities: List[str] = list(row.get("bridge_entities", []))
        category: str | None = row.get("category")
        path_count: int = int(row.get("path_count", 1))

        # Confidence: max 0.95 at distance 2 with many paths, min 0.1 at distance 4 with 1 path
        distance_factor = max(0.0, (4 - distance) / 2.0)  # 1.0 at d=2, 0.0 at d=4
        path_factor = min(1.0, path_count / 5.0)           # saturates at 5 paths
        confidence = round(0.3 + 0.5 * distance_factor + 0.15 * path_factor, 3)
        confidence = min(0.95, max(0.1, confidence))

        # Human-readable reason
        if bridge_entities:
            bridges_str = " and ".join(f'"{b}"' for b in bridge_entities[:3])
            reason = f"Because you're interested in {bridges_str}, you might want to explore {entity_name}."
        else:
            reason = f"{entity_name} is related to your existing interests."

        recommendations.append(
            Recommendation(
                entity_name=entity_name,
                entity_type=entity_type,
                reason=reason,
                distance=distance,
                bridge_entities=bridge_entities,
                confidence=confidence,
                category=category,
            )
        )

    logger.info(
        "Generated %d recommendations for user %s",
        len(recommendations),
        user_id,
    )
    return recommendations
