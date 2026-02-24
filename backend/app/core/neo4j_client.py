from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

from neo4j import (
    AsyncDriver,
    AsyncGraphDatabase,
    AsyncResult,
    NotificationDisabledClassification,
)
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Module-level singleton so the driver is shared across the process lifetime.
_driver: Optional[AsyncDriver] = None


def get_driver() -> AsyncDriver:
    """
    Return the cached Neo4j AsyncDriver, creating it on first call.

    The driver maintains its own internal connection pool; a single instance
    per process is the recommended pattern.
    """
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
            max_connection_lifetime=3600,       # seconds
            max_connection_pool_size=50,
            connection_acquisition_timeout=30,  # seconds
            notifications_disabled_classifications=(
                NotificationDisabledClassification.UNRECOGNIZED,
            ),
        )
        logger.info("Neo4j AsyncDriver created for URI: %s", settings.NEO4J_URI)
    return _driver


def get_session_kwargs(database: str | None = None) -> Dict[str, str]:
    """
    Build kwargs for driver.session().

    If no database is provided (or configured), the Neo4j user's default/home
    database is used.
    """
    if database is None:
        configured = get_settings().NEO4J_DATABASE.strip()
        database = configured or None

    return {"database": database} if database else {}


async def close_driver() -> None:
    """Close the driver and release all pooled connections. Call at app shutdown."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j AsyncDriver closed")


@asynccontextmanager
async def execute_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    database: str | None = None,
) -> AsyncGenerator[AsyncResult, None]:
    """
    Async context manager that runs a single Cypher query inside an auto-commit
    session and yields the AsyncResult.

    Example:
        async with execute_query("MATCH (n:User {id: $id}) RETURN n", {"id": uid}) as result:
            records = await result.fetch(100)
    """
    driver = get_driver()
    async with driver.session(**get_session_kwargs(database)) as session:
        try:
            result = await session.run(query, params or {})
            yield result
        except Neo4jError as exc:
            logger.error("Neo4j query error [%s]: %s", exc.code, exc.message)
            raise
        except Exception as exc:
            logger.error("Unexpected error during Neo4j query execution: %s", exc)
            raise


async def health_check() -> bool:
    """
    Perform a lightweight connectivity check against Neo4j.

    Returns True if the database is reachable, False otherwise.
    """
    try:
        driver = get_driver()
        await driver.verify_connectivity()
        return True
    except (ServiceUnavailable, Exception) as exc:
        logger.warning("Neo4j health check failed: %s", exc)
        return False
