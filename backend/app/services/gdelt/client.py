from __future__ import annotations

import logging
from typing import Any, Dict, List
from urllib.parse import quote

import httpx

from app.models.gdelt import GDELTArticle

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GDELT Doc API v2 constants
# ---------------------------------------------------------------------------
_GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
_DEFAULT_MAX_RECORDS = 10
_REQUEST_TIMEOUT = 15.0  # seconds


class GDELTClient:
    """
    Lightweight async client for the GDELT Doc API v2.

    The GDELT Doc API is publicly accessible with no authentication required.
    Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

    Usage::

        async with GDELTClient() as client:
            articles = await client.search_articles("Python programming", max_records=10)
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> GDELTClient:
        self._client = httpx.AsyncClient(timeout=_REQUEST_TIMEOUT)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def search_articles(
        self,
        query: str,
        max_records: int = _DEFAULT_MAX_RECORDS,
    ) -> List[GDELTArticle]:
        """
        Search the GDELT Doc API for recent news articles matching *query*.

        Args:
            query:       Free-text search term (entity name, topic, etc.)
            max_records: Maximum articles to return (capped at 250 by GDELT).

        Returns:
            List of :class:`~app.models.gdelt.GDELTArticle` objects, newest first.
        """
        if self._client is None:
            raise RuntimeError("GDELTClient must be used as an async context manager.")

        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": str(min(max_records, 250)),
            "sort": "DateDesc",
        }

        try:
            response = await self._client.get(_GDELT_DOC_URL, params=params)
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("GDELT API HTTP error for query '%s': %s", query, exc)
            return []
        except httpx.RequestError as exc:
            logger.warning("GDELT API request error for query '%s': %s", query, exc)
            return []
        except Exception as exc:  # noqa: BLE001
            logger.warning("GDELT API unexpected error for query '%s': %s", query, exc)
            return []

        raw_articles: List[Dict[str, Any]] = data.get("articles") or []
        return [self._parse_article(a) for a in raw_articles if a.get("url")]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_article(raw: Dict[str, Any]) -> GDELTArticle:
        """Map a raw GDELT article dict to a :class:`GDELTArticle`."""
        return GDELTArticle(
            url=raw.get("url", ""),
            title=raw.get("title") or raw.get("url", ""),
            domain=raw.get("domain", ""),
            seen_date=raw.get("seendate", ""),
            language=raw.get("language", "English"),
            source_country=raw.get("sourcecountry", ""),
            social_image=raw.get("socialimage") or None,
        )
