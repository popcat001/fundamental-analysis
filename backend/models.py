from sqlalchemy import Column, Integer, String, DECIMAL, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'

    ticker = Column(String(10), primary_key=True)
    company_name = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationship
    financial_data = relationship("FinancialData", back_populates="company")

    def __repr__(self):
        return f"<Company(ticker='{self.ticker}', name='{self.company_name}')>"

class FinancialData(Base):
    __tablename__ = 'financial_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey('companies.ticker'), nullable=False)
    fiscal_quarter = Column(String(10), nullable=False)  # e.g., '2024-Q3'
    eps = Column(DECIMAL(10, 2))
    free_cash_flow = Column(BigInteger)
    gross_income = Column(BigInteger)
    gross_margin = Column(DECIMAL(5, 4))
    net_income = Column(BigInteger)
    net_margin = Column(DECIMAL(5, 4))
    capex = Column(BigInteger)
    cash_balance = Column(BigInteger)
    total_debt = Column(BigInteger)
    data_source = Column(String(50))
    fetched_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    company = relationship("Company", back_populates="financial_data")

    # Unique constraint on ticker and fiscal_quarter combination
    __table_args__ = (
        UniqueConstraint('ticker', 'fiscal_quarter', name='_ticker_quarter_uc'),
    )

    def __repr__(self):
        return f"<FinancialData(ticker='{self.ticker}', quarter='{self.fiscal_quarter}')>"