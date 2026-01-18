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

## API Response Structures

This section documents the raw JSON response structures received from each API endpoint.

### CoinGecko API

**Endpoint:** `GET /coins/markets`

**Response Type:** `List[dict]` (array of coin objects)

**Example Response:**
```json
[
  {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": 45000.50,
    "market_cap": 850000000000,
    "market_cap_rank": 1,
    "total_volume": 25000000000,
    "high_24h": 46000.00,
    "low_24h": 44000.00,
    "price_change_24h": 500.50,
    "price_change_percentage_24h": 1.12,
    "circulating_supply": 19500000.0,
    "total_supply": 21000000.0,
    "max_supply": 21000000.0,
    "last_updated": "2024-01-15T12:30:45.000Z"
  },
  {
    "id": "ethereum",
    "symbol": "eth",
    "name": "Ethereum",
    "current_price": 2800.75,
    "market_cap": 350000000000,
    "market_cap_rank": 2,
    "total_volume": 15000000000,
    "high_24h": 2900.00,
    "low_24h": 2700.00,
    "price_change_24h": 50.25,
    "price_change_percentage_24h": 1.83,
    "circulating_supply": 120000000.0,
    "total_supply": 120000000.0,
    "max_supply": null,
    "last_updated": "2024-01-15T12:30:45.000Z"
  }
]
```

**Key Fields:**
- `id`: Unique identifier (string)
- `symbol`: Ticker symbol (string, lowercase)
- `current_price`: Current USD price (float, > 0)
- `last_updated`: ISO 8601 timestamp (datetime)
- `high_24h` / `low_24h`: 24-hour price range (float, optional)
- `market_cap`: Market capitalization (int, optional)

**Note:** Response is an array, not wrapped in an object. Each item represents one cryptocurrency.

---

### RandomUser API

**Endpoint:** `GET /?results=50`

**Response Type:** `dict` with `results` array and `info` object

**Example Response:**
```json
{
  "results": [
    {
      "gender": "female",
      "name": {
        "title": "Mrs",
        "first": "Esther",
        "last": "Longoria"
      },
      "location": {
        "street": {
          "number": 9812,
          "name": "Circuito Malasia"
        },
        "city": "El Chote",
        "state": "Jalisco",
        "country": "Mexico",
        "postcode": 13967,
        "coordinates": {
          "latitude": "27.5977",
          "longitude": "148.4798"
        },
        "timezone": {
          "offset": "-1:00",
          "description": "Azores, Cape Verde Islands"
        }
      },
      "email": "esther.longoria@example.com",
      "login": {
        "uuid": "6766f547-0a24-4755-be2f-026767582bb1",
        "username": "yellowbear262",
        "password": "bubba123",
        "salt": "NksEtwn3",
        "md5": "73b6878d517f83379d6dfd38fc0f7d1d",
        "sha1": "c1b2b0c37174867d53007858de4d007b7edaf96d",
        "sha256": "aeec5f11a68b34601356903007def180ed3134e146a0dc1eb4f16ea88e628611"
      },
      "dob": {
        "date": "1967-02-19T12:26:54.026Z",
        "age": 58
      },
      "registered": {
        "date": "2011-09-20T18:25:43.751Z",
        "age": 14
      },
      "phone": "(643) 517 7129",
      "cell": "(694) 914 9112",
      "id": {
        "name": "NSS",
        "value": "27 07 63 2528 6"
      },
      "picture": {
        "large": "https://randomuser.me/api/portraits/women/40.jpg",
        "medium": "https://randomuser.me/api/portraits/med/women/40.jpg",
        "thumbnail": "https://randomuser.me/api/portraits/thumb/women/40.jpg"
      },
      "nat": "MX"
    }
  ],
  "info": {
    "seed": "cbdd6fae1fbb7764",
    "results": 50,
    "page": 1,
    "version": "1.4"
  }
}
```

**Key Fields:**
- `results`: Array of user objects (List[User])
- `info`: Metadata about the request
  - `seed`: Random seed used for generation
  - `results`: Number of users returned
  - `page`: Page number
  - `version`: API version

**User Object Fields:**
- `gender`: "male" or "female" (string)
- `name`: Nested object with `title`, `first`, `last` (string)
- `location`: Nested object with address, coordinates, timezone
- `postcode`: Can be `string` or `int` depending on country
- `email`: Email address (string)
- `dob` / `registered`: Date objects with `date` (ISO 8601) and `age` (int)
- `nat`: 2-letter nationality code (string)

**Note:** `postcode` field type varies by country (string for some, int for others).

---

### Snowflake API (Internal)

#### POST `/snowflake/copy-into`

**Response Type:** `dict` with job submission details

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "QUEUED",
  "message": "Load job submitted successfully."
}
```

**Key Fields:**
- `job_id`: Unique job identifier (UUID string)
- `status`: Job status enum (`QUEUED`, `RUNNING`, `SUCCESS`, `FAILED`)
- `message`: Human-readable status message (string)

---

#### GET `/snowflake/monitor/{job_id}`

**Response Type:** `dict` with job status and results

**Success Response (200):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "message": "Load completed successfully.",
  "rows_loaded": 2,
  "error_details": null
}
```

**Failure Response (200):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "FAILED",
  "message": "Load job failed validation.",
  "rows_loaded": null,
  "error_details": {
    "error_code": "NOT_NULL_VIOLATION",
    "error_message": "Row at index 1 is missing required field 'id'",
    "failed_rows": 1
  }
}
```

**Queued/Running Response (200):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "QUEUED",
  "message": "Job is queued for processing.",
  "rows_loaded": null,
  "error_details": null
}
```

**Key Fields:**
- `job_id`: Same UUID from submission (string)
- `status`: Current job status (enum)
- `message`: Status description (string)
- `rows_loaded`: Number of rows successfully loaded (int, null if not completed)
- `error_details`: Error object if failed, null otherwise
  - `error_code`: Error type identifier (string)
  - `error_message`: Human-readable error description (string)
  - `failed_rows`: Number of rows that failed (int, optional)

**Status Flow:**
1. `QUEUED` → Job submitted, waiting
2. `RUNNING` → Job processing
3. `SUCCESS` → Job completed, `rows_loaded` populated
4. `FAILED` → Job failed, `error_details` populated

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
