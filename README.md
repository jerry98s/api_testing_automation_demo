# API Testing Automation Framework

A lightweight, DRY-principled API testing framework for validating both internal (FastAPI) and external REST APIs.

## Overview

This project includes:
1. **Mock Snowflake API** - A FastAPI app simulating async data loading with DQ validation
2. **Test Framework** - Simplified pytest-based testing for API schema and data quality validation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the mock API
uvicorn app.main:app --reload

# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_snowflake.py -v    # Internal API tests
pytest tests/test_coingecko.py -v    # External API tests
pytest tests/test_randomuser.py -v   # RandomUser API tests
```

## Project Structure

```
api_testing_automation_demo/
├── app/                        # Mock Snowflake API
│   ├── main.py                 # FastAPI endpoints
│   ├── models.py               # API Pydantic schemas
│   └── service.py              # State machine & DQ logic
│
├── tests/                      # Test Framework
│   ├── __init__.py
│   ├── conftest.py             # All fixtures (single source of truth)
│   ├── clients.py              # Simple API clients
│   ├── schemas/                # Pydantic models for validation
│   │   ├── __init__.py
│   │   ├── coingecko.py        # CoinGecko response schemas
│   │   ├── snowflake.py        # Snowflake response schemas
│   │   └── randomuser.py       # RandomUser response schemas
│   ├── test_coingecko.py       # External API tests (DQ checks)
│   ├── test_randomuser.py      # RandomUser API tests (DQ checks)
│   └── test_snowflake.py       # Internal API tests (schema validation)
│
├── requirements.txt
├── pytest.ini
└── README.md
```

## Test Framework Design

### Principles

| Principle | Implementation |
|-----------|----------------|
| **DRY** | Single `conftest.py` with all fixtures |
| **Simplicity** | No factories, registries, or plugin systems |
| **Flat Structure** | Tests at root level, not nested in folders |
| **Self-Documenting** | Tests define their own data, no YAML configs |

### API Clients

Two simple client types in `tests/clients.py`:

```python
# External APIs (CoinGecko, etc.)
client = ExternalAPIClient(base_url="https://api.coingecko.com/api/v3")
response = client.get("/coins/markets", params={"vs_currency": "usd"})

# Internal APIs (FastAPI TestClient)
from app.main import app
client = create_internal_client(app)
response = client.post("/snowflake/copy-into", json={...})
```

### Adding a New API

**3 steps only:**

1. **Create schema** (`tests/schemas/newapi.py`):
```python
from pydantic import BaseModel

class MyResponse(BaseModel):
    id: str
    status: str
```

2. **Add fixture** (`tests/conftest.py`):
```python
@pytest.fixture(scope="module")
def newapi_client():
    return ExternalAPIClient(base_url="https://api.example.com")
```

3. **Write tests** (`tests/test_newapi.py`):
```python
from tests.schemas.newapi import MyResponse

def test_response_schema(newapi_client):
    response = newapi_client.get("/endpoint")
    validated = MyResponse(**response.json())
    assert validated.id is not None
```

---

## Mock Snowflake API

### Async Job Pattern

The API simulates realistic Snowflake behavior:

1. **Client** submits data batch
2. **API** returns HTTP 202 with `job_id`
3. **Background** processes through state machine
4. **Client** polls until `SUCCESS` or `FAILED`

### State Machine

| Time Elapsed | Status | Description |
|--------------|--------|-------------|
| 0-2s | `QUEUED` | Waiting for resources |
| 2-5s | `RESUMING_WAREHOUSE` | Cold start simulation |
| 5-8s | `EXECUTING` | Processing data |
| 8s+ | `SUCCESS` / `FAILED` | Final state |

### Data Quality Rules

| Rule | Check | Error Code |
|------|-------|------------|
| A | Every row has `id` field | `NOT_NULL_VIOLATION` |
| B | All rows have same schema | `SCHEMA_MISMATCH` |
| C | All checks pass | Returns `rows_loaded` |

### Endpoints

#### POST `/snowflake/copy-into`

Submit data for loading.

```json
{
  "table_name": "RAW_TRANSACTIONS",
  "load_mode": "APPEND",
  "rows": [
    {"id": 1, "amount": 100.50},
    {"id": 2, "amount": 200.75}
  ]
}
```

**Response (202):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "QUEUED",
  "message": "Load job submitted successfully."
}
```

#### GET `/snowflake/monitor/{job_id}`

Check job status.

**Success Response:**
```json
{
  "job_id": "...",
  "status": "SUCCESS",
  "rows_loaded": 2,
  "message": "Load completed successfully."
}
```

**Failure Response:**
```json
{
  "job_id": "...",
  "status": "FAILED",
  "error_details": {
    "error_code": "NOT_NULL_VIOLATION",
    "error_message": "Row at index 1 is missing required field 'id'"
  }
}
```

---

## Test Categories

### Schema Validation (`test_snowflake.py`)

- Response matches Pydantic model
- Required fields present
- Correct data types
- Enum values valid

### Data Quality (`test_coingecko.py`)

- **Freshness**: Data updated within 15 minutes
- **Business Logic**: BTC price > ETH price
- **Range Checks**: `high_24h >= low_24h`
- **Clock Skew**: No future timestamps

---

## Dependencies

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pytest==7.4.3
requests==2.31.0
httpx==0.25.2
```

## License

MIT
