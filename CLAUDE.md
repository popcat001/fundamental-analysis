# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A web-based fundamental analysis tool for viewing financial data of publicly traded companies with comprehensive P/E multiple-based stock valuation. Built with FastAPI backend and React frontend, using Alpha Vantage API for financial data retrieval with intelligent caching.

**Key Features:**
- Financial data viewing (8 quarters of history)
- Stock valuation analysis with forward EPS estimation
- Peer comparison analysis
- Historical P/E ratio tracking
- Fair value calculation with upside/downside assessment

## Runtime Requirements

**IMPORTANT - Always follow these conventions:**
- **Python files:** Always run using `uv` (e.g., `uv run app.py`, `uv run pytest`)
- **JavaScript files:** Always run using `bun` (e.g., `bun script.js`, `bun run test`)
- Never use `python`, `node`, or `npm` commands directly in this project

## Changelog Maintenance

**IMPORTANT - Update CHANGELOG.md only when committing to GitHub:**
- Do NOT update CHANGELOG.md during regular development or feature implementation
- ONLY update CHANGELOG.md when the user explicitly asks to commit changes to git
- When creating a git commit, first update `CHANGELOG.md`:
  - Add entries to the `[Unreleased]` section under appropriate categories (Added, Changed, Fixed, etc.)
  - Follow the Keep a Changelog format (see CHANGELOG.md for details)
  - Be specific and concise in descriptions
  - Then proceed with the git commit

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

### Managing Peer Mappings

Default peer suggestions for valuation analysis are defined in `peers.md` in the config folder.

**File location:** `/config/peers.md` (symlinked to `frontend/public/peers.md`)

**Format:**
```
TICKER    PEER1, PEER2, PEER3
AMD       NVDA, AVGO, INTC, QCOM
```
- Ticker symbol, followed by 2+ spaces/tabs, then comma-separated peer tickers
- Peers are auto-populated in the UI when analyzing a ticker

**How it works:**
- The app fetches and parses `peers.md` at runtime (no build step required)
- Simply edit `peers.md` and refresh the browser to see changes
- If a ticker is not found in `peers.md`, the peer input field starts empty

## Environment Setup

