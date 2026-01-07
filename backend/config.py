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

# Create settings instance
settings = Settings()