# Fundamental Analysis Backend

Backend API for retrieving and caching stock fundamental financial data using Alpha Vantage API.

## Features

- Fetch fundamental financial data (income statement, cash flow, balance sheet, EPS)
- SQLite database caching with intelligent refresh logic
- Rate limiting compliance with Alpha Vantage API (1.5s between requests)
- RESTful API endpoints

## Database Cache Behavior

### How the Cache Works

The application uses a **permanent database cache** with intelligent refresh logic:

1. **Data is stored PERMANENTLY** in the database
   - Financial records are never automatically deleted
   - Once stored, they remain in the database indefinitely

2. **The 30-day "expiry" only determines WHEN TO REFRESH**:
   - When you request data, it checks: "Is this data less than 30 days old?"
   - **If YES (fresh)**: Returns cached data from database (no API call)
   - **If NO (stale)**: Fetches fresh data from API and updates the cache

3. **Data is UPDATED, not replaced**:
   - If a record exists for a quarter, it updates that record
   - If a record doesn't exist, it creates a new one
   - The `fetched_at` timestamp is updated to track freshness

4. **Fallback to stale cache**:
   - If the API fails but you have old cached data (even >30 days old)
   - It will return the stale data rather than failing completely

### Summary

- **Database storage**: Permanent (never auto-deleted)
- **Cache freshness check**: 30 days (configurable via `CACHE_EXPIRY_DAYS`)
- **Behavior after 30 days**: Fetches fresh data and updates existing records
- **Old data**: Kept as fallback if API fails

This design provides:
- ✅ Fast responses using cached data (when fresh)
- ✅ Up-to-date data (refreshes every 30 days)
- ✅ Reliability (uses old cache if API is down)
- ✅ Historical preservation (data never deleted)

## API Configuration

### Alpha Vantage Rate Limits

The application respects Alpha Vantage's free tier limits:
- **Rate limit**: 1.5 seconds between requests (enforced in code)
- **Daily limit**: 25 API calls per day
- **Per symbol fetch**: ~6 seconds (4 API calls: earnings, income statement, cash flow, balance sheet)

### Data Fetched

For each stock symbol, the application fetches **16 quarters (4 years)** of:
- Quarterly earnings (EPS)
- Income statements (revenue, gross profit, net income)
- Cash flow statements (operating cash flow, capex)
- Balance sheets (cash, debt)

## Environment Variables

Create a `.env` file in the backend directory:

```
# API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Database URL (optional - for PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost/fundamentals_db

# Cache Settings
CACHE_EXPIRY_DAYS=30

# Frontend URL for CORS
FRONTEND_URL=http://localhost:3000
```

## Installation

```bash
# Install dependencies (if using requirements.txt)
pip install -r requirements.txt

# Or install manually
pip install fastapi uvicorn sqlalchemy python-dotenv requests
```

## Running the Application

```bash
# Start the server
python app.py

# Server runs on http://localhost:8000
```

## API Endpoints

### Get Financial Data
```
GET /api/ticker/{symbol}
```
Returns financial data for the specified stock symbol.

**Response:**
```json
{
  "company_name": "Apple Inc.",
  "ticker": "AAPL",
  "last_updated": "2024-01-06T12:00:00",
  "data": [
    {
      "quarter": "2024-Q3",
      "eps": 1.52,
      "fcf": 25000000000,
      "gross_income": 45000000000,
      "gross_margin": 0.45,
      "net_income": 23000000000,
      "net_margin": 0.23,
      "capex": 2500000000,
      "cash": 50000000000,
      "debt": 120000000000,
      "source": "Alpha Vantage",
      "last_updated": "2024-01-06T12:00:00"
    }
  ]
}
```

### Get Cached Tickers
```
GET /api/tickers
```
Returns list of all tickers currently in the cache.

### Refresh Data
```
POST /api/ticker/{symbol}/refresh
```
Forces a refresh of data from the API, bypassing cache.

### Health Check
```
GET /health
```
Returns API health status.

## Testing

```bash
# Run the test script
python test_api.py
```

## Database Schema

### Company Table
- `id`: Primary key
- `ticker`: Stock symbol (unique)
- `company_name`: Company name
- `last_updated`: Timestamp of last update

### FinancialData Table
- `id`: Primary key
- `ticker`: Foreign key to Company
- `fiscal_quarter`: Quarter (e.g., "2024-Q3")
- `eps`: Earnings per share
- `free_cash_flow`: Free cash flow
- `gross_income`: Gross profit
- `gross_margin`: Gross margin percentage
- `net_income`: Net income
- `net_margin`: Net margin percentage
- `capex`: Capital expenditures
- `cash_balance`: Cash and cash equivalents
- `total_debt`: Total debt (short-term + long-term)
- `data_source`: Data source (e.g., "Alpha Vantage")
- `fetched_at`: Timestamp when data was fetched

## Architecture

```
app.py                  # FastAPI application entry point
├── api/
│   ├── routes.py       # API route definitions
│   └── financial_api.py # Alpha Vantage API client
├── services/
│   └── data_service.py # Business logic and caching
├── models.py           # SQLAlchemy database models
├── database.py         # Database configuration
└── config.py           # Application settings
```

## Notes

- The application uses SQLite by default (file: `fundamentals.db`)
- Can be configured to use PostgreSQL via `DATABASE_URL` environment variable
- All timestamps use UTC
- Rate limiting ensures compliance with Alpha Vantage API terms
