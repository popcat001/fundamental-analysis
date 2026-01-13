# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-01-12

### Changed
- Extracted configuration constants to `config.py` (removed magic numbers)
- Reduced code duplication in API client (80% reduction via generic method)
- Added database indexes for improved query performance
- Simplified CLAUDE.md documentation (70% reduction)
- Modernized codebase (fixed deprecated imports, PropTypes validation)

## [0.3.0] - 2026-01-12

### Added
- Runtime peer mapping from `config/peers.md` (auto-populated in UI)
- Regression method visualization with formula display
- Number of quarters indicators in valuation steps

### Changed
- Peer mappings now managed via `config/peers.md` (single source of truth)
- Dual-method forward EPS charts (Growth + Regression side-by-side)

### Removed
- Hardcoded peer mappings from JavaScript components

## [0.2.0] - 2026-01-12

### Added
- **P/E multiple-based valuation system** with 5-step methodology
- Dual-method forward EPS estimation (growth + regression)
- Historical P/E analysis with stock price tracking (yfinance)
- Peer comparison analysis
- Interactive valuation charts (Recharts)
- Valuation caching (24h default)
- API endpoints: `POST /GET /api/valuation/{symbol}`

### Changed
- Extended data retention from 4 to 16 quarters (displays 8)

## [0.1.0] - 2025-12

### Added
- FastAPI backend + React frontend
- Alpha Vantage API integration with intelligent caching (30d)
- SQLite database for financial data storage
- 3-layer backend architecture (API, Service, Data)
- DataTable component for 8 quarters of financial metrics

### Changed
- Switched from FMP to Alpha Vantage API

## [0.0.1] - Initial

- Project initialization
