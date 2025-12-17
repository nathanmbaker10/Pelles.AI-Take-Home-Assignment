"""Data models for job tracking."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Job(BaseModel):
    """Job model."""
    job_id: str
    status: JobStatus
    description: Optional[str] = None
    error: Optional[str] = None

