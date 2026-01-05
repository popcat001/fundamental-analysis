
# Fundamental Analysis Tool — Requirements

**Version:** 1.0  
**Date:** 2026-01-05

## Table of Contents

1. Executive Summary
2. System Overview
3. Technical Specifications
4. Functional Requirements
5. Non-Functional Requirements
6. Error Handling
7. User Interface Design
8. Development Roadmap
9. Testing Requirements
10. Deployment
11. Maintenance and Updates
12. Future Enhancements
13. Appendix

## 1. Executive Summary

### Purpose

This document outlines the requirements for a fundamental analysis tool designed to assist with stock trading decisions by aggregating, storing, and visualizing key financial metrics for publicly traded companies.

### Target Users

Individual investors, day traders, and financial analysts who need quick access to historical financial data.

### Key Features

- Ticker-based data retrieval
- Local database caching
- Historical trend visualization (8 quarters)
- Automatic data fetching from financial APIs

## 2. System Overview

### 2.1 Architecture

The system consists of three main components:

- Frontend UI: Web-based interface for data input and visualization
- Backend API: Handles data retrieval, processing, and database operations
- Database: Local storage for cached financial data

### 2.2 Data Flow

User enters stock ticker → System checks database → If data missing/incomplete, fetch from API → Store in database → Display results in UI

## 3. Technical Specifications

### 3.1 Technology Stack

**Frontend:** React.js with Chart.js or Recharts for data visualization

**Backend:** Python FastAPI

**Database:** PostgreSQL (for multi-user deployment)

**Financial Data API:** Alpha Vantage (free tier: 25 requests/day) or Financial Modeling Prep (free tier: 250 requests/day)

Other options:
    SEC EDGAR (Official API)
    SimFin

**Key Python Libraries:**

- FastAPI/Flask: Web framework for REST API
- SQLAlchemy: ORM for database operations
- pandas: Data manipulation and analysis
- requests: HTTP library for API calls
- python-dotenv: Environment variable management

### 3.2 Project Structure

```
fundamental-analysis/
├── backend/
│   ├── app.py                 # Main application entry point
│   ├── config.py              # Configuration and environment variables
│   ├── models.py              # SQLAlchemy database models
│   ├── database.py            # Database connection and session management
│   ├── api/
│   │   ├── routes.py          # API endpoint definitions
│   │   └── financial_api.py   # External API integration (FMP/Alpha Vantage)
│   ├── services/
│   │   ├── data_service.py    # Business logic for data retrieval
│   │   └── cache_service.py   # Caching logic
+│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   └── services/          # API client for backend
│   └── package.json
└── README.md
```

### 3.3 Database Schema

#### Table: companies

- `ticker` (VARCHAR, PRIMARY KEY)
- `company_name` (VARCHAR)
- `last_updated` (TIMESTAMP)

#### Table: financial_data

- `id` (INTEGER, PRIMARY KEY, AUTO_INCREMENT)
- `ticker` (VARCHAR, FOREIGN KEY → companies.ticker)
- `fiscal_quarter` (VARCHAR, e.g., '2024-Q3')
- `eps` (DECIMAL)
- `free_cash_flow` (BIGINT)
- `gross_income` (BIGINT)
- `gross_margin` (DECIMAL)
- `net_income` (BIGINT)
- `net_margin` (DECIMAL)
- `capex` (BIGINT)
- `cash_balance` (BIGINT)
- `total_debt` (BIGINT)
- `data_source` (VARCHAR, e.g., 'AlphaVantage')
- `fetched_at` (TIMESTAMP)

- UNIQUE CONSTRAINT on (`ticker`, `fiscal_quarter`)

### 3.4 API Integration

**Primary Choice:** Financial Modeling Prep (FMP) — comprehensive fundamental data with a generous free tier

**Backup Option:** Alpha Vantage — reliable alternative if FMP rate limits are exceeded

Required API endpoints:

- Income statement (quarterly)
- Cash flow statement (quarterly)
- Balance sheet (quarterly)

## 4. Functional Requirements

### 4.1 Core Features

#### FR-1: Ticker Input

- User can enter a stock ticker symbol (e.g., AAPL, MSFT)
- System validates ticker format (uppercase, 1–5 characters)
- System provides autocomplete suggestions based on previously searched tickers

