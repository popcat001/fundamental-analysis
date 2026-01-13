# Stock Fundamental Analysis Tool

Web-based fundamental analysis and P/E multiple-based valuation tool for publicly traded companies.

**FastAPI backend + React frontend + Alpha Vantage API + SQLite caching**

## Features

### Financial Data
- **8 quarters** of historical financial data
- Key metrics: EPS, Revenue, Free Cash Flow, Margins, Debt
- Intelligent caching (30-day expiry)
- Manual refresh on demand

### Stock Valuation
- **P/E multiple-based valuation** with 5-step methodology
- **Dual-method forward EPS** estimation (growth + regression)
- **Historical P/E analysis** with stock price tracking
- **Peer comparison** analysis (customizable peer groups)
- **Interactive charts** with expandable visualizations
- Fair value calculation with upside/downside assessment

## Prerequisites

- **Python 3.9+** with `uv` package manager
- **Bun** runtime for JavaScript
- **Alpha Vantage API key** (free tier: https://www.alphavantage.co/support/#api-key)

## Quick Setup

### 1. Environment Configuration

```bash
# Copy environment template
cp backend/.env.example .env

# Edit .env and add your API key
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

### 2. Start Backend

```bash
cd backend
uv run app.py
# Runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 3. Start Frontend

```bash
cd frontend
bun install
bun start
# Runs on http://localhost:3000
```

## Usage

1. Open http://localhost:3000
2. Enter ticker symbol (e.g., AAPL, MSFT, GOOGL)
3. Click "Search" to load financial data
4. Click "Calculate Valuation" to run P/E analysis
5. Optionally add peer tickers for comparison (auto-populated from `config/peers.md`)
6. Expand chart sections for detailed visualizations

## Peer Mappings

Default peer suggestions are managed in `config/peers.md`:

```
AAPL    MSFT, GOOGL, META
AMD     NVDA, AVGO, INTC, QCOM
```

Edit this file to customize default peers. Changes take effect immediately (no rebuild needed).

## API Endpoints

### Financial Data
- `GET /api/ticker/{symbol}` - Get cached financial data
- `POST /api/ticker/{symbol}/refresh` - Force refresh from API
- `GET /api/tickers` - List all cached tickers

### Valuation
- `POST /api/valuation/{symbol}` - Calculate valuation (with optional peers)
- `GET /api/valuation/{symbol}` - Retrieve cached valuation

## Architecture

```
backend/
├── api/               # Alpha Vantage client + FastAPI routes
├── services/          # Business logic (data, valuation, prices)
├── models.py          # SQLAlchemy models
├── config.py          # Configuration constants
└── app.py            # Application entry point

frontend/
├── src/components/
│   ├── DataTable.js          # Financial data display
│   ├── ValuationAnalysis.js  # Valuation UI
│   └── ValuationCharts.js    # Interactive charts
└── public/peers.md    # Symlink to config/peers.md

config/
└── peers.md          # Peer mapping configuration
```

## Configuration

Key settings in `.env`:

- `ALPHA_VANTAGE_API_KEY` - Required for API access
- `CACHE_EXPIRY_DAYS` - Financial data cache duration (default: 30)
- `VALUATION_CACHE_HOURS` - Valuation cache duration (default: 24)
- `FRONTEND_URL` - CORS configuration (default: http://localhost:3000)

All calculation constants (P/E base, growth multipliers, etc.) are in `backend/config.py`.

## Database

SQLite for development (`fundamental_analysis.db` auto-created in backend directory).

For production, set `DATABASE_URL` environment variable for PostgreSQL.

## API Rate Limits

Alpha Vantage free tier: **25 requests/day**

- Rate limiting: 1.5s between calls
- New ticker fetch: ~6 seconds (4 API calls)
- Use caching to minimize API usage

## Troubleshooting

**API Key Issues**
- Verify `ALPHA_VANTAGE_API_KEY` in `.env`
- Check daily limit (25 requests for free tier)

**Database Issues**
- Delete `fundamental_analysis.db` and restart backend

**Port Conflicts**
- Backend: port 8000
- Frontend: port 3000
- Kill processes: `lsof -ti:8000 | xargs kill`

**CORS Issues**
- Update `FRONTEND_URL` in `.env` if using different port

## Documentation

- `CLAUDE.md` - Development guide for Claude Code
- `CHANGELOG.md` - Version history
- `backend/VALUATION_README.md` - Detailed valuation methodology

## License

MIT License
