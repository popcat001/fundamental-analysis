# Fundamental Analysis Tool

A web-based tool for viewing financial data of publicly traded companies, built with FastAPI (backend) and React (frontend).

## Features

- **Ticker Search**: Look up financial data for any publicly traded company
- **Data Caching**: Intelligent caching to minimize API calls and improve performance
- **8 Quarter History**: View up to 8 quarters of historical financial data
- **Key Metrics**: Track important metrics including:
  - Earnings Per Share (EPS)
  - Free Cash Flow
  - Gross Income & Margin
  - Net Income & Margin
  - Capital Expenditures
  - Cash Balance
  - Total Debt
- **Auto-refresh**: Automatically fetches new data if cached data is older than 30 days
- **Manual Refresh**: Force-refresh data with a single click

## Prerequisites

- Python 3.9 or higher
- Node.js 14 or higher
- uv (Python package manager) - Install with: `pip install uv`
- Financial Modeling Prep API key (free tier available at https://financialmodelingprep.com/)

## Setup Instructions

### 1. Clone the Repository

```bash
cd fundamental-analysis
```

### 2. Backend Setup

#### Create Environment File

```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your API key:
```
FMP_API_KEY=your_api_key_here
```

#### Install Dependencies

From the project root directory:

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Dependencies are already installed via uv
```

### 3. Frontend Setup

```bash
cd frontend
bun install
```

## Running the Application

### Start the Backend Server

From the project root directory:

```bash
cd backend
uv run app.py
```

Stop the backend
```
ps aux | grep uvicorn | grep -v grep
kill -9 <PID>

lsof -ti:8000 # Find process that is using the port
kill <PID>
```

The backend will start on http://localhost:8000

You can view the API documentation at http://localhost:8000/docs

### Start the Frontend Development Server

In a new terminal:

```bash
cd frontend
bun start
```

The frontend will start on http://localhost:3000

## Usage

1. Open http://localhost:3000 in your browser
2. Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
3. Click "Search" to retrieve financial data
4. View the data in a table format showing the last 8 quarters
5. Click "Refresh Data" to force-fetch the latest data from the API

## API Endpoints

- `GET /api/ticker/{symbol}` - Get financial data for a ticker
- `POST /api/ticker/{symbol}/refresh` - Force refresh data from API
- `GET /api/tickers` - List all cached tickers
- `GET /api/search?q={query}` - Search for tickers

## Database

The application uses SQLite for local development. The database file (`fundamental_analysis.db`) will be created automatically in the backend directory when you first run the application.

For production deployment, you can configure PostgreSQL by setting the `DATABASE_URL` environment variable.

## Project Structure

```
fundamental-analysis/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── financial_api.py    # External API client
│   │   └── routes.py           # FastAPI routes
│   ├── services/
│   │   ├── __init__.py
│   │   └── data_service.py     # Business logic & caching
│   ├── app.py                  # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection
│   ├── models.py               # SQLAlchemy models
│   └── .env.example            # Environment variables template
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── services/           # API client
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
└── README.md
```

## Troubleshooting

### API Key Issues
- Ensure your FMP API key is correctly set in the `.env` file
- Check that you haven't exceeded the daily API limit (250 requests for free tier)

### Database Issues
- If you encounter database errors, try deleting `fundamental_analysis.db` and restarting the backend

### CORS Issues
- The backend is configured to allow requests from `http://localhost:3000`
- If running the frontend on a different port, update `FRONTEND_URL` in the `.env` file

### Connection Issues
- Ensure both backend (port 8000) and frontend (port 3000) servers are running
- Check that no other applications are using these ports

## Future Enhancements (Phase 2 & 3)

- Chart visualizations with trend analysis
- Multi-ticker comparison
- Export functionality (CSV, Excel)
- Technical indicators integration
- Portfolio tracking
- Industry peer comparison

## License

This project is licensed under the MIT License.