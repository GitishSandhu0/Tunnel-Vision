from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatusEnum(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class UploadResponse(BaseModel):
    job_id: str = Field(..., description="UUID of the created processing job")
    status: JobStatusEnum = Field(default=JobStatusEnum.queued)
    message: str = Field(default="File accepted and queued for processing")
    filename: str


class JobStatus(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    file_type: str
    status: JobStatusEnum
    error_message: Optional[str] = None
    entities_extracted: int = 0
    categories_extracted: int = 0
    created_at: datetime
    updated_at: datetime


class JobStatusResponse(BaseModel):
    job: JobStatus


class ProcessingResult(BaseModel):
    job_id: str
    user_id: str
    entities_extracted: int = 0
    categories_extracted: int = 0
    success: bool = True
    error: Optional[str] = None
    processed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
