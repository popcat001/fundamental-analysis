# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Number of quarters indicator in Forward EPS Calculation section (Part 1)
- Number of quarters indicator in Fundamentals-Based P/E section (Part 4)
- Regression method chart visualization in detailed data visualization
- Regression formula display showing fitted equation (EPS = slope × Quarter + intercept)
- Intercept value to regression method output in backend
- Automatic peer mapping from `config/peers.md` - fetched and parsed at runtime
- Symlink from `frontend/public/peers.md` to `config/peers.md` for single source of truth

### Changed
- Moved peer mappings configuration from hardcoded JavaScript to `config/peers.md`
- Updated Forward EPS chart section to show both Growth and Regression methods side-by-side
- Improved chart titles and legends for better clarity
- Updated CLAUDE.md with runtime requirements (uv for Python, bun for JavaScript)
- Updated CLAUDE.md with peer mapping management instructions

### Removed
- Hardcoded DEFAULT_PEERS object from ValuationAnalysis.js component
- Generation script approach for peer mappings (replaced with runtime parsing)

## [0.2.0] - 2026-01-12

### Added
- Comprehensive P/E multiple-based stock valuation module
- Dual-method forward EPS estimation (growth rate + linear regression)
- Historical P/E ratio analysis with stock price tracking
- Peer comparison analysis functionality
- Fundamentals-based P/E calculation with adjustments
- Justified P/E synthesis using weighted averages
- Fair value price calculation with upside/downside assessment
- Valuation result caching system (24-hour default)
- Interactive charts for valuation visualization using Recharts
- ValuationAnalysis UI component with step-by-step methodology display
- ValuationCharts component with expandable detailed visualizations
- Historical stock price fetching and caching via yfinance
- API endpoints: POST `/api/valuation/{symbol}` and GET `/api/valuation/{symbol}`

### Changed
- Extended financial data retention from 4 to 16 quarters
- Enhanced DataTable component to display 8 quarters of financial data

### Fixed
- Various bug fixes and improvements

## [0.1.0] - 2025-12-XX

### Added
- Initial project setup with FastAPI backend and React frontend
- Alpha Vantage API integration for financial data retrieval
- SQLite database for caching financial data
- Three-layer backend architecture (API, Service, Data layers)
- Financial data viewing for publicly traded companies
- Quarterly earnings, income statement, cash flow, and balance sheet data
- Intelligent caching system (30-day default expiry)
- API rate limiting to comply with Alpha Vantage restrictions
- Frontend proxy configuration for API communication
- DataTable component for displaying financial metrics
- Environment configuration via `.env` file

### Changed
- Switched from FMP (Financial Modeling Prep) to Alpha Vantage API

### Fixed
- Removed `.env` file from version control
- Removed `node_modules` from tracking

## [0.0.1] - Initial Commit

### Added
- Project initialization
- Basic repository structure

---

## Maintenance Instructions

When making changes to the project:

1. **During Development**: Add items to the `[Unreleased]` section under appropriate categories:
   - **Added** for new features
   - **Changed** for changes in existing functionality
   - **Deprecated** for soon-to-be removed features
   - **Removed** for now removed features
   - **Fixed** for any bug fixes
   - **Security** for vulnerability fixes

2. **When Releasing**:
   - Move items from `[Unreleased]` to a new version section
   - Add the version number and date
   - Create a new empty `[Unreleased]` section
   - Update version numbers in `package.json` and other relevant files

3. **Version Numbering**: Follow [Semantic Versioning](https://semver.org/):
   - MAJOR version for incompatible API changes
   - MINOR version for new functionality in a backwards compatible manner
   - PATCH version for backwards compatible bug fixes

4. **Categories**:
   - Use consistent category headers (Added, Changed, Fixed, etc.)
   - List changes in bullet points
   - Be specific and concise
   - Link to issues/PRs when applicable

5. **Keep Updated**: Update this file with every significant change or feature addition
