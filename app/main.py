"""
FastAPI application with Mock Snowflake API endpoints.

This module contains the HTTP endpoints for submitting and monitoring load jobs.
"""
from fastapi import FastAPI, HTTPException
from app.models import CopyCommand, JobSubmissionResponse, JobStatus, JobStatusEnum
from app.service import submit_job, get_job_status

app = FastAPI(title="Mock Snowflake API")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Mock Snowflake API",
        "version": "1.0.0",
        "endpoints": {
            "submit_job": "POST /snowflake/copy-into",
            "monitor_job": "GET /snowflake/monitor/{job_id}"
        }
    }


@app.post("/snowflake/copy-into", status_code=202, response_model=JobSubmissionResponse)
async def trigger_load(command: CopyCommand):
    """
    Submit a load job to the Mock Snowflake API.
    
    The response_model parameter tells FastAPI to validate the response
    against the JobSubmissionResponse schema automatically.
    """
    job_id = submit_job(command)
    return {
        "job_id": job_id, 
        "status": JobStatusEnum.QUEUED, 
        "message": "Job submitted successfully"
    }


@app.get("/snowflake/monitor/{job_id}", response_model=JobStatus)
async def monitor_job(job_id: str):
    """
    Monitor the status of a load job.
    
    The response_model parameter tells FastAPI to validate the response
    against the JobStatus schema automatically.
    """
    status_data = get_job_status(job_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return status_data


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
