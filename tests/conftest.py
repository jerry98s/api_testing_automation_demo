"""
Pytest fixtures for API testing.

All fixtures centralized in one place - DRY principle.
"""
import pytest
from tests.clients import ExternalAPIClient, create_internal_client


# =============================================================================
# COINGECKO (External API)
# =============================================================================

@pytest.fixture(scope="session")
def coingecko_client():
    """CoinGecko API client - session scoped to respect rate limits."""
    return ExternalAPIClient(
        base_url="https://api.coingecko.com/api/v3",
        headers={"Accept": "application/json"}
    )


@pytest.fixture(scope="session")
def crypto_data(coingecko_client):
    """
    Fetch BTC & ETH market data once per session.
    
    Session-scoped to minimize API calls and respect rate limits.
    CoinGecko free tier: ~10-30 calls/minute.
    """
    response = coingecko_client.get("/coins/markets", params={
        "vs_currency": "usd",
        "ids": "bitcoin,ethereum",
        "order": "market_cap_desc"
    })
    assert response.status_code == 200, \
        f"CoinGecko API error. Status: {response.status_code}"
    return response.json()


# =============================================================================
# RANDOMUSER (External API)
# =============================================================================

@pytest.fixture(scope="session")
def randomuser_client():
    """RandomUser API client - session scoped to minimize API calls."""
    return ExternalAPIClient(
        base_url="https://randomuser.me/api",
        headers={"Accept": "application/json"}
    )


@pytest.fixture(scope="session")
def randomuser_data(randomuser_client):
    """
    Fetch 50 random users once per session.
    
    Session-scoped to minimize API calls.
    RandomUser API has no rate limits but we still want to be respectful.
    """
    response = randomuser_client.get("/", params={"results": 50})
    assert response.status_code == 200, \
        f"RandomUser API error. Status: {response.status_code}"
    return response.json()


# =============================================================================
# SNOWFLAKE (Internal API)
# =============================================================================

@pytest.fixture(scope="module")
def snowflake_client():
    """
    Snowflake API TestClient.
    
    Requires app.main:app to exist. Comment out if app not implemented.
    """
    from app.main import app
    return create_internal_client(app)
