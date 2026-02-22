from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import tempfile
import uuid
from typing import Any, Dict

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from app.core.config import Settings, get_settings
from app.core.security import get_current_user
from app.models.upload import JobStatusEnum, JobStatusResponse, UploadResponse
from app.services.ai.extractor import AIExtractor
from app.services.ai.queue import processing_queue
from app.services.ingestion.parser import parse_upload
from app.services.ingestion.pii_scrubber import scrub_batch
from app.services.graph.neo4j_ingestion import ingest_user_entities

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",
    "application/json",
    "text/json",
}
ALLOWED_EXTENSIONS = {".zip", ".json"}


def _get_supabase_client(settings: Settings):
    """Lazily import and create a Supabase client to avoid import-time errors."""
    from supabase import create_client  # type: ignore[import-untyped]

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


async def _update_job_status(
    settings: Settings,
    job_id: str,
    status: str,
    *,
    error_message: str | None = None,
    entities_extracted: int | None = None,
    categories_extracted: int | None = None,
) -> None:
    """Persist job status to Supabase upload_jobs table."""
    payload: Dict[str, Any] = {"status": status, "updated_at": "now()"}
    if error_message is not None:
        payload["error_message"] = error_message
    if entities_extracted is not None:
        payload["entities_extracted"] = entities_extracted
    if categories_extracted is not None:
        payload["categories_extracted"] = categories_extracted
    try:
        client = _get_supabase_client(settings)
        client.table("upload_jobs").update(payload).eq("id", job_id).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to update job %s status to %s: %s", job_id, status, exc)


async def _process_upload(
    job_id: str,
    user_id: str,
    file_path: str,
    file_extension: str,
    settings: Settings,
) -> None:
    """
    Background coroutine that handles the full ETL pipeline:
      1. Mark job as 'processing'
      2. Parse the uploaded file into raw text items
      3. Scrub PII from all text items
      4. Extract entities/categories via Gemini (rate-limited through ProcessingQueue)
      5. Ingest results into Neo4j using the Shared Master Node architecture
      6. Cache summary stats back to Supabase
      7. Mark job as 'completed' (or 'failed' on error)
    """
    await _update_job_status(settings, job_id, "processing")
    try:
        # --- Step 1: Parse ---
        parsed = await asyncio.to_thread(parse_upload, file_path, file_extension)
        raw_texts: list[str] = parsed.get("items", [])
        if not raw_texts:
            raise ValueError("No processable text content found in the uploaded file.")

        # --- Step 2: PII scrubbing ---
        clean_texts = await asyncio.to_thread(scrub_batch, raw_texts)

        # --- Step 3: AI extraction (wrapped in queue for rate limiting) ---
        extractor = AIExtractor(settings)
        extraction_result = await processing_queue.enqueue(
            job_id,
            extractor.extract_entities_and_categories(
                clean_texts,
                source_platform=parsed.get("source_platform"),
            ),
        )

        # --- Step 4: Neo4j ingestion ---
        await ingest_user_entities(user_id, extraction_result)

        # --- Step 5: Supabase stats cache ---
        await _update_job_status(
            settings,
            job_id,
            "completed",
            entities_extracted=len(extraction_result.entities),
            categories_extracted=len(extraction_result.categories),
        )
        logger.info(
            "Job %s completed: %d entities, %d categories",
            job_id,
            len(extraction_result.entities),
            len(extraction_result.categories),
        )

    except Exception as exc:  # noqa: BLE001
        logger.error("Job %s failed: %s", job_id, exc, exc_info=True)
        await _update_job_status(settings, job_id, "failed", error_message=str(exc))
    finally:
        # Always clean up the temp file
        try:
            os.unlink(file_path)
        except OSError:
            pass


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a data export file for processing",
)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="ZIP or JSON data export (max 50 MB)"),
    user: Dict[str, Any] = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    """
    Accept a .zip or .json data export, validate it, save it to a temp file,
    create a Supabase job record, and enqueue background processing.
    """
    # --- Validate extension ---
    filename = file.filename or "upload"
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Only .zip and .json are accepted.",
        )

    # --- Stream to temp file while checking size ---
    user_id: str = user["sub"]
    max_bytes = settings.max_upload_size_bytes
    total_bytes = 0
    suffix = ext

    tmp_path: str
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        chunk_size = 64 * 1024  # 64 KB
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                os.unlink(tmp_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
                )
            tmp.write(chunk)

    # --- Create Supabase job record ---
    job_id = str(uuid.uuid4())
    file_type = "zip" if ext == ".zip" else "json"
    try:
        client = _get_supabase_client(settings)
        client.table("upload_jobs").insert(
            {
                "id": job_id,
                "user_id": user_id,
                "filename": filename,
                "file_type": file_type,
                "status": JobStatusEnum.queued.value,
            }
        ).execute()
    except Exception as exc:
        os.unlink(tmp_path)
        logger.error("Failed to create job record in Supabase: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not persist job record. Please try again.",
        ) from exc

    # --- Enqueue background processing ---
    background_tasks.add_task(
        _process_upload,
        job_id,
        user_id,
        tmp_path,
        ext,
        settings,
    )

    return UploadResponse(
        job_id=job_id,
        status=JobStatusEnum.queued,
        filename=filename,
    )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get the status of a processing job",
)
async def get_job_status(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> JobStatusResponse:
    """
    Returns the current status of a processing job.
    Users can only query their own jobs (enforced via RLS + explicit filter).
    """
    # Validate UUID format to prevent injection
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format.")

    user_id: str = user["sub"]
    try:
        client = _get_supabase_client(settings)
        response = (
            client.table("upload_jobs")
            .select("*")
            .eq("id", job_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    except Exception as exc:
        logger.error("Failed to fetch job %s: %s", job_id, exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        ) from exc

    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    return JobStatusResponse(job=response.data)
