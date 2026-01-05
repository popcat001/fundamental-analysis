from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Create SQLAlchemy engine
# For local development, we'll use SQLite. For production, use PostgreSQL.
if settings.DATABASE_URL:
    engine = create_engine(settings.DATABASE_URL)
else:
    # SQLite database for local development
    SQLALCHEMY_DATABASE_URL = "sqlite:///./fundamental_analysis.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base from models
from models import Base

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()