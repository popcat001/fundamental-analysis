import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Configuration settings for the application"""

    # API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "")  # PostgreSQL URL if provided

    # API Configuration
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

    # Cache settings
    CACHE_EXPIRY_DAYS = int(os.getenv("CACHE_EXPIRY_DAYS", "30"))

    # API Rate Limits
    # Alpha Vantage Free Tier Limits:
    # - 1.5 seconds between requests (enforced in code, conservative to avoid warnings)
    # - 25 requests per day
    ALPHA_VANTAGE_DAILY_LIMIT = 25
    ALPHA_VANTAGE_RATE_LIMIT = 1.5  # seconds between requests

    # Request Timeouts
    API_REQUEST_TIMEOUT = 15  # seconds (increased to account for rate limiting)

    # Frontend URL for CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Quarter limit for financial statements
    NUM_QUARTERS = 16

    # Valuation Cache Settings
    VALUATION_CACHE_HOURS = int(os.getenv("VALUATION_CACHE_HOURS", "24"))

    # Stock Price Cache Settings
    PRICE_CACHE_DAYS_HISTORICAL = int(os.getenv("PRICE_CACHE_DAYS_HISTORICAL", "999999"))  # Never expire historical
    PRICE_CACHE_DAYS_RECENT = int(os.getenv("PRICE_CACHE_DAYS_RECENT", "1"))  # 1 day for recent

    # Valuation Calculation Settings
    PE_BASE_MARKET = float(os.getenv("PE_BASE_MARKET", "22.0"))  # Market baseline P/E, use S&P 500 forward P/E
    PE_GROWTH_MULTIPLIER = float(os.getenv("PE_GROWTH_MULTIPLIER", "0.5"))  # Growth adjustment factor
    MIN_QUARTERS_FOR_VALUATION = int(os.getenv("MIN_QUARTERS_FOR_VALUATION", "8"))  # Minimum quarters needed

    # EPS Calculation Settings
    TTM_QUARTERS = 4  # Trailing twelve months = 4 quarters

    # Fundamentals P/E Adjustment Thresholds
    EXCELLENT_NET_MARGIN_THRESHOLD = 0.20  # 20% net margin threshold
    MARGIN_EXCELLENT_ADJUSTMENT = 3  # P/E adjustment for excellent margins
    MARGIN_IMPROVING_ADJUSTMENT = 2  # P/E adjustment for improving margins
    HIGH_DEBT_TO_EQUITY_THRESHOLD = 1.5  # Debt-to-equity ratio threshold
    DEBT_RISK_ADJUSTMENT = -2  # P/E adjustment for high debt
    DECLINING_MARGIN_ADJUSTMENT = -2  # P/E adjustment for declining margins

    # Justified P/E Weighting (with peer comparison)
    PE_WEIGHT_HISTORICAL = 0.4  # Weight for historical P/E
    PE_WEIGHT_PEER = 0.3  # Weight for peer P/E
    PE_WEIGHT_FUNDAMENTALS = 0.3  # Weight for fundamentals P/E

    # Justified P/E Weighting (without peer comparison)
    PE_WEIGHT_HISTORICAL_NO_PEER = 0.57  # Weight for historical P/E when no peers
    PE_WEIGHT_FUNDAMENTALS_NO_PEER = 0.43  # Weight for fundamentals P/E when no peers

    # Stock Price Lookup Settings
    PRICE_LOOKUP_DAYS_RANGE = 5  # Days to search before/after target date
    PRICE_FETCH_BUFFER_DAYS = 7  # Buffer days when fetching historical price range

# Create settings instance
settings = Settings()