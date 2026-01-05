import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Configuration settings for the application"""

    # API Keys
    FMP_API_KEY = os.getenv("FMP_API_KEY", "")
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "")  # PostgreSQL URL if provided

    # API Configuration
    FMP_BASE_URL = "https://financialmodelingprep.com/stable"
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

    # Cache settings
    CACHE_EXPIRY_DAYS = int(os.getenv("CACHE_EXPIRY_DAYS", "30"))

    # API Rate Limits
    FMP_DAILY_LIMIT = 250  # Free tier limit
    ALPHA_VANTAGE_DAILY_LIMIT = 25  # Free tier limit

    # Request Timeouts
    API_REQUEST_TIMEOUT = 10  # seconds

    # Frontend URL for CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Create settings instance
settings = Settings()