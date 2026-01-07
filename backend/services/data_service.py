from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Company, FinancialData
from api.financial_api import FinancialAPIClient
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import logging
from config import settings

logger = logging.getLogger(__name__)

class DataService:
    """Service for handling financial data retrieval and caching"""

    def __init__(self, db: Session):
        self.db = db
        self.api_client = FinancialAPIClient()

    def get_financial_data(self, symbol: str) -> List[Dict]:
        """
        Get financial data for a symbol, using cache if available and fresh
        """
        symbol = symbol.upper()
        logger.info(f"Starting get_financial_data for {symbol}")

        try:
            # Check if company exists in database
            logger.info(f"Getting or creating company record for {symbol}")
            company = self._get_or_create_company(symbol)

            # Check cache
            logger.info(f"Fetch cached data from database for {symbol}")
            cached_data = self._get_cached_data(symbol)

            # Check if cached data is fresh
            if cached_data and self._is_data_fresh(cached_data):
                logger.info(f"Returning cached data for {symbol}")
                return self._format_data(cached_data)

            # Fetch fresh data from API
            logger.info(f"Fetching fresh data from API for {symbol}")
            fresh_data = self._fetch_from_api(symbol)

            if fresh_data:
                # Store in cache
                logger.info(f"Storing {len(fresh_data)} quarters in cache for {symbol}")
                self._store_in_cache(symbol, fresh_data)
                logger.info(f"Successfully stored data for {symbol}")
                # Fetch back from cache to get FinancialData objects for formatting
                cached_data = self._get_cached_data(symbol)
                return self._format_data(cached_data)

            # If API fetch failed but we have stale cached data, return it
            if cached_data:
                logger.warning(f"API fetch failed, returning stale cached data for {symbol}")
                return self._format_data(cached_data)

            # No data available
            logger.error(f"No data available for {symbol}")
            raise ValueError(f"Unable to retrieve data for ticker {symbol}")

        except ValueError:
            # Re-raise ValueError as-is (404 error)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_financial_data for {symbol}: {type(e).__name__}: {str(e)}", exc_info=True)
            raise

    def _get_or_create_company(self, symbol: str) -> Company:
        """Get or create a company record"""
        company = self.db.query(Company).filter(Company.ticker == symbol).first()

        if not company:
            # Try to get company info from API
            company_info = self.api_client.get_company_info(symbol)

            company = Company(
                ticker=symbol,
                company_name=company_info.get('companyName', symbol) if company_info else symbol
            )
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)

        return company

    def _get_cached_data(self, symbol: str) -> List[FinancialData]:
        """Get cached financial data from database"""
        return self.db.query(FinancialData).filter(
            FinancialData.ticker == symbol
        ).order_by(FinancialData.fiscal_quarter.desc()).limit(8).all()

    def _is_data_fresh(self, data: List[FinancialData]) -> bool:
        """Check if cached data is fresh (less than CACHE_EXPIRY_DAYS old)"""
        if not data:
            return False

        # Check the most recent fetch time
        latest_fetch = max(d.fetched_at for d in data)
        age_days = (datetime.utcnow() - latest_fetch).days

        return age_days < settings.CACHE_EXPIRY_DAYS

    def _fetch_from_api(self, symbol: str) -> List[Dict]:
        """
        Fetch fresh data from external API
        Note: Due to Alpha Vantage rate limiting (1.5 sec between calls), this takes ~6 seconds
        to fetch all four data sources (earnings, income, cash flow, balance sheet)
        """
        # Get all financial data including EPS
        eps_data = self.api_client.get_earnings(symbol)
        income_data = self.api_client.get_income_statement(symbol)
        cash_flow_data = self.api_client.get_cash_flow_statement(symbol)
        balance_sheet_data = self.api_client.get_balance_sheet(symbol)

        if not income_data:
            logger.warning(f"No income statement data returned for {symbol}")
            return []

        logger.info(f"Processing {len(income_data)} quarters for {symbol}")

        # Combine data from all three statements
        combined_data = []

        for income in income_data:  # Process all returned quarters
            date = income.get('date')
            period = income.get('period')

            # Find matching cash flow, balance sheet, and EPS data
            cash_flow = next((cf for cf in cash_flow_data if cf.get('date') == date), {})
            balance_sheet = next((bs for bs in balance_sheet_data if bs.get('date') == date), {})
            eps_record = next((ep for ep in eps_data if ep.get('date') == date), {})

            if not cash_flow:
                logger.warning(f"No cash flow data for {symbol} on {date}")
            if not balance_sheet:
                logger.warning(f"No balance sheet data for {symbol} on {date}")
            if not eps_record:
                logger.warning(f"No EPS data for {symbol} on {date}")

            # Calculate derived metrics
            revenue = income.get('revenue', 0)
            gross_profit = income.get('grossProfit', 0)
            net_income = income.get('netIncome', 0)

            gross_margin = (gross_profit / revenue) if revenue > 0 else 0
            net_margin = (net_income / revenue) if revenue > 0 else 0

            # Extract free cash flow (operating cash flow - capex)
            operating_cash_flow = cash_flow.get('operatingCashFlow', 0)
            capex = abs(cash_flow.get('capitalExpenditure', 0))  # Usually negative
            free_cash_flow = operating_cash_flow - capex

            combined = {
                'fiscal_quarter': self._format_quarter(date, period),
                'eps': eps_record.get('reportedEPS', 0),
                'free_cash_flow': free_cash_flow,
                'gross_income': gross_profit,
                'gross_margin': gross_margin,
                'net_income': net_income,
                'net_margin': net_margin,
                'capex': capex,
                'cash_balance': balance_sheet.get('cashAndCashEquivalents', 0),
                'total_debt': (balance_sheet.get('shortTermDebt', 0) +
                              balance_sheet.get('longTermDebt', 0)),
                'data_source': 'Alpha Vantage'
            }
            combined_data.append(combined)

        quarters = [d['fiscal_quarter'] for d in combined_data]
        logger.info(f"Fetched data for {symbol}: {quarters}")

        return combined_data

    def _store_in_cache(self, symbol: str, data: List[Dict]):
        """Store financial data in database cache"""
        try:
            # Update company last_updated timestamp
            company = self.db.query(Company).filter(Company.ticker == symbol).first()
            if company:
                company.last_updated = datetime.utcnow()
                logger.info(f"Updated last_updated for {symbol}")

            for record in data:
                # Check if record already exists
                existing = self.db.query(FinancialData).filter(
                    FinancialData.ticker == symbol,
                    FinancialData.fiscal_quarter == record['fiscal_quarter']
                ).first()

                if existing:
                    # Update existing record
                    logger.info(f"Updating existing record for {symbol} {record['fiscal_quarter']}")
                    for key, value in record.items():
                        if key != 'fiscal_quarter':
                            setattr(existing, key, value)
                    existing.fetched_at = datetime.utcnow()
                else:
                    # Create new record
                    logger.info(f"Creating new record for {symbol} {record['fiscal_quarter']}")
                    financial_data = FinancialData(
                        ticker=symbol,
                        **record
                    )
                    self.db.add(financial_data)

            self.db.commit()
            logger.info(f"Successfully committed {len(data)} records for {symbol}")

        except Exception as e:
            logger.error(f"Error storing data for {symbol}: {type(e).__name__}: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

    def _format_data(self, data: List[FinancialData]) -> List[Dict]:
        """Format financial data for API response"""
        formatted = []

        for record in data:
            formatted.append({
                'quarter': record.fiscal_quarter,
                'eps': float(record.eps) if record.eps else 0,
                'fcf': record.free_cash_flow,
                'gross_income': record.gross_income,
                'gross_margin': float(record.gross_margin) if record.gross_margin else 0,
                'net_income': record.net_income,
                'net_margin': float(record.net_margin) if record.net_margin else 0,
                'capex': record.capex,
                'cash': record.cash_balance,
                'debt': record.total_debt,
                'source': record.data_source,
                'last_updated': record.fetched_at.isoformat() if record.fetched_at else None
            })

        # Sort by quarter descending (newest first)
        formatted.sort(key=lambda x: x['quarter'], reverse=True)

        return formatted

    def _format_quarter(self, date_str: str, period: str) -> str:
        """Format date and period into quarter string (e.g., '2024-Q3')"""
        if period and period.startswith('Q'):
            # Already in quarter format
            year = date_str[:4] if date_str else ''
            return f"{year}-{period}"

        # Convert date to quarter
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            quarter = (date.month - 1) // 3 + 1
            return f"{date.year}-Q{quarter}"
        except ValueError:
            return date_str

    def refresh_data(self, symbol: str) -> List[Dict]:
        """Force refresh data from API, bypassing cache"""
        symbol = symbol.upper()

        # Ensure company exists
        self._get_or_create_company(symbol)

        # Fetch fresh data from API (combines all three statements)
        fresh_data = self._fetch_from_api(symbol)

        if fresh_data:
            # Delete old cached data for this ticker to avoid stale data
            self.db.query(FinancialData).filter(
                FinancialData.ticker == symbol
            ).delete()
            self.db.commit()

            # Store fresh data in cache
            self._store_in_cache(symbol, fresh_data)
            return self._format_data(self._get_cached_data(symbol))

        raise ValueError(f"Unable to refresh data for ticker {symbol}")