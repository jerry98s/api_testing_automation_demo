"""
Data Quality Tests for CoinGecko API.

Validates cryptocurrency market data across three dimensions:
1. Schema Validation - Does the data match our expected contract?
2. Business Logic - Do the financial numbers make sense?
3. Data Freshness - Is the data recent enough?

Note: CoinGecko free tier has rate limits (~10-30 calls/minute).
"""
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from tests.schemas.coingecko import CoinMarketData


class TestSchemaValidation:
    """Validate API response matches expected schema."""
    
    def test_schema_contract(self, crypto_data):
        """Validate all required fields and types are correct."""
        assert len(crypto_data) >= 2, "Expected at least Bitcoin and Ethereum"
        
        for item in crypto_data:
            try:
                coin = CoinMarketData(**item)
                assert coin.symbol == coin.symbol.lower(), \
                    f"Symbol {coin.symbol} should be lowercase"
            except ValidationError as e:
                pytest.fail(f"Schema validation failed for {item.get('id')}: {e}")


class TestBusinessLogic:
    """Validate financial data makes sense."""
    
    def test_bitcoin_price_greater_than_ethereum(self, crypto_data):
        """BTC should be more expensive than ETH (standard market condition)."""
        btc = next((c for c in crypto_data if c["id"] == "bitcoin"), None)
        eth = next((c for c in crypto_data if c["id"] == "ethereum"), None)
        
        assert btc is not None, "Bitcoin data not found"
        assert eth is not None, "Ethereum data not found"
        assert btc["current_price"] > eth["current_price"], \
            f"Anomaly: ETH ({eth['current_price']}) > BTC ({btc['current_price']})"
    
    def test_24h_high_low_range(self, crypto_data):
        """Validate high_24h >= low_24h for all coins."""
        for item in crypto_data:
            if item.get("high_24h") and item.get("low_24h"):
                assert item["high_24h"] >= item["low_24h"], \
                    f"{item['id']}: high_24h ({item['high_24h']}) < low_24h ({item['low_24h']})"
    
    def test_current_price_within_24h_range(self, crypto_data):
        """Current price should be within 24h range (with 5% buffer)."""
        for item in crypto_data:
            if item.get("high_24h") and item.get("low_24h"):
                buffer = (item["high_24h"] - item["low_24h"]) * 0.05
                assert item["current_price"] <= item["high_24h"] + buffer, \
                    f"{item['id']}: price exceeds high_24h"
                assert item["current_price"] >= item["low_24h"] - buffer, \
                    f"{item['id']}: price below low_24h"


class TestDataFreshness:
    """Validate data timeliness."""
    
    def test_data_not_stale(self, crypto_data):
        """Data must be updated within last 15 minutes."""
        for item in crypto_data:
            coin = CoinMarketData(**item)
            now = datetime.now(timezone.utc)
            
            last_updated = coin.last_updated
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            
            lag = now - last_updated
            assert lag < timedelta(minutes=15), \
                f"Stale data: {coin.id} last updated {lag} ago"
    
    def test_no_clock_skew(self, crypto_data):
        """Data should not be from the future."""
        for item in crypto_data:
            coin = CoinMarketData(**item)
            now = datetime.now(timezone.utc)
            
            last_updated = coin.last_updated
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            
            lag = now - last_updated
            assert lag.total_seconds() >= -60, \
                f"Clock skew: {coin.id} is {abs(lag)} in the future"
