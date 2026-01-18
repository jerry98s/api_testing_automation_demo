"""
Simple API clients for testing.

Two client types:
- ExternalAPIClient: For external APIs (uses requests)
- InternalAPIClient: For FastAPI apps (uses TestClient)
"""
import requests
from typing import Optional, Dict, Any


class ExternalAPIClient:
    """HTTP client for external APIs using requests library."""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
    
    def get(self, path: str, **kwargs) -> requests.Response:
        return requests.get(
            f"{self.base_url}{path}",
            headers={**self.headers, **kwargs.pop('headers', {})},
            **kwargs
        )
    
    def post(self, path: str, **kwargs) -> requests.Response:
        return requests.post(
            f"{self.base_url}{path}",
            headers={**self.headers, **kwargs.pop('headers', {})},
            **kwargs
        )
    
    def put(self, path: str, **kwargs) -> requests.Response:
        return requests.put(
            f"{self.base_url}{path}",
            headers={**self.headers, **kwargs.pop('headers', {})},
            **kwargs
        )
    
    def delete(self, path: str, **kwargs) -> requests.Response:
        return requests.delete(
            f"{self.base_url}{path}",
            headers={**self.headers, **kwargs.pop('headers', {})},
            **kwargs
        )


def create_internal_client(app: Any):
    """
    Create a TestClient for FastAPI app.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        FastAPI TestClient
    """
    from fastapi.testclient import TestClient
    return TestClient(app)
