"""
Pydantic models for the Mock Snowflake API.

These define the contract between the API and clients.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

# --- ENUMS ---
class LoadMode(str, Enum):
    APPEND = "APPEND"
    OVERWRITE = "OVERWRITE"

class JobStatusEnum(str, Enum):
    QUEUED = "QUEUED"
    RESUMING_WAREHOUSE = "RESUMING_WAREHOUSE"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

# --- NESTED MODELS ---
class ErrorDetails(BaseModel):
    error_code: str
    error_message: str

# --- INPUT MODELS ---
class CopyCommand(BaseModel):
    table_name: str
    load_mode: LoadMode  # Required field (no default)
    rows: List[Dict[str, Any]] = Field(..., min_length=1)

# --- OUTPUT MODELS ---
class JobSubmissionResponse(BaseModel):
    job_id: str
    status: JobStatusEnum
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: JobStatusEnum
    rows_loaded: Optional[int] = None
    error_details: Optional[ErrorDetails] = None
    message: Optional[str] = None

# --- COINGECKO API MODELS ---
class CoinMarketData(BaseModel):
    """
    Pydantic model for CoinGecko Coins Markets API response.
    
    Defines the data contract for cryptocurrency market data with
    data quality rules built into the validation.
    """
    id: str
    symbol: str
    name: str
    current_price: float = Field(..., gt=0)  # DQ Rule: Price must be positive
    market_cap: int = Field(..., gt=0)       # DQ Rule: Market Cap must be positive
    total_volume: int
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    last_updated: datetime                   # DQ Rule: Must be a valid timestamp

    class Config:
        extra = "ignore"  # CoinGecko sends lots of extra fields we don't need
