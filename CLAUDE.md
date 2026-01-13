# CLAUDE.md

Guide for Claude Code when working with this repository.

## Project Overview

Stock fundamental analysis tool with P/E multiple-based valuation. FastAPI backend + React frontend, using Alpha Vantage API with SQLite caching.

**Stack:** Python (uv) + React (bun) + SQLAlchemy + Axios

## Essential Rules

1. **Runtime:** Always use `uv` for Python, `bun` for JavaScript (never `python`/`node`/`npm`)
2. **Changelog:** Update `CHANGELOG.md` ONLY when user requests git commit
   - Use new version number (e.g., `[0.4.0]`), NOT `[Unreleased]`
   - Increment version using semantic versioning
3. **Peer mappings:** Edit `/config/peers.md` only (symlinked to `frontend/public/peers.md`)

## Quick Start

```bash
# Backend (port 8000)
cd backend && uv run app.py

# Frontend (port 3000)
cd frontend && bun install && bun start

# Tests
cd backend && pytest
cd frontend && bun test
```

## Environment

Required `.env` in project root (copy from `backend/.env.example`):
- `ALPHA_VANTAGE_API_KEY` - Required
- `CACHE_EXPIRY_DAYS` - Default: 30
- `VALUATION_CACHE_HOURS` - Default: 24

## Peer Mappings

Edit `/config/peers.md` with format: `TICKER    PEER1, PEER2, PEER3`
- Auto-populated in UI, parsed at runtime
- No build step needed

## Architecture

**Backend:** 3-layer structure
- `api/` - Alpha Vantage client + FastAPI routes
- `services/` - Business logic (data, valuation, prices)
- `models.py` - SQLAlchemy models (Company, FinancialData, StockPrice, ValuationCache)

**Frontend:** React components
- `DataTable.js` - 8 quarters financial data
- `ValuationAnalysis.js` - P/E valuation UI
- `ValuationCharts.js` - Interactive charts

**Data Flow:** Route → Check cache → Fetch from API if stale → Store → Return

## Key Concepts

**Caching:**
- Financial data: Fresh for `CACHE_EXPIRY_DAYS` (30d)
- Valuation: Fresh for `VALUATION_CACHE_HOURS` (24h)
- Prices: Historical never expire, recent expire after 1 day
- Force refresh: `/api/ticker/{symbol}/refresh`

**API Limits:**
- Alpha Vantage: 25 req/day (free tier)
- Rate limiting: 1.5s between calls
- New ticker fetch: ~6 seconds (4 API calls)

**Valuation:**
- 5-step P/E multiple-based methodology
- Dual EPS estimation (growth + regression)
- Peer comparison (optional)
- See `backend/VALUATION_README.md` for details

**Configuration:** All magic numbers in `backend/config.py`
