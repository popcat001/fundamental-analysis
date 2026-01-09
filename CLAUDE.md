# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A web-based fundamental analysis tool for viewing financial data of publicly traded companies. Built with FastAPI backend and React frontend, using Alpha Vantage API for financial data retrieval with intelligent caching.

## Development Commands

### Backend (FastAPI)

```bash
# Run the backend server (from project root)
cd backend
uv run app.py
# Server starts at http://localhost:8000
# API docs available at http://localhost:8000/docs

# Run backend tests
cd backend
pytest
# Or run specific test
pytest test_api.py
```

### Frontend (React)

```bash
# Install dependencies
cd frontend
bun install

# Run development server
bun start
# Server starts at http://localhost:3000

# Build for production
bun run build

# Run tests
bun test
```

## Environment Setup

Backend requires `.env` file in project root directory (copy from `backend/.env.example`):
- `ALPHA_VANTAGE_API_KEY`: Required for API access
- `CACHE_EXPIRY_DAYS`: Data cache duration (default: 30 days)
- `FRONTEND_URL`: CORS configuration (default: http://localhost:3000)

## Architecture

### Backend Structure

**Three-layer architecture:**
1. **API Layer** (`api/`):
   - `financial_api.py`: External API client for Alpha Vantage with rate limiting
   - `routes.py`: FastAPI endpoints

2. **Service Layer** (`services/`):
   - `data_service.py`: Business logic, caching strategy, data transformation

3. **Data Layer**:
   - `database.py`: SQLAlchemy session management
   - `models.py`: Database models (Company, FinancialData)

**Data Flow:**
- Route receives request → DataService checks cache → If stale/missing, FinancialAPIClient fetches from Alpha Vantage → DataService stores in cache → Response formatted and returned

### Database Schema

**Company table:**
- ticker (PK), company_name, last_updated

**FinancialData table:**
- id (PK), ticker (FK), fiscal_quarter (unique with ticker)
- Financial metrics: eps, free_cash_flow, gross_income, gross_margin, net_income, net_margin, capex, cash_balance, total_debt
- data_source, fetched_at

### API Rate Limiting

Alpha Vantage has strict rate limits (25 requests/day on free tier). The `FinancialAPIClient` enforces 1.5 second delays between API calls to avoid rate limit warnings. When fetching data for a new ticker, the backend makes 4 sequential API calls (company info, earnings, income statement, cash flow, balance sheet), taking approximately 6 seconds total.

### Caching Strategy

Data is cached in SQLite (dev) or PostgreSQL (prod). Cache is considered fresh if less than `CACHE_EXPIRY_DAYS` old. The `/api/ticker/{symbol}/refresh` endpoint bypasses cache and force-fetches from API.

### Frontend Architecture

React app with Axios for API communication. Proxy configured in package.json routes `/api/*` requests to backend at `http://localhost:8000`.

## Key Implementation Details

**Data transformation:** Alpha Vantage returns separate statements (income, cash flow, balance sheet, earnings). The `data_service.py` combines these by matching fiscal dates and calculates derived metrics (gross margin, net margin, free cash flow).

**Quarter formatting:** Fiscal quarters stored as "YYYY-QN" format (e.g., "2024-Q3") extracted from fiscal date endings.

**Error handling:** API client uses retry logic (3 retries with backoff) for transient failures. DataService falls back to stale cache if API fetch fails.

## Testing

Backend has `test_api.py` for testing Alpha Vantage integration. When writing tests, ensure API rate limits are respected (use mocks for unit tests).
