from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"

class JobCreateRequest(BaseModel):
    spec: dict[str, Any]
    is_preview: bool = False
    row_count: int | None = None
    use_ollama: bool = False

class JobStatusResponse(BaseModel):
    id: str
    status: JobStatus
    progress: float = 0.0
    row_count: int
    is_preview: bool
    created_at: str
    updated_at: str
    completed_at: str | None = None
    error_message: str | None = None
    has_artifacts: bool = False

class JobRecord(BaseModel):
    id: str
    spec_json: str
    status: JobStatus
    progress: float = 0.0
    row_count: int
    is_preview: bool = False
    use_ollama: bool = False
    created_at: str
    updated_at: str
    completed_at: str | None = None
    error_message: str | None = None
    artifact_dir: str
