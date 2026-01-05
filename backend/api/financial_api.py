import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional
from datetime import datetime
import logging
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialAPIClient:
    """Client for fetching financial data from external APIs"""

    def __init__(self):
        self.fmp_api_key = settings.FMP_API_KEY
        self.alpha_vantage_api_key = settings.ALPHA_VANTAGE_API_KEY
        self.fmp_base_url = settings.FMP_BASE_URL
        self.alpha_vantage_base_url = settings.ALPHA_VANTAGE_BASE_URL
        self.session = self._create_session()

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

    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get company profile information"""
        if not self.fmp_api_key:
            logger.error("FMP API key not configured")
            return None

        url = f"{self.fmp_base_url}/profile/{symbol}"
        params = {'apikey': self.fmp_api_key}

        try:
            response = self.session.get(url, params=params, timeout=settings.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]  # FMP returns a list with one item
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch company info for {symbol}: {str(e)}")
            return None

    def get_income_statement(self, symbol: str, period: str = 'quarter', limit: int = 4) -> List[Dict]:
        """Get income statement data from FMP"""
        if not self.fmp_api_key:
            logger.error("FMP API key not configured")
            return []

        url = f"{self.fmp_base_url}/income-statement"
        params = {
            'symbol': symbol,
            'period': period,
            'limit': limit,
            'apikey': self.fmp_api_key
        }

        try:
            response = self.session.get(url, params=params, timeout=settings.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            print(response.json())
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch income statement for {symbol}: {str(e)}")
            # Try fallback to Alpha Vantage
            return []

    def get_cash_flow_statement(self, symbol: str, period: str = 'quarter', limit: int = 4) -> List[Dict]:
        """Get cash flow statement data from FMP"""
        if not self.fmp_api_key:
            logger.error("FMP API key not configured")
            return []

        url = f"{self.fmp_base_url}/cash-flow-statement"
        params = {
            'symbol': symbol,
            'period': period,
            'limit': limit,
            'apikey': self.fmp_api_key
        }

        try:
            response = self.session.get(url, params=params, timeout=settings.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch cash flow statement for {symbol}: {str(e)}")
            return []

    def get_balance_sheet(self, symbol: str, period: str = 'quarter', limit: int = 4) -> List[Dict]:
        """Get balance sheet data from FMP"""
        if not self.fmp_api_key:
            logger.error("FMP API key not configured")
            return []

        url = f"{self.fmp_base_url}/balance-sheet-statement"
        params = {
            'symbol': symbol,
            'period': period,
            'limit': limit,
            'apikey': self.fmp_api_key
        }

        try:
            response = self.session.get(url, params=params, timeout=settings.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch balance sheet for {symbol}: {str(e)}")
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