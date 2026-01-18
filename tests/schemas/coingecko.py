"""CoinGecko API Pydantic models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CoinMarketData(BaseModel):
    """Schema for CoinGecko /coins/markets endpoint response."""
    
    id: str
    symbol: str
    name: str
    current_price: float = Field(gt=0)
    market_cap: Optional[int] = None
    market_cap_rank: Optional[int] = None
    total_volume: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None
    last_updated: datetime
    
    class Config:
        extra = "allow"  # Allow extra fields from API
