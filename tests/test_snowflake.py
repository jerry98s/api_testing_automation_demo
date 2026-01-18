"""
Schema Validation Tests for Snowflake API.

Validates API responses against Pydantic models for the Snowflake
COPY-INTO data loading endpoints.
"""
import pytest
import time
from pydantic import ValidationError

from tests.schemas.snowflake import (
    JobSubmissionResponse,
    JobStatus,
    JobStatusEnum,
    ErrorDetails,
    CopyCommand,
    LoadMode,
)


class TestJobSubmission:
    """Test job submission endpoint."""
    
    def test_submit_job_schema(self, snowflake_client):
        """Validate job submission response matches schema."""
        request_data = {
            "table_name": "RAW_TRANSACTIONS",
            "load_mode": "APPEND",
            "rows": [{"id": 1, "name": "Test", "amount": 100.50}]
        }
        
        response = snowflake_client.post("/snowflake/copy-into", json=request_data)
        assert response.status_code == 202
        
        result = JobSubmissionResponse(**response.json())
        assert result.job_id is not None
        assert len(result.job_id) > 0
        assert result.status == JobStatusEnum.QUEUED
        assert "submitted" in result.message.lower()
    
    def test_invalid_schema_detection(self):
        """Pydantic should catch invalid response data."""
        invalid_data = {
            "job_id": 12345,  # Should be string
            "status": "INVALID_STATUS",
            "message": None
        }
        
        with pytest.raises(ValidationError) as exc:
            JobSubmissionResponse(**invalid_data)
        
        error_fields = [e["loc"][0] for e in exc.value.errors()]
        assert "job_id" in error_fields or "status" in error_fields


class TestJobStatus:
    """Test job status monitoring endpoint."""
    
    def test_status_queued(self, snowflake_client):
        """Validate QUEUED status response."""
        request_data = {
            "table_name": "RAW_TRANSACTIONS",
            "load_mode": "APPEND",
            "rows": [{"id": 1, "name": "Test"}]
        }
        submit_resp = snowflake_client.post("/snowflake/copy-into", json=request_data)
        job_id = submit_resp.json()["job_id"]
        
        response = snowflake_client.get(f"/snowflake/monitor/{job_id}")
        assert response.status_code == 200
        
        status = JobStatus(**response.json())
        assert status.job_id == job_id
        assert status.status == JobStatusEnum.QUEUED
        assert status.rows_loaded is None
        assert status.error_details is None
    
    def test_status_success(self, snowflake_client):
        """Validate SUCCESS status after job completion."""
        request_data = {
            "table_name": "RAW_TRANSACTIONS",
            "load_mode": "APPEND",
            "rows": [
                {"id": 1, "name": "Item 1", "amount": 100.0},
                {"id": 2, "name": "Item 2", "amount": 200.0}
            ]
        }
        submit_resp = snowflake_client.post("/snowflake/copy-into", json=request_data)
        job_id = submit_resp.json()["job_id"]
        
        time.sleep(9)  # Wait for job completion
        
        response = snowflake_client.get(f"/snowflake/monitor/{job_id}")
        assert response.status_code == 200
        
        status = JobStatus(**response.json())
        assert status.job_id == job_id
        assert status.status == JobStatusEnum.SUCCESS
        assert status.rows_loaded == 2
        assert status.error_details is None
        assert "success" in status.message.lower()
    
    def test_status_failed(self, snowflake_client):
        """Validate FAILED status with error details."""
        request_data = {
            "table_name": "RAW_TRANSACTIONS",
            "load_mode": "APPEND",
            "rows": [{"name": "Item without ID"}]  # Missing 'id' - will fail
        }
        submit_resp = snowflake_client.post("/snowflake/copy-into", json=request_data)
        job_id = submit_resp.json()["job_id"]
        
        time.sleep(9)
        
        response = snowflake_client.get(f"/snowflake/monitor/{job_id}")
        assert response.status_code == 200
        
        status = JobStatus(**response.json())
        assert status.job_id == job_id
        assert status.status == JobStatusEnum.FAILED
        assert status.rows_loaded is None
        assert status.error_details is not None
        assert isinstance(status.error_details, ErrorDetails)
        assert "NOT_NULL_VIOLATION" in status.error_details.error_code


class TestRequestSchema:
    """Test request schema validation."""
    
    def test_valid_copy_command(self):
        """Valid CopyCommand should pass."""
        cmd = CopyCommand(
            table_name="RAW_TRANSACTIONS",
            load_mode=LoadMode.APPEND,
            rows=[{"id": 1, "name": "Test"}]
        )
        assert cmd.table_name == "RAW_TRANSACTIONS"
        assert cmd.load_mode == LoadMode.APPEND
        assert len(cmd.rows) == 1
    
    def test_missing_required_fields(self):
        """Pydantic should catch missing fields."""
        with pytest.raises(ValidationError) as exc:
            CopyCommand(table_name="RAW_TRANSACTIONS")
        
        error_fields = [e["loc"][0] for e in exc.value.errors()]
        assert "load_mode" in error_fields
        assert "rows" in error_fields
    
    def test_empty_rows_rejected(self):
        """Empty rows list should be rejected."""
        with pytest.raises(ValidationError) as exc:
            CopyCommand(
                table_name="RAW_TRANSACTIONS",
                load_mode=LoadMode.APPEND,
                rows=[]
            )
        
        assert any("rows" in str(e) for e in exc.value.errors())


class TestEndpoints:
    """Test basic endpoint structure."""
    
    def test_root_endpoint(self, snowflake_client):
        """Root endpoint should return API info."""
        response = snowflake_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert isinstance(data["endpoints"], dict)
    
    def test_health_check(self, snowflake_client):
        """Health check should return healthy status."""
        response = snowflake_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
