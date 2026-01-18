"""Snowflake API Pydantic models."""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LoadMode(str, Enum):
    """Load mode for COPY INTO command."""
    APPEND = "APPEND"
    TRUNCATE = "TRUNCATE"
    UPSERT = "UPSERT"


class JobStatusEnum(str, Enum):
    """Job status enumeration."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ErrorDetails(BaseModel):
    """Error details for failed jobs."""
    error_code: str
    error_message: str
    failed_rows: Optional[int] = None


class CopyCommand(BaseModel):
    """Request schema for COPY INTO command."""
    table_name: str
    load_mode: LoadMode
    rows: List[Dict[str, Any]] = Field(min_length=1)


class JobSubmissionResponse(BaseModel):
    """Response schema for job submission."""
    job_id: str
    status: JobStatusEnum
    message: str


class JobStatus(BaseModel):
    """Response schema for job status monitoring."""
    job_id: str
    status: JobStatusEnum
    message: str
    rows_loaded: Optional[int] = None
    error_details: Optional[ErrorDetails] = None
