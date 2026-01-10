"""
Stock Price API Client using yfinance

This module handles fetching historical stock prices from Yahoo Finance
via the yfinance library.
"""
import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockPriceAPIClient:
    """Client for fetching stock price data from Yahoo Finance"""

    def __init__(self):
        """Initialize the stock price API client"""
        pass

    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch historical daily prices using yfinance

        Args:
            symbol: Stock ticker
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List[Dict] with keys: date, open, high, low, close, adjusted_close, volume
        """
        try:
            logger.info(f"Fetching historical prices for {symbol} from {start_date} to {end_date}")

            # Create ticker object
            ticker = yf.Ticker(symbol)

            # Fetch historical data
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                logger.warning(f"No price data returned for {symbol}")
                return []

            # Convert to list of dicts
            prices = []
            for date, row in hist.iterrows():
                prices.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'adjusted_close': float(row['Close']),  # yfinance returns adjusted by default
                    'volume': int(row['Volume'])
                })

            logger.info(f"Fetched {len(prices)} days of price data for {symbol}")
            return prices

        except Exception as e:
            logger.error(f"Failed to fetch historical prices for {symbol}: {str(e)}")
            return []

    def get_price_at_date(self, symbol: str, target_date: str) -> Optional[Dict]:
        """
        Get price for a specific date, with fallback to nearest trading day

        Strategy:
        1. Try exact date match
        2. If weekend/holiday, try previous 5 business days
        3. Return None if no data found

        Args:
            symbol: Stock ticker
            target_date: Target date in YYYY-MM-DD format

        Returns:
            Dict with price data or None if not found
        """
        try:
            # Parse target date
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')

            # Fetch data for a range around the target date (target - 7 days to target + 1 day)
            start_date = (target_dt - timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = (target_dt + timedelta(days=1)).strftime('%Y-%m-%d')

            prices = self.get_historical_prices(symbol, start_date, end_date)

            if not prices:
                logger.warning(f"No prices found for {symbol} around {target_date}")
                return None

            # Try to find exact match first
            for price in prices:
                if price['date'] == target_date:
                    logger.info(f"Found exact price match for {symbol} on {target_date}")
                    return price

            # If no exact match, find the closest earlier date within 5 days
            target_ts = datetime.strptime(target_date, '%Y-%m-%d')
            closest_price = None
            closest_diff = None

            for price in prices:
                price_ts = datetime.strptime(price['date'], '%Y-%m-%d')

                # Only consider dates before or on target date
                if price_ts <= target_ts:
                    diff = (target_ts - price_ts).days

                    # Within 5 days
                    if diff <= 5:
                        if closest_diff is None or diff < closest_diff:
                            closest_diff = diff
                            closest_price = price

            if closest_price:
                logger.info(f"Using price from {closest_price['date']} for {symbol} (target: {target_date}, {closest_diff} days earlier)")
                return closest_price
            else:
                logger.warning(f"No suitable price found for {symbol} within 5 days of {target_date}")
                return None

        except Exception as e:
            logger.error(f"Error fetching price for {symbol} at {target_date}: {str(e)}")
            return None

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get the most recent closing price for a symbol

        Args:
            symbol: Stock ticker

        Returns:
            Current price or None if unavailable
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Try to get the current price from various fields
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')

            if current_price:
                logger.info(f"Current price for {symbol}: ${current_price:.2f}")
                return float(current_price)
            else:
                logger.warning(f"Could not get current price for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return None