#### FR-2: Data Retrieval

- System first queries local database for requested ticker
- If data is missing or older than 30 days, system fetches from API
- System retrieves data for the most recent 8 fiscal quarters (2 years)
- System stores fetched data in database with timestamp

#### FR-3: Data Display

Display the following metrics for each of the past 8 quarters:

- Earnings Per Share (EPS) — in dollars
- Free Cash Flow (FCF) — in millions
- Gross Income — in millions
- Gross Margin — as percentage
- Net Income — in millions
- Net Margin — as percentage
- Capital Expenditures (CapEx) — in millions
- Cash Balance — in millions
- Total Debt — in millions

#### FR-4: Data Visualization

- Display data in both tabular and chart formats
- Table view: Scrollable table with quarters as columns, metrics as rows
- Chart view: Line charts showing trends over 8 quarters
- Allow users to toggle between table and chart views
- Highlight positive trends in green, negative trends in red

#### FR-5: Data Refresh

- Provide 'Refresh' button to manually update data from API
- Display last updated timestamp for each ticker
- Auto-refresh data if older than 30 days when ticker is searched

### 4.2 Secondary Features

#### FR-6: Multi-Ticker Comparison (Future Enhancement)

- Allow users to compare up to 3 tickers side-by-side
- Display comparative charts with multiple lines

#### FR-7: Export Functionality (Future Enhancement)

- Export data as CSV or Excel file
- Export charts as PNG images

## 5. Non-Functional Requirements

### 5.1 Performance

- Database queries should return cached data within 500ms
- API requests should timeout after 10 seconds
- UI should display loading indicators for operations taking >1 second

### 5.2 Reliability

- Gracefully handle API rate limit errors with user-friendly messages
- Implement retry logic with exponential backoff for failed API requests
- System should continue to display cached data even if API is unavailable

### 5.3 Usability

- Interface should be responsive and work on desktop screens (1024px minimum width)
- Error messages should be clear and actionable
- Charts should be interactive with hover tooltips showing exact values

### 5.4 Security

- API keys should be stored in environment variables, not hardcoded
- Implement input validation to prevent SQL injection
- Use parameterized queries for all database operations

## 6. Error Handling

### 6.1 Invalid Ticker

**Scenario:** User enters ticker that doesn't exist

**Response:** Display message: "Ticker symbol 'XYZ' not found. Please verify the symbol and try again."

### 6.2 API Rate Limit Exceeded

**Scenario:** API returns 429 status code

**Response:** Display cached data if available, with message: "API rate limit reached. Displaying cached data from [timestamp]. Try again in [X] minutes."

### 6.3 Missing Data

**Scenario:** API returns incomplete data (e.g., only 5 quarters instead of 8)

**Response:** Display available data and show 'N/A' for missing quarters. Include note: "Data incomplete: Only X quarters available."

### 6.4 API Connection Failure

**Scenario:** Unable to connect to API (network error, API down)

**Response:** Display cached data if available. If no cached data exists, show: "Unable to retrieve data. Please check your internet connection and try again."

### 6.5 Database Error

**Scenario:** Database connection fails or query error occurs

**Response:** Log error to console, attempt to fetch from API directly. Display message: "Database temporarily unavailable. Fetching fresh data..."

## 7. User Interface Design

### 7.1 Layout

- Top Section: Input area with ticker search box and refresh button
- Middle Section: Toggle buttons for Table/Chart view
- Main Section: Data display area (table or charts)
- Bottom Section: Data source attribution and last updated timestamp

### 7.2 Table View

- Columns: Q1 2023, Q2 2023, Q3 2023, Q4 2023, Q1 2024, Q2 2024, Q3 2024, Q4 2024
- Rows: Each financial metric (EPS, FCF, Gross Income, etc.)
- Alternating row colors for readability
- Right-align numbers, format with thousand separators

### 7.3 Chart View

- Separate line chart for each metric
- X-axis: Fiscal quarters (oldest to newest, left to right)
- Y-axis: Metric value with appropriate scale
- Color scheme: Blue for positive values, Red for negative values
- Hover tooltips showing exact values

### 7.4 Loading States

