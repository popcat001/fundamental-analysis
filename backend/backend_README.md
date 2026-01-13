# Backend API

FastAPI backend for stock fundamental data and P/E-based valuation analysis.

**Alpha Vantage API + SQLite caching + yfinance prices**

## Features

- Financial data retrieval (16 quarters, displays 8)
- P/E multiple-based stock valuation
- Intelligent caching (permanent storage, smart refresh)
- Rate limiting (1.5s between API calls)
- Stock price tracking (yfinance)

## Quick Start

```bash
# Create .env file
cp .env.example .env
# Add ALPHA_VANTAGE_API_KEY=your_key_here

# Start server
uv run app.py
# Runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Cache Behavior

### Permanent Storage with Smart Refresh

1. **Data stored permanently** - Records never auto-deleted
2. **30-day freshness check** - Determines when to refresh
   - **Fresh (<30d)**: Returns cached data (no API call)
   - **Stale (>30d)**: Fetches from API and updates cache
3. **Update, not replace** - Existing records updated, new ones added
4. **Fallback** - Returns stale cache if API fails

**Benefits:**
- Fast responses (cached data)
- Current data (30-day refresh)
- Reliability (fallback to stale cache)
- Historical preservation

## API Rate Limits

Alpha Vantage free tier:
- **Daily limit**: 25 API calls
- **Rate limiting**: 1.5 seconds between calls (enforced)
- **Per ticker**: ~6 seconds (4 API calls)

## Environment Variables

```bash
# Required
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Optional
DATABASE_URL=postgresql://user:pass@localhost/db  # Default: SQLite
CACHE_EXPIRY_DAYS=30
VALUATION_CACHE_HOURS=24
FRONTEND_URL=http://localhost:3000
```

## Installation

```bash
# Dependencies managed by uv (auto-installed)
uv run app.py
```

## API Endpoints

### Financial Data

**Get data**
```
GET /api/ticker/{symbol}
```

**Refresh data**
```
POST /api/ticker/{symbol}/refresh
```

**List cached tickers**
```
GET /api/tickers
```

### Valuation

**Calculate valuation**
```
POST /api/valuation/{symbol}
Body: {"peers": ["MSFT", "GOOGL"]}  # Optional
```

**Get cached valuation**
```
GET /api/valuation/{symbol}?peers=MSFT,GOOGL
```

### System

**Health check**
```
GET /health
```

## Example Response

```json
{
  "company_name": "Apple Inc.",
  "ticker": "AAPL",
  "last_updated": "2026-01-12T10:00:00",
  "data": [
    {
      "quarter": "2024-Q3",
      "fiscal_date": "2024-09-30",
      "reported_date": "2024-10-31",
      "eps": 1.52,
      "revenue": 94000000000,
      "fcf": 25000000000,
      "gross_income": 45000000000,
      "gross_margin": 0.45,
      "net_income": 23000000000,
      "net_margin": 0.23,
      "capex": 2500000000,
      "cash": 50000000000,
      "debt": 120000000000,
      "source": "Alpha Vantage"
    }
  ]
}
```

## Database Schema

**Company**
- ticker (PK), company_name, last_updated

**FinancialData**
- id (PK), ticker (FK, indexed), fiscal_quarter (unique with ticker)
- eps, revenue, free_cash_flow, gross_income, gross_margin, net_income, net_margin
- capex, cash_balance, total_debt
- data_source, fetched_at (indexed)

**StockPrice**
- id (PK), ticker (FK, indexed), date (unique with ticker, indexed)
- open, high, low, close, adjusted_close, volume
- data_source, fetched_at

**ValuationCache**
- id (PK), ticker (FK, indexed), peers (unique with ticker)
- valuation_data (JSON), calculated_at (indexed), expires_at (indexed)

## Architecture

```
app.py                 # FastAPI entry point
├── api/
│   ├── routes.py      # API endpoints
│   └── financial_api.py  # Alpha Vantage client
├── services/
│   ├── data_service.py      # Financial data logic
│   ├── valuation_service.py # Valuation calculations
│   └── price_service.py     # Stock price fetching
├── models.py          # SQLAlchemy models
├── database.py        # DB configuration
└── config.py          # Settings and constants
```

## Testing

```bash
uv run pytest
# Or specific test
uv run pytest test_api.py
```

## Notes

- Default database: `fundamental_analysis.db` (SQLite)
- PostgreSQL: Set `DATABASE_URL` environment variable
- All timestamps use UTC
- Valuation methodology: See `VALUATION_README.md`
