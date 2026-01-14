from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
import re
from datetime import datetime, timezone
from database import get_db
from services.data_service import DataService
from services.valuation_service import ValuationService
from models import Company, ValuationCache

router = APIRouter()

# Ticker validation regex (1-5 uppercase letters)
TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')

# Dependency for validating and normalizing ticker symbols
def validate_ticker(symbol: str = Path(..., description="Stock ticker symbol (1-5 letters)")) -> str:
    """
    Validate and normalize ticker symbol

    Args:
        symbol: Stock ticker symbol

    Returns:
        Normalized (uppercase) ticker symbol

    Raises:
        HTTPException: If ticker format is invalid
    """
    symbol = symbol.upper()
    if not TICKER_PATTERN.match(symbol):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticker format: {symbol}. Must be 1-5 uppercase letters."
        )
    return symbol

# Request models
class ValuationRequest(BaseModel):
    peers: Optional[List[str]] = None

@router.get("/ticker/{symbol}", response_model=Dict)
def get_ticker_data(
    symbol: str = Depends(validate_ticker),
    db: Session = Depends(get_db)
):
    """
    Retrieve financial data for a given ticker symbol.

    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)

    Returns:
        Dict containing symbol, financial data, and last updated timestamp
    """

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
    symbol: str = Depends(validate_ticker),
    db: Session = Depends(get_db)
):
    """
    Force refresh financial data for a ticker symbol from the API.

    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)

    Returns:
        Dict containing refreshed financial data
    """

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

@router.post("/valuation/{symbol}", response_model=Dict)
def calculate_valuation(
    symbol: str = Depends(validate_ticker),
    request: ValuationRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Calculate stock valuation using P/E multiple method

    Performs comprehensive valuation analysis including:
    - Forward EPS estimation (growth rate & regression methods)
    - Historical P/E ratio analysis
    - Peer comparison (if peers provided)
    - Fundamentals-based P/E calculation
    - Justified P/E synthesis
    - Fair value price range

    Args:
        symbol: Stock ticker (e.g., AAPL)
        request: ValuationRequest with optional peer list

    Returns:
        Complete valuation report with fair value estimates

    Example request body:
        {"peers": ["MSFT", "GOOGL", "META"]}
    """

    # Validate peer tickers if provided
    if request.peers:
        for peer in request.peers:
            if not TICKER_PATTERN.match(peer.upper()):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid peer ticker format: {peer}. Must be 1-5 uppercase letters."
                )

    # Create valuation service
    valuation_service = ValuationService(db)

    try:
        # Perform valuation analysis
        result = valuation_service.perform_valuation(
            symbol,
            [p.upper() for p in request.peers] if request.peers else None
        )
        return result

    except ValueError as e:
        # Insufficient data or other validation error
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=500,
            detail=f"Valuation calculation failed: {str(e)}"
        )

@router.get("/valuation/{symbol}", response_model=Dict)
def get_cached_valuation(
    symbol: str = Depends(validate_ticker),
    peers: Optional[str] = Query(None, description="Comma-separated peer tickers (e.g., 'MSFT,GOOGL,META')"),
    db: Session = Depends(get_db)
):
    """
    Get cached valuation results if available and fresh

    Returns previously calculated valuation if:
    - Calculation was performed within last 24 hours
    - Same peer list was used (order doesn't matter)

    Args:
        symbol: Stock ticker
        peers: Optional comma-separated peer tickers

    Returns:
        Cached valuation report or 404 if not found/expired

    Example:
        GET /api/valuation/AAPL?peers=MSFT,GOOGL,META
    """

    # Parse and sort peers for cache lookup
    peer_list = [p.strip().upper() for p in peers.split(',')] if peers else []
    peer_str = ','.join(sorted(peer_list))

    # Query cache (use naive datetime for database comparison)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    cache = db.query(ValuationCache).filter(
        ValuationCache.ticker == symbol,
        ValuationCache.peers == peer_str,
        ValuationCache.expires_at > now_utc
    ).first()

    if not cache:
        raise HTTPException(
            status_code=404,
            detail=f"No cached valuation found for {symbol}" + (f" with peers {peer_str}" if peer_str else "") + ". Use POST /api/valuation/{symbol} to calculate."
        )

    # Return cached full valuation report (includes all visualization data)
    if cache.valuation_data:
        # Return full cached report
        result = cache.valuation_data.copy() if isinstance(cache.valuation_data, dict) else cache.valuation_data
        result["cached"] = True
        result["calculated_at"] = cache.calculated_at.isoformat()
        return result
    else:
        # Fallback to simplified format for old cache entries without valuation_data
        return {
            "symbol": symbol,
            "cached": True,
            "calculated_at": cache.calculated_at.isoformat(),
            "expires_at": cache.expires_at.isoformat(),
            "forward_eps": {
                "growth_method": cache.forward_eps_growth,
                "regression_method": cache.forward_eps_regression,
                "recommended": (float(cache.forward_eps_growth) + float(cache.forward_eps_regression)) / 2 if cache.forward_eps_growth and cache.forward_eps_regression else None
            },
            "historical_pe": {
                "average": float(cache.historical_pe_avg) if cache.historical_pe_avg else None,
                "median": float(cache.historical_pe_median) if cache.historical_pe_median else None
            },
            "peer_comparison": {
                "average_pe": float(cache.peer_pe_avg) if cache.peer_pe_avg else None,
                "peers": peer_list
            },
            "fundamentals_pe": float(cache.fundamentals_pe) if cache.fundamentals_pe else None,
            "justified_pe": {
                "low": float(cache.justified_pe_low) if cache.justified_pe_low else None,
                "high": float(cache.justified_pe_high) if cache.justified_pe_high else None,
                "midpoint": (float(cache.justified_pe_low) + float(cache.justified_pe_high)) / 2 if cache.justified_pe_low and cache.justified_pe_high else None
            },
            "fair_value": {
                "low": float(cache.fair_value_low) if cache.fair_value_low else None,
                "high": float(cache.fair_value_high) if cache.fair_value_high else None,
                "midpoint": (float(cache.fair_value_low) + float(cache.fair_value_high)) / 2 if cache.fair_value_low and cache.fair_value_high else None
            },
            "note": "This is cached data without visualization details. Use POST /api/valuation/{symbol} to recalculate with full data."
        }