- Show spinner with message 'Searching database...' when querying local data
- Show progress indicator with message 'Fetching data from [API name]...' when calling API
- Disable input field and refresh button while data is loading

## 8. Development Roadmap

### 8.1 Phase 1: MVP (Minimum Viable Product)

- Database setup with schema implementation (SQLAlchemy models)
- Python backend with FastAPI/Flask and basic REST endpoints
- Basic UI with ticker input and table view
- API integration with one provider (FMP recommended)
- Data caching mechanism
- Basic error handling

**Timeline:** 2-3 weeks

### 8.2 Phase 2: Enhanced Visualization

- Implement chart view with line graphs
- Add toggle between table and chart views
- Improve styling and responsiveness
- Add trend indicators (green/red highlighting)

**Timeline:** 1-2 weeks

### 8.3 Phase 3: Advanced Features

- Multi-ticker comparison
- Export functionality (CSV, Excel, PNG)
- User preferences and saved searches
- Advanced filtering and sorting options

**Timeline:** 2-3 weeks

## 9. Testing Requirements

### 9.1 Unit Tests

- Database query functions
- API response parsing
- Data transformation utilities
- Validation functions

### 9.2 Integration Tests

- End-to-end ticker search flow
- Database-to-UI data flow
- API-to-database storage
- Error handling scenarios

### 9.3 Test Data

- Use well-known tickers for testing: AAPL, MSFT, GOOGL, TSLA
- Test with invalid tickers: INVALID, 123, XYZ999
- Test with newly listed companies (limited historical data)
- Mock API responses for offline testing

## 10. Deployment

### 10.1 Local Deployment

**Target:** Single-user desktop application

**Setup:** SQLite database, local Python Flask/FastAPI server, React frontend

**Access:** http://localhost:5000 (Flask) or http://localhost:8000 (FastAPI)

### 10.2 Web Deployment (Optional)

**Target:** Multi-user web application

**Hosting:** Heroku, DigitalOcean, or AWS

**Database:** PostgreSQL on Heroku or AWS RDS

**Considerations:** Implement user authentication if deploying publicly

## 11. Maintenance and Updates

### 11.1 Data Freshness

- Implement scheduled jobs to refresh data for frequently accessed tickers
- Set automatic data expiry after 30 days
- Notify users if data is stale (>30 days old)

### 11.2 API Monitoring

- Log API usage to track rate limit consumption
- Set up alerts for API failures or rate limit approaches
- Have backup API provider credentials ready

### 11.3 Database Maintenance

- Implement automated backups (daily for production)
- Periodically clean up data older than 5 years
- Monitor database size and optimize queries as needed

## 12. Future Enhancements

- Technical Analysis Integration: Add moving averages, RSI, MACD indicators
- Portfolio Tracking: Allow users to create and track portfolios; calculate aggregate metrics across portfolio
- Alerts and Notifications: Set alerts for specific financial thresholds (e.g., EPS > $5); Email notifications for quarterly earnings releases
- Peer Comparison: Automatically compare company with industry peers; Display industry averages and benchmarks
- AI-Powered Insights: Use ML to identify trends and anomalies; Generate automated analysis summaries

## 13. Appendix

### 13.1 Financial Data API Comparison

| Provider | Free Tier Limit | Data Coverage | Recommendation |
|---|---:|---|---|
| Financial Modeling Prep | 250 requests/day | Comprehensive, quarterly data | Primary choice |
| Alpha Vantage | 25 requests/day | Good coverage, some limitations | Backup option |
| Yahoo Finance (unofficial) | Unlimited (no guarantee) | Basic data, may change anytime | Not recommended |

### 13.2 Glossary of Financial Terms

- **EPS (Earnings Per Share):** Net income divided by number of outstanding shares. Indicates profitability per share.
- **Free Cash Flow (FCF):** Operating cash flow minus capital expenditures. Represents cash available for expansion, dividends, or debt reduction.
- **Gross Margin:** (Gross Income / Revenue) × 100. Percentage of revenue remaining after cost of goods sold.
- **Net Margin:** (Net Income / Revenue) × 100. Percentage of revenue remaining after all expenses.
- **CapEx (Capital Expenditures):** Funds used to acquire or upgrade physical assets. Indicates investment in long-term growth.
- **Cash Balance:** Total cash and cash equivalents. Indicates liquidity and financial flexibility.
- **Total Debt:** Sum of short-term and long-term debt obligations. Higher debt may indicate financial risk.

