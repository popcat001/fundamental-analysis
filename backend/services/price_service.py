"""
Price Service for stock price data management

This service handles caching and retrieval of stock price data,
using the database as a cache and fetching from yfinance when needed.
"""
from sqlalchemy.orm import Session
from models import StockPrice, Company
from api.stock_price_api import StockPriceAPIClient
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import logging
from config import settings

logger = logging.getLogger(__name__)


class PriceService:
    """Service for handling stock price data retrieval and caching"""

    def __init__(self, db: Session):
        self.db = db
        self.api_client = StockPriceAPIClient()

    def get_price_at_date(self, symbol: str, date: str) -> Optional[float]:
        """
        Get close price for a specific date, using cache or fetching if needed

        Strategy:
        1. Check database cache for exact date
        2. If not found, check +/- 5 days for nearest trading day
        3. If still not found, fetch from yfinance
        4. Store in cache and return

        Args:
            symbol: Stock ticker
            date: Date in YYYY-MM-DD format

        Returns:
            Close price or None if not available
        """
        symbol = symbol.upper()

        # Step 1: Check cache for exact date
        cached_price = self.db.query(StockPrice).filter(
            StockPrice.ticker == symbol,
            StockPrice.date == date
        ).first()

        if cached_price and self._is_data_fresh(cached_price.fetched_at, date):
            logger.info(f"Using cached price for {symbol} on {date}: ${cached_price.close}")
            return float(cached_price.close)

        # Step 2: Check cache for nearby dates
        target_dt = datetime.strptime(date, '%Y-%m-%d')
        start_range = (target_dt - timedelta(days=settings.PRICE_LOOKUP_DAYS_RANGE)).strftime('%Y-%m-%d')
        end_range = (target_dt + timedelta(days=settings.PRICE_LOOKUP_DAYS_RANGE)).strftime('%Y-%m-%d')

        nearby_prices = self.db.query(StockPrice).filter(
            StockPrice.ticker == symbol,
            StockPrice.date >= start_range,
            StockPrice.date <= end_range,
            StockPrice.date <= date  # Only earlier dates
        ).order_by(StockPrice.date.desc()).all()

        if nearby_prices:
            # Use the most recent price before target date
            nearest = nearby_prices[0]
            if self._is_data_fresh(nearest.fetched_at, nearest.date):
                logger.info(f"Using nearby cached price from {nearest.date} for {symbol} (target: {date})")
                return float(nearest.close)

        # Step 3: Fetch from yfinance
        logger.info(f"No cached price found for {symbol} on {date}, fetching from yfinance...")
        price_data = self.api_client.get_price_at_date(symbol, date)

        if price_data:
            # Store in cache
            self._store_price(symbol, price_data)
            return float(price_data['close'])

        logger.warning(f"Could not find price for {symbol} on {date}")
        return None

    def get_historical_prices(self, symbol: str, dates: List[str]) -> Dict[str, float]:
        """
        Get prices for multiple dates efficiently

        Strategy:
        1. Query all dates from cache in one DB call
        2. Identify missing dates
        3. Fetch missing date range from yfinance in one call
        4. Store all missing prices in cache
        5. Return complete dict of date -> price

        Args:
            symbol: Stock ticker
            dates: List of dates in YYYY-MM-DD format

        Returns:
            Dict mapping date to close price
        """
        symbol = symbol.upper()
        result = {}

        # Step 1: Check cache
        cached_prices = self.db.query(StockPrice).filter(
            StockPrice.ticker == symbol,
            StockPrice.date.in_(dates)
        ).all()

        cached_dict = {p.date: float(p.close) for p in cached_prices if self._is_data_fresh(p.fetched_at, p.date)}

        # Step 2: Identify missing dates
        missing_dates = [d for d in dates if d not in cached_dict]

        if not missing_dates:
            logger.info(f"All {len(dates)} prices for {symbol} found in cache")
            return cached_dict

        # Step 3: Fetch missing range from yfinance
        logger.info(f"Fetching {len(missing_dates)} missing dates for {symbol}")
        min_date = min(missing_dates)
        max_date = max(missing_dates)

        # Expand range slightly for better coverage
        start_date = (datetime.strptime(min_date, '%Y-%m-%d') - timedelta(days=settings.PRICE_FETCH_BUFFER_DAYS)).strftime('%Y-%m-%d')
        end_date = (datetime.strptime(max_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        fetched_prices = self.api_client.get_historical_prices(symbol, start_date, end_date)

        # Step 4: Store in cache and build result
        for price_data in fetched_prices:
            self._store_price(symbol, price_data)
            if price_data['date'] in dates:
                result[price_data['date']] = float(price_data['close'])

        # Step 5: Combine cached and fetched results
        result.update(cached_dict)

        # Handle any still-missing dates with nearest neighbor
        still_missing = [d for d in dates if d not in result]
        for missing_date in still_missing:
            price = self.get_price_at_date(symbol, missing_date)
            if price:
                result[missing_date] = price

        logger.info(f"Returning {len(result)} prices for {symbol} ({len(dates)} requested)")
        return result

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get the most recent price for a symbol

        Args:
            symbol: Stock ticker

        Returns:
            Current price
        """
        symbol = symbol.upper()

        # Try to get from yfinance
        current_price = self.api_client.get_current_price(symbol)

        if current_price:
            return current_price

        # Fallback: Get most recent cached price
        latest_price = self.db.query(StockPrice).filter(
            StockPrice.ticker == symbol
        ).order_by(StockPrice.date.desc()).first()

        if latest_price:
            logger.info(f"Using latest cached price for {symbol} from {latest_price.date}: ${latest_price.close}")
            return float(latest_price.close)

        logger.warning(f"Could not get current price for {symbol}")
        return None

    def _store_price(self, symbol: str, price_data: Dict):
        """
        Store price data in database cache

        Args:
            symbol: Stock ticker
            price_data: Dict with date, open, high, low, close, adjusted_close, volume
        """
        try:
            # Check if already exists
            existing = self.db.query(StockPrice).filter(
                StockPrice.ticker == symbol,
                StockPrice.date == price_data['date']
            ).first()

            # Store as naive UTC in database
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

            if existing:
                # Update existing
                existing.open = price_data['open']
                existing.high = price_data['high']
                existing.low = price_data['low']
                existing.close = price_data['close']
                existing.adjusted_close = price_data['adjusted_close']
                existing.volume = price_data['volume']
                existing.fetched_at = now_utc
            else:
                # Create new
                stock_price = StockPrice(
                    ticker=symbol,
                    date=price_data['date'],
                    open=price_data['open'],
                    high=price_data['high'],
                    low=price_data['low'],
                    close=price_data['close'],
                    adjusted_close=price_data['adjusted_close'],
                    volume=price_data['volume'],
                    data_source='yfinance',
                    fetched_at=now_utc
                )
                self.db.add(stock_price)

            self.db.commit()
            logger.debug(f"Stored price for {symbol} on {price_data['date']}")

        except Exception as e:
            logger.error(f"Error storing price for {symbol}: {str(e)}")
            self.db.rollback()

    def _is_data_fresh(self, fetched_at: datetime, date: str) -> bool:
        """
        Check if cached price data is fresh

        Logic:
        - For historical dates (>30 days old): Never expire (prices don't change)
        - For recent dates (<30 days): Expire after 1 day (allow for corrections)
        - For today's date: Always fetch fresh

        Args:
            fetched_at: When the price was fetched
            date: The date of the price data (YYYY-MM-DD)

        Returns:
            True if data is fresh, False if should re-fetch
        """
        if not fetched_at:
            return False

        # Parse the price date and make timezone-aware
        price_date = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        today = datetime.now(timezone.utc)

        # Make fetched_at timezone-aware if needed (database stores as UTC)
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)

        # How old is the price data itself?
        data_age_days = (today - price_date).days

        # Historical prices (>30 days old) never expire
        if data_age_days > 30:
            return True

        # Recent prices (<30 days) expire after 1 day
        cache_age_hours = (today - fetched_at).total_seconds() / 3600
        if cache_age_hours < 24:
            return True

        return False
