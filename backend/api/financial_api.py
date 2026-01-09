import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional
from datetime import datetime
import logging
import time
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialAPIClient:
    """Client for fetching financial data from external APIs"""

    def __init__(self):
        self.alpha_vantage_api_key = settings.ALPHA_VANTAGE_API_KEY
        self.alpha_vantage_base_url = settings.ALPHA_VANTAGE_BASE_URL
        self.session = self._create_session()
        self.last_api_call_time = 0  # Track last API call for rate limiting
        self.min_call_interval = 1.5  # Minimum 1.5 seconds between calls (conservative to avoid warnings)

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
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

    def _wait_for_rate_limit(self):
        """Enforce rate limit of 1 request per second for Alpha Vantage"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call_time

        if time_since_last_call < self.min_call_interval:
            wait_time = self.min_call_interval - time_since_last_call
            logger.info(f"Rate limiting: waiting {wait_time:.2f} seconds before next API call")
            time.sleep(wait_time)

        self.last_api_call_time = time.time()

    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get company profile information from Alpha Vantage"""
        if not self.alpha_vantage_api_key:
            logger.error("Alpha Vantage API key not configured")
            return None

        self._wait_for_rate_limit()  # Enforce rate limit

        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.alpha_vantage_api_key
        }

        try:
            response = self.session.get(self.alpha_vantage_base_url, params=params, timeout=settings.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Check if we got valid data
            if data and 'Symbol' in data:
                # Transform Alpha Vantage format to match expected format
                return {
                    'companyName': data.get('Name', symbol),
                    'symbol': data.get('Symbol', symbol),
                    'sector': data.get('Sector', ''),
                    'industry': data.get('Industry', '')
                }
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch company info for {symbol}: {str(e)}")
            return None

    def get_earnings(self, symbol: str, limit: int = settings.NUM_QUARTERS) -> List[Dict]:
        """Get EPS data from Alpha Vantage EARNINGS endpoint"""
        if not self.alpha_vantage_api_key:
            logger.error("Alpha Vantage API key not configured")
            return []

        self._wait_for_rate_limit()  # Enforce rate limit

        params = {
            'function': 'EARNINGS',
            'symbol': symbol,
            'apikey': self.alpha_vantage_api_key
        }

        try:
            response = self.session.get(self.alpha_vantage_base_url, params=params, timeout=settings.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error for {symbol}: {data['Error Message']}")
                return []

            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note for {symbol}: {data['Note']}")
                return []

            # Alpha Vantage returns quarterly earnings - limit to requested number
            quarterly_earnings = data.get('quarterlyEarnings', [])[:limit]

            # Transform to a dict keyed by fiscal date for easy lookup
            eps_data = []
            for earning in quarterly_earnings:
                try:
                    eps_data.append({
                        'date': earning.get('fiscalDateEnding', ''),
                        'reportedDate': earning.get('reportedDate', ''),
                        'reportedEPS': float(earning.get('reportedEPS', 0) or 0)
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error converting EPS data for {symbol} report {earning.get('fiscalDateEnding')}: {e}")
                    continue

            logger.info(f"Fetched {len(eps_data)} quarters of EPS data for {symbol}")
            return eps_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch earnings for {symbol}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching earnings for {symbol}: {type(e).__name__}: {str(e)}")
            return []

    def get_income_statement(self, symbol: str, period: str = 'quarter', limit: int = settings.NUM_QUARTERS) -> List[Dict]:
        """Get income statement data from Alpha Vantage"""
        if not self.alpha_vantage_api_key:
            logger.error("Alpha Vantage API key not configured")
            return []

        self._wait_for_rate_limit()  # Enforce rate limit

        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': symbol,
            'apikey': self.alpha_vantage_api_key
        }

        try:
            response = self.session.get(self.alpha_vantage_base_url, params=params, timeout=settings.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error for {symbol}: {data['Error Message']}")
                return []

            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note for {symbol}: {data['Note']}")
                return []

            # Alpha Vantage returns quarterly reports under 'quarterlyReports' key
            reports = data.get('quarterlyReports', [])[:limit] if period == 'quarter' else data.get('annualReports', [])[:limit]

            if not reports:
                logger.warning(f"No reports found in Alpha Vantage response for {symbol}. Response keys: {list(data.keys())}")
                return []

            # Transform to match expected format
            transformed_reports = []
            for report in reports:
                try:
                    transformed_reports.append({
                        'date': report.get('fiscalDateEnding', ''),
                        'period': self._extract_quarter_from_date(report.get('fiscalDateEnding', '')),
                        'revenue': float(report.get('totalRevenue', 0) or 0),
                        'grossProfit': float(report.get('grossProfit', 0) or 0),
                        'netIncome': float(report.get('netIncome', 0) or 0),
                        'eps': 0  # Will be filled in from earnings data
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error converting data for {symbol} report {report.get('fiscalDateEnding')}: {e}")
                    continue

            logger.info(f"Fetched {len(transformed_reports)} quarters of income statement data for {symbol}")
            return transformed_reports
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch income statement for {symbol}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching income statement for {symbol}: {type(e).__name__}: {str(e)}")
            return []

    def get_cash_flow_statement(self, symbol: str, period: str = 'quarter', limit: int = settings.NUM_QUARTERS) -> List[Dict]:
        """Get cash flow statement data from Alpha Vantage"""
        if not self.alpha_vantage_api_key:
            logger.error("Alpha Vantage API key not configured")
            return []

        self._wait_for_rate_limit()  # Enforce rate limit

        params = {
            'function': 'CASH_FLOW',
            'symbol': symbol,
            'apikey': self.alpha_vantage_api_key
        }

        try:
            response = self.session.get(self.alpha_vantage_base_url, params=params, timeout=settings.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error for {symbol}: {data['Error Message']}")
                return []

            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note for {symbol}: {data['Note']}")
                return []

            # Alpha Vantage returns quarterly reports under 'quarterlyReports' key
            reports = data.get('quarterlyReports', [])[:limit] if period == 'quarter' else data.get('annualReports', [])[:limit]

            # Transform to match expected format
            transformed_reports = []
            for report in reports:
                try:
                    transformed_reports.append({
                        'date': report.get('fiscalDateEnding', ''),
                        'operatingCashFlow': float(report.get('operatingCashflow', 0) or 0),
                        'capitalExpenditure': float(report.get('capitalExpenditures', 0) or 0)
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error converting cash flow data for {symbol} report {report.get('fiscalDateEnding')}: {e}")
                    continue
            
            logger.info(f"Fetched {len(transformed_reports)} quarters of cash flow statement data for {symbol}")
            return transformed_reports
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch cash flow statement for {symbol}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching cash flow statement for {symbol}: {type(e).__name__}: {str(e)}")
            return []

    def get_balance_sheet(self, symbol: str, period: str = 'quarter', limit: int = settings.NUM_QUARTERS) -> List[Dict]:
        """Get balance sheet data from Alpha Vantage"""
        if not self.alpha_vantage_api_key:
            logger.error("Alpha Vantage API key not configured")
            return []

        self._wait_for_rate_limit()  # Enforce rate limit

        params = {
            'function': 'BALANCE_SHEET',
            'symbol': symbol,
            'apikey': self.alpha_vantage_api_key
        }

        try:
            response = self.session.get(self.alpha_vantage_base_url, params=params, timeout=settings.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error for {symbol}: {data['Error Message']}")
                return []

            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note for {symbol}: {data['Note']}")
                return []

            # Alpha Vantage returns quarterly reports under 'quarterlyReports' key
            reports = data.get('quarterlyReports', [])[:limit] if period == 'quarter' else data.get('annualReports', [])[:limit]

            # Transform to match expected format
            transformed_reports = []
            for report in reports:
                try:
                    transformed_reports.append({
                        'date': report.get('fiscalDateEnding', ''),
                        'cashAndCashEquivalents': float(report.get('cashAndCashEquivalentsAtCarryingValue', 0) or 0),
                        'shortTermDebt': float(report.get('shortTermDebt', 0) or 0),
                        'longTermDebt': float(report.get('longTermDebt', 0) or 0)
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error converting balance sheet data for {symbol} report {report.get('fiscalDateEnding')}: {e}")
                    continue
            
            logger.info(f"Fetched {len(transformed_reports)} quarters of balance sheet data for {symbol}")
            return transformed_reports
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch balance sheet for {symbol}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching balance sheet for {symbol}: {type(e).__name__}: {str(e)}")
            return []

    def _get_quarter_from_date(self, date_str: str) -> str:
        """Convert date string to quarter format (e.g., '2024-Q3')"""
        if not date_str:
            return ""
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            quarter = (date.month - 1) // 3 + 1
            return f"{date.year}-Q{quarter}"
        except ValueError:
            return date_str

    def _extract_quarter_from_date(self, date_str: str) -> str:
        """Extract quarter from date string (e.g., '2024-09-30' -> 'Q3')"""
        if not date_str:
            return ""
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            quarter = (date.month - 1) // 3 + 1
            return f"Q{quarter}"
        except ValueError:
            return ""