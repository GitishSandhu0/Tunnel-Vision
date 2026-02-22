from __future__ import annotations

import logging
from typing import Any, Dict, List, Set

import httpx

from app.models.gdelt import GDELTArticle

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GDELT Doc API v2 constants
# ---------------------------------------------------------------------------
_GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
_REQUEST_TIMEOUT = 20.0  # seconds – world-today fetches request more articles

# Maximum number of raw articles to request from GDELT before deduplication.
_RAW_FETCH_SIZE = 250

# Keywords used to categorise each article title against existing Neo4j Category
# nodes (seeded by database/neo4j/seed_master_nodes.cypher).  The keys MUST
# exactly match the Category.name values in the graph.
_CATEGORY_KEYWORD_MAP: Dict[str, List[str]] = {
    "History & Society": [
        "war", "conflict", "crisis", "attack", "protest", "rights",
        "migration", "refugee", "humanitarian", "troops", "military",
        "election", "president", "parliament", "minister", "senate",
        "congress", "government", "sanctions", "diplomacy", "treaty",
        "ceasefire", "coup", "insurgency", "assassination", "terrorism",
    ],
    "Business & Economics": [
        "economy", "economic", "market", "stock", "trade", "inflation",
        "gdp", "finance", "banking", "investment", "tariff", "recession",
        "supply chain", "company", "corporation", "merger", "acquisition",
        "oil", "gas", "commodity", "export", "import", "debt", "budget",
        "suez canal", "shipping", "logistics", "port", "freight",
    ],
    "Technology": [
        "artificial intelligence", "ai", "tech", "software", "startup",
        "cybersecurity", "hack", "data breach", "silicon valley",
        "semiconductor", "chip", "robot", "automation", "digital",
        "smartphone", "satellite", "internet",
    ],
    "Health & Wellness": [
        "health", "disease", "pandemic", "epidemic", "outbreak", "vaccine",
        "hospital", "cancer", "virus", "covid", "medicine", "drug",
        "clinical", "surgery", "mental health", "treatment",
    ],
    "Science": [
        "climate", "space", "nasa", "research", "study", "discovery",
        "science", "scientist", "experiment", "carbon", "atmosphere",
        "ocean", "earthquake", "volcano",
    ],
    "Environment & Sustainability": [
        "climate change", "emissions", "carbon", "renewable", "environment",
        "pollution", "deforestation", "biodiversity", "wildfire", "flood",
        "drought", "glacier", "fossil fuel",
    ],
}


def _extract_categories(title: str) -> List[str]:
    """
    Return a deduplicated list of Neo4j Category names that match the article title.

    Matching is case-insensitive substring search.  A single article can match
    multiple categories (e.g. "AI startup funding" → Technology + Business).
    """
    title_lower = title.lower()
    matched: List[str] = []
    seen: Set[str] = set()
    for category_name, keywords in _CATEGORY_KEYWORD_MAP.items():
        if category_name in seen:
            continue
        if any(kw in title_lower for kw in keywords):
            matched.append(category_name)
            seen.add(category_name)
    return matched


async def fetch_world_today_events(max_events: int = 50) -> List[GDELTArticle]:
    """
    Fetch the top *max_events* global news articles from the GDELT Doc API.

    Strategy:
    - Request up to 250 articles from the last 24 hours (``timespan=24h``).
    - Deduplicate by publisher domain so each major news source contributes at
      most one story (ensures topical diversity).
    - Return the first ``max_events`` entries.

    Returns an empty list if the GDELT API is unreachable.
    """
    params = {
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(_RAW_FETCH_SIZE),
        "sort": "DateDesc",
        "timespan": "24h",
    }

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(_GDELT_DOC_URL, params=params)
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("GDELT World Today HTTP error: %s", exc)
        return []
    except httpx.RequestError as exc:
        logger.warning("GDELT World Today request error: %s", exc)
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("GDELT World Today unexpected error: %s", exc)
        return []

    raw_articles: List[Dict[str, Any]] = data.get("articles") or []

    # Deduplicate by domain – one story per news source for diversity.
    seen_domains: Set[str] = set()
    unique: List[GDELTArticle] = []
    for raw in raw_articles:
        if not raw.get("url"):
            continue
        domain = raw.get("domain", "")
        if domain and domain in seen_domains:
            continue
        seen_domains.add(domain)
        unique.append(
            GDELTArticle(
                url=raw.get("url", ""),
                title=raw.get("title") or raw.get("url", ""),
                domain=domain,
                seen_date=raw.get("seendate", ""),
                language=raw.get("language", "English"),
                source_country=raw.get("sourcecountry", ""),
                social_image=raw.get("socialimage") or None,
            )
        )
        if len(unique) >= max_events:
            break

    logger.info("GDELT World Today: fetched %d unique events", len(unique))
    return unique
