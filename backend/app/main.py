from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.neo4j_client import close_driver, get_driver
from app.api.routes import health, ingest, graph, recommendations, gdelt

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application-level resources.

    Startup  – initialise the Neo4j driver (verifies connectivity) and log that
               the service is ready.
    Shutdown – gracefully close the Neo4j connection pool.
    """
    settings = get_settings()
    logger.info(
        "Tunnel Vision API starting up (env=%s, neo4j=%s)",
        settings.APP_ENV,
        settings.NEO4J_URI,
    )

    # Eagerly create and verify the driver so misconfiguration surfaces early.
    driver = get_driver()
    try:
        await driver.verify_connectivity()
        logger.info("Neo4j connectivity verified ✓")
    except Exception as exc:  # noqa: BLE001
        # Non-fatal at startup so the app can still serve /health/ping for cron
        logger.warning("Neo4j connectivity check failed at startup: %s", exc)

    logger.info("Tunnel Vision API ready ✓")
    yield

    # --- shutdown ---
    await close_driver()
    logger.info("Tunnel Vision API shut down cleanly")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Tunnel Vision API",
        description=(
            "Backend for Tunnel Vision – a SaaS app that maps your digital "
            "interests into an interactive knowledge graph."
        ),
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(health.router, tags=["Health"])
    app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
    app.include_router(graph.router, prefix="/graph", tags=["Graph"])
    app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
    app.include_router(gdelt.router, prefix="/gdelt", tags=["GDELT"])

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "status_code": exc.status_code},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred.", "status_code": 500},
        )

    # ------------------------------------------------------------------
    # Root
    # ------------------------------------------------------------------
    @app.get("/", tags=["Root"], summary="App info")
    async def root() -> dict:
        return {
            "app": "Tunnel Vision API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
        }

    return app


app = create_app()
