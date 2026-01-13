from sqlalchemy import Column, Integer, String, DECIMAL, BigInteger, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'

    ticker = Column(String(10), primary_key=True)
    company_name = Column(String(255))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    financial_data = relationship("FinancialData", back_populates="company")
    stock_prices = relationship("StockPrice", back_populates="company")
    valuations = relationship("ValuationCache", back_populates="company")

    def __repr__(self):
        return f"<Company(ticker='{self.ticker}', name='{self.company_name}')>"

class FinancialData(Base):
    __tablename__ = 'financial_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey('companies.ticker'), nullable=False, index=True)
    fiscal_quarter = Column(String(10), nullable=False)  # e.g., '2024-Q3'
    fiscal_date = Column(String(10))  # e.g., '2024-09-30'
    reported_date = Column(String(10))  # e.g., '2024-10-31' - when earnings were reported
    eps = Column(DECIMAL(10, 2))
    revenue = Column(BigInteger)  # Total revenue for the quarter
    free_cash_flow = Column(BigInteger)
    gross_income = Column(BigInteger)
    gross_margin = Column(DECIMAL(5, 4))
    net_income = Column(BigInteger)
    net_margin = Column(DECIMAL(5, 4))
    capex = Column(BigInteger)
    cash_balance = Column(BigInteger)
    total_debt = Column(BigInteger)
    data_source = Column(String(50))
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationship
    company = relationship("Company", back_populates="financial_data")

    # Unique constraint on ticker and fiscal_quarter combination
    __table_args__ = (
        UniqueConstraint('ticker', 'fiscal_quarter', name='_ticker_quarter_uc'),
    )

    def __repr__(self):
        return f"<FinancialData(ticker='{self.ticker}', quarter='{self.fiscal_quarter}')>"

class StockPrice(Base):
    __tablename__ = 'stock_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey('companies.ticker'), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    open = Column(DECIMAL(10, 2))
    high = Column(DECIMAL(10, 2))
    low = Column(DECIMAL(10, 2))
    close = Column(DECIMAL(10, 2), nullable=False)  # Primary price for P/E calculations
    adjusted_close = Column(DECIMAL(10, 2))
    volume = Column(BigInteger)
    data_source = Column(String(50), default='yfinance')
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    company = relationship("Company", back_populates="stock_prices")

    # Unique constraint on ticker and date combination
    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='_ticker_date_uc'),
    )

    def __repr__(self):
        return f"<StockPrice(ticker='{self.ticker}', date='{self.date}', close={self.close})>"

class ValuationCache(Base):
    __tablename__ = 'valuation_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey('companies.ticker'), nullable=False, index=True)
    peers = Column(String(255))  # Comma-separated list of peer tickers

    # Forward EPS estimates
    forward_eps_growth = Column(DECIMAL(10, 2))
    forward_eps_regression = Column(DECIMAL(10, 2))

    # P/E metrics
    historical_pe_avg = Column(DECIMAL(10, 2))
    historical_pe_median = Column(DECIMAL(10, 2))
    peer_pe_avg = Column(DECIMAL(10, 2))
    fundamentals_pe = Column(DECIMAL(10, 2))

    # Final justified P/E range
    justified_pe_low = Column(DECIMAL(10, 2))
    justified_pe_high = Column(DECIMAL(10, 2))

    # Implied price range
    fair_value_low = Column(DECIMAL(10, 2))
    fair_value_high = Column(DECIMAL(10, 2))

    # Full valuation report (includes all visualization data)
    valuation_data = Column(JSON)  # Complete valuation report for charts

    # Metadata
    calculated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, index=True)  # For cache invalidation

    # Relationship
    company = relationship("Company", back_populates="valuations")

    # Unique constraint on ticker and peers combination
    __table_args__ = (
        UniqueConstraint('ticker', 'peers', name='_ticker_peers_uc'),
    )

    def __repr__(self):
        return f"<ValuationCache(ticker='{self.ticker}', peers='{self.peers}')>"