"""
SQLAlchemy database models for ECB Financial Data Visualizer
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from typing import Optional

Base = declarative_base()

class FinancialSeries(Base):
    """Financial time series metadata"""
    __tablename__ = 'financial_series'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    frequency = Column(String(10), nullable=False)
    unit = Column(String(50), nullable=True)
    source_agency = Column(String(50), nullable=False, default="ECB")
    last_updated = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Relationship to observations
    observations = relationship("Observation", back_populates="series", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FinancialSeries(key={self.series_key}, name={self.name})>"

class Observation(Base):
    """Individual data observations"""
    __tablename__ = 'observations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(Integer, ForeignKey('financial_series.id'), nullable=False, index=True)
    period = Column(String(20), nullable=False, index=True)
    value = Column(Float, nullable=False)
    status = Column(String(10), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Relationship to series
    series = relationship("FinancialSeries", back_populates="observations")
    
    # Unique constraint on series_id + period
    __table_args__ = (
        {'sqlite_autoincrement': True}
    )
    
    def __repr__(self):
        return f"<Observation(series_id={self.series_id}, period={self.period}, value={self.value})>"

class DataFetchLog(Base):
    """Log of data fetch operations"""
    __tablename__ = 'data_fetch_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_key = Column(String(100), nullable=False, index=True)
    fetch_timestamp = Column(DateTime, nullable=False, default=datetime.now)
    success = Column(String(10), nullable=False)  # 'success' or 'error'
    observations_count = Column(Integer, nullable=False, default=0)
    error_message = Column(String(500), nullable=True)
    
    def __repr__(self):
        return f"<DataFetchLog(series_key={self.series_key}, success={self.success})>"