### 13.3 Example API Response Structure

Financial Modeling Prep Income Statement Response:

{ "date": "2024-09-30", "symbol": "AAPL", "reportedCurrency": "USD", "revenue": 94930000000, "grossProfit": 43882000000, "grossProfitRatio": 0.4623, "netIncome": 22956000000, "eps": 1.47, "period": "Q4" }

### 13.4 Python Backend Implementation Examples

**Example 1: FastAPI Endpoint for Ticker Data**

```python
from fastapi import FastAPI, HTTPException
from services.data_service import DataService

app = FastAPI()
data_service = DataService()

@app.get("/api/ticker/{symbol}")
async def get_ticker_data(symbol: str):
    """Retrieve financial data for a given ticker symbol"""
    try:
        data = await data_service.get_financial_data(symbol)
        return {
            "symbol": symbol,
            "data": data,
            "last_updated": data_service.get_last_updated(symbol)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Example 2: SQLAlchemy Models**

```python
from sqlalchemy import Column, Integer, String, DECIMAL, BigInteger, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    
    ticker = Column(String(10), primary_key=True)
    company_name = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)

class FinancialData(Base):
    __tablename__ = 'financial_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey('companies.ticker'))
    fiscal_quarter = Column(String(10))  # e.g., '2024-Q3'
    eps = Column(DECIMAL(10, 2))
    free_cash_flow = Column(BigInteger)
    gross_income = Column(BigInteger)
    gross_margin = Column(DECIMAL(5, 4))
    net_income = Column(BigInteger)
    net_margin = Column(DECIMAL(5, 4))
    capex = Column(BigInteger)
    cash_balance = Column(BigInteger)
    total_debt = Column(BigInteger)
    data_source = Column(String(50))
    fetched_at = Column(DateTime, default=datetime.utcnow)
```

**Example 3: Financial API Client with Retry Logic**

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

class FinancialAPIClient:
    def __init__(self):
        self.api_key = os.getenv('FMP_API_KEY')
        self.base_url = 'https://financialmodelingprep.com/api/v3'
        self.session = self._create_session()
    
    def _create_session(self):
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def get_income_statement(self, symbol: str, period: str = 'quarter', limit: int = 8):
        url = f"{self.base_url}/income-statement/{symbol}"
        params = {'period': period, 'limit': limit, 'apikey': self.api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
```

**Example 4: Data Service with Caching**

```python
from sqlalchemy.orm import Session
from models import Company, FinancialData
from datetime import datetime, timedelta
import pandas as pd

class DataService:
    def __init__(self, db: Session, api_client: FinancialAPIClient):
        self.db = db
        self.api_client = api_client
    
    async def get_financial_data(self, symbol: str):
        # Check cache first
        cached_data = self._get_from_cache(symbol)
        
        if cached_data and self._is_fresh(cached_data):
            return self._format_data(cached_data)
        
        # Fetch from API if cache miss or stale
        api_data = await self._fetch_from_api(symbol)
        self._store_in_cache(symbol, api_data)
        
        return self._format_data(api_data)
    
    def _is_fresh(self, data, max_age_days=30):
        if not data:
            return False
        latest = max(d.fetched_at for d in data)
        return datetime.utcnow() - latest < timedelta(days=max_age_days)
    
    def _format_data(self, data):
        # Convert to pandas DataFrame for easy manipulation
        df = pd.DataFrame([{
            'quarter': d.fiscal_quarter,
            'eps': float(d.eps),
            'fcf': d.free_cash_flow,
            'gross_income': d.gross_income,
            'gross_margin': float(d.gross_margin),
            'net_income': d.net_income,
            'net_margin': float(d.net_margin),
            'capex': d.capex,
            'cash': d.cash_balance,
            'debt': d.total_debt
        } for d in data])
        
        return df.to_dict('records')
```

**Example 5: requirements.txt for Python Backend**

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pandas==2.1.3
requests==2.31.0
python-dotenv==1.0.0
psycopg2-binary==2.9.9  # For PostgreSQL
pytest==7.4.3
httpx==0.25.1  # For testing async endpoints
```

--- End of Document ---
