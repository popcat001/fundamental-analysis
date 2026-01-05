from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict
import re
from database import get_db
from services.data_service import DataService
from models import Company

router = APIRouter()

# Ticker validation regex (1-5 uppercase letters)
TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')

@router.get("/ticker/{symbol}", response_model=Dict)
def get_ticker_data(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve financial data for a given ticker symbol.

    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)

    Returns:
        Dict containing symbol, financial data, and last updated timestamp
    """
    # Validate ticker format
    symbol = symbol.upper()
    if not TICKER_PATTERN.match(symbol):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticker format: {symbol}. Must be 1-5 uppercase letters."
        )

    # Create data service
    data_service = DataService(db)

    try:
        # Get financial data (will use cache if available)
        financial_data = data_service.get_financial_data(symbol)

        # Get company info
        company = db.query(Company).filter(Company.ticker == symbol).first()

        return {
            "symbol": symbol,
            "company_name": company.company_name if company else symbol,
            "data": financial_data,
            "last_updated": company.last_updated.isoformat() if company and company.last_updated else None
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/ticker/{symbol}/refresh")
def refresh_ticker_data(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Force refresh financial data for a ticker symbol from the API.

    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)

    Returns:
        Dict containing refreshed financial data
    """
    # Validate ticker format
    symbol = symbol.upper()
    if not TICKER_PATTERN.match(symbol):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticker format: {symbol}. Must be 1-5 uppercase letters."
        )

    # Create data service
    data_service = DataService(db)

    try:
        # Force refresh from API
        financial_data = data_service.refresh_data(symbol)

        # Get updated company info
        company = db.query(Company).filter(Company.ticker == symbol).first()

        return {
            "symbol": symbol,
            "company_name": company.company_name if company else symbol,
            "data": financial_data,
            "last_updated": company.last_updated.isoformat() if company and company.last_updated else None,
            "message": "Data successfully refreshed from API"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh data: {str(e)}"
        )

@router.get("/tickers", response_model=List[Dict])
def get_cached_tickers(
    db: Session = Depends(get_db)
):
    """
    Get list of all tickers that have been previously searched and cached.

    Returns:
        List of ticker symbols with company names and last updated timestamps
    """
    companies = db.query(Company).order_by(Company.last_updated.desc()).all()

    return [
        {
            "symbol": company.ticker,
            "company_name": company.company_name,
            "last_updated": company.last_updated.isoformat() if company.last_updated else None
        }
        for company in companies
    ]

@router.get("/search", response_model=List[Dict])
def search_tickers(
    q: str = Query(..., min_length=1, max_length=5, description="Search query"),
    db: Session = Depends(get_db)
):
    """
    Search for tickers in the cached database.

    Args:
        q: Search query (partial ticker or company name)

    Returns:
        List of matching tickers
    """
    query = q.upper()

    # Search in both ticker and company name
    companies = db.query(Company).filter(
        (Company.ticker.like(f"{query}%")) |
        (Company.company_name.ilike(f"%{query}%"))
    ).limit(10).all()

    return [
        {
            "symbol": company.ticker,
            "company_name": company.company_name
        }
        for company in companies
    ]