Backend requires `.env` file in project root directory (copy from `backend/.env.example`):
- `ALPHA_VANTAGE_API_KEY`: Required for API access
- `CACHE_EXPIRY_DAYS`: Financial data cache duration (default: 30 days)
- `VALUATION_CACHE_HOURS`: Valuation results cache duration (default: 24 hours)
- `FRONTEND_URL`: CORS configuration (default: http://localhost:3000)

## Architecture

### Backend Structure

**Three-layer architecture:**
1. **API Layer** (`api/`):
   - `financial_api.py`: External API client for Alpha Vantage with rate limiting
   - `routes.py`: FastAPI endpoints

2. **Service Layer** (`services/`):
   - `data_service.py`: Business logic, caching strategy, data transformation
   - `valuation_service.py`: Stock valuation calculations, P/E analysis, peer comparison
   - `price_service.py`: Historical stock price fetching and caching (yfinance)

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

**StockPrice table:**
- id (PK), ticker (FK), date (unique with ticker)
- OHLCV data: open, high, low, close, volume
- fetched_at, expires_at

**ValuationCache table:**
- id (PK), ticker, peer_list (sorted, comma-separated)
- valuation_data (JSON), calculated_at, expires_at
- Unique constraint on (ticker, peer_list)

### API Rate Limiting

Alpha Vantage has strict rate limits (25 requests/day on free tier). The `FinancialAPIClient` enforces 1.5 second delays between API calls to avoid rate limit warnings. When fetching data for a new ticker, the backend makes 4 sequential API calls (company info, earnings, income statement, cash flow, balance sheet), taking approximately 6 seconds total.

### Caching Strategy

**Financial Data Caching:**
Data is cached in SQLite (dev) or PostgreSQL (prod). Cache is considered fresh if less than `CACHE_EXPIRY_DAYS` old. The `/api/ticker/{symbol}/refresh` endpoint bypasses cache and force-fetches from API.

**Valuation Caching:**
Valuation results cached for `VALUATION_CACHE_HOURS` (default: 24 hours). Cache key includes ticker and sorted peer list. POST endpoint always recalculates, GET endpoint returns cached data if available and fresh.

**Stock Price Caching:**
- Historical prices (>30 days old): Never expire
- Recent prices (<30 days): Expire after 1 day
- Ensures historical P/E ratios remain consistent while keeping recent prices fresh

### Frontend Architecture

React app with Axios for API communication. Proxy configured in package.json routes `/api/*` requests to backend at `http://localhost:8000`.

**Components:**
- `DataTable.js`: Financial data display (8 quarters)
- `ValuationAnalysis.js`: Stock valuation UI with step-by-step methodology display
  - Peer ticker input for comparison
  - Dual-method forward EPS estimation display
  - Historical P/E analysis visualization
  - Fundamentals-based P/E breakdown
  - Fair value assessment with upside/downside
  - Cache status indicator

## Key Implementation Details

**Data transformation:** Alpha Vantage returns separate statements (income, cash flow, balance sheet, earnings). The `data_service.py` combines these by matching fiscal dates and calculates derived metrics (gross margin, net margin, free cash flow).

**Quarter formatting:** Fiscal quarters stored as "YYYY-QN" format (e.g., "2024-Q3") extracted from fiscal date endings.

**Error handling:** API client uses retry logic (3 retries with backoff) for transient failures. DataService falls back to stale cache if API fetch fails.

## Valuation Module

A comprehensive P/E multiple-based valuation system that calculates fair value price ranges. See `backend/VALUATION_README.md` for detailed methodology.

### API Endpoints

- `POST /api/valuation/{symbol}` - Calculate fresh valuation (force recalculation)
  - Request body: `{"peers": ["MSFT", "GOOGL", "META"]}` (optional)
  - Returns full valuation report with all calculation steps

- `GET /api/valuation/{symbol}` - Retrieve cached valuation
  - Query params: `?peers=MSFT,GOOGL,META` (optional)
  - Returns simplified cached data or 404 if not found/expired

### Methodology Overview

**5-Step Valuation Process:**

1. **Forward EPS Estimation** - Dual methods (growth rate + linear regression)
   - Growth method: QoQ compound growth projection
   - Regression method: Linear trend extrapolation
   - Recommended EPS: Average of both methods

2. **Historical P/E Analysis** - Calculate P/E ratios for last 5-8 quarters
   - Uses actual stock prices at earnings report dates (yfinance)
   - Computes TTM EPS for each quarter
   - Statistics: avg, median, min, max, std dev

3. **Peer Comparison** (optional) - Compare P/E multiples with industry peers
   - Fetches financial data for each peer
   - Calculates current P/E for each peer
   - Computes peer group average and median

4. **Fundamentals-Based P/E** - Adjust baseline P/E based on company metrics
   - Base P/E: 15.0
   - Adjustments for: growth rate, margins, debt, margin trends
   - Formula: `15 + growth_adj + margin_adj + risk_adj`

5. **Justified P/E Synthesis** - Weighted average of all P/E estimates
   - Without peers: 57% historical, 43% fundamentals
   - With peers: 40% historical, 30% peer, 30% fundamentals
   - Range: midpoint ± 10% or ± 1 std dev

6. **Fair Value Calculation** - `Forward EPS × Justified P/E`
   - Produces low/high/midpoint estimates
   - Assessment: Undervalued / Fairly Valued / Overvalued

### Data Requirements

- Minimum 8 quarters of financial data required
- EPS data must be available for all quarters
- Stock prices fetched automatically from yfinance for earnings report dates

### Configuration

Key settings in `backend/config.py`:
- `VALUATION_CACHE_HOURS`: Cache duration (default: 24)
- `PE_BASE_MARKET`: Baseline P/E (default: 15.0)
- `PE_GROWTH_MULTIPLIER`: Growth adjustment factor (default: 0.5)
- `MIN_QUARTERS_FOR_VALUATION`: Data requirement (default: 8)

## Testing

Backend has `test_api.py` for testing Alpha Vantage integration. When writing tests, ensure API rate limits are respected (use mocks for unit tests).
