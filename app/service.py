"""
Service layer containing the state machine logic and data quality rules.

This module separates business logic from API routing for clean architecture.
"""
import time
import uuid
from typing import Dict, Optional
from datetime import datetime

from app.models import CopyCommand, JobStatusEnum, ErrorDetails, JobStatus

_JOB_STORE = {}


def submit_job(command: CopyCommand) -> str:
    """Submit a new load job and return its job_id."""
    job_id = str(uuid.uuid4())
    _JOB_STORE[job_id] = {
        "start_time": time.time(),
        "command": command
    }
    return job_id


def get_job_status(job_id: str) -> Optional[Dict]:
    """
    Get the current status of a job.
    
    Returns a dict that matches the JobStatus Pydantic model.
    FastAPI's response_model will validate and serialize this automatically.
    """
    job = _JOB_STORE.get(job_id)
    if not job:
        return None

    elapsed = time.time() - job["start_time"]
    rows = job["command"].rows
    job_id_str = str(job_id)

    # --- TIME SIMULATION ---
    if elapsed < 2:
        return {
            "job_id": job_id_str,
            "status": JobStatusEnum.QUEUED,
            "rows_loaded": None,
            "error_details": None,
            "message": "Job submitted successfully"
        }
    if elapsed < 5:
        return {
            "job_id": job_id_str,
            "status": JobStatusEnum.RESUMING_WAREHOUSE,
            "rows_loaded": None,
            "error_details": None,
            "message": "Waking up warehouse"
        }
    if elapsed < 8:
        return {
            "job_id": job_id_str,
            "status": JobStatusEnum.EXECUTING,
            "rows_loaded": None,
            "error_details": None,
            "message": "Running query"
        }

    # --- DQ LOGIC (Final State: 8+ seconds) ---
    # Rule 1: Not Null Check (Primary Key)
    if any("id" not in row or row.get("id") is None for row in rows):
        return {
            "job_id": job_id_str,
            "status": JobStatusEnum.FAILED,
            "rows_loaded": None,
            "error_details": ErrorDetails(
                error_code="NOT_NULL_VIOLATION",
                error_message="Column 'id' is missing."
            ).model_dump(),  # Convert Pydantic object to dict for JSON response
            "message": "Data Quality Failure"
        }

    # Rule 2: Schema Validation
    if rows:
        first_row_keys = set(rows[0].keys())
        for idx, row in enumerate(rows[1:], start=1):
            row_keys = set(row.keys())
            if row_keys != first_row_keys:
                missing_keys = first_row_keys - row_keys
                extra_keys = row_keys - first_row_keys
                error_parts = []
                if missing_keys:
                    error_parts.append(f"missing fields: {sorted(missing_keys)}")
                if extra_keys:
                    error_parts.append(f"extra fields: {sorted(extra_keys)}")
                return {
                    "job_id": job_id_str,
                    "status": JobStatusEnum.FAILED,
                    "rows_loaded": None,
                    "error_details": ErrorDetails(
                        error_code="SCHEMA_MISMATCH",
                        error_message=f"Row at index {idx} has schema mismatch: {', '.join(error_parts)}"
                    ).model_dump(),
                    "message": "Data Quality Failure"
                }

    # Rule 3: Success Case (All checks passed)
    return {
        "job_id": job_id_str,
        "status": JobStatusEnum.SUCCESS,
        "rows_loaded": len(rows),
        "error_details": None,
        "message": "Load success"
    }
