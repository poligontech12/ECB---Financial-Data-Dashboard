"""
Pydantic data models for ECB API responses and internal data structures
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class SeriesFrequency(str, Enum):
    """ECB data frequency types"""
    DAILY = "D"
    WEEKLY = "W" 
    MONTHLY = "M"
    QUARTERLY = "Q"
    ANNUAL = "A"

class ObservationStatus(str, Enum):
    """ECB observation status codes"""
    NORMAL = "A"
    BREAK = "B"
    ESTIMATED = "E"
    FORECAST = "F"
    MISSING = "M"
    PROVISIONAL = "P"

class ECBObservation(BaseModel):
    """Individual observation from ECB API"""
    period: str = Field(..., description="Time period (YYYY-MM-DD, YYYY-MM, etc.)")
    value: Optional[float] = Field(None, description="Observation value")
    status: Optional[ObservationStatus] = Field(None, description="Observation status")
    
    @validator('period')
    def validate_period(cls, v):
        """Validate period format"""
        if not v or len(v) < 4:
            raise ValueError("Period must be at least 4 characters (YYYY)")
        return v

class SeriesMetadata(BaseModel):
    """Metadata for a time series"""
    series_key: str = Field(..., description="ECB series key")
    title: str = Field(..., description="Series title") 
    unit: Optional[str] = Field(None, description="Unit of measurement")
    frequency: SeriesFrequency = Field(..., description="Data frequency")
    source_agency: str = Field(default="ECB", description="Source agency")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
class ECBSeriesData(BaseModel):
    """Complete series data from ECB API"""
    metadata: SeriesMetadata
    observations: List[ECBObservation] = Field(default_factory=list)
    
    @property
    def latest_value(self) -> Optional[float]:
        """Get the most recent observation value"""
        if not self.observations:
            return None
        # Sort by period and get the last value
        sorted_obs = sorted(self.observations, key=lambda x: x.period)
        return sorted_obs[-1].value if sorted_obs else None
    
    @property
    def observation_count(self) -> int:
        """Get total number of observations"""
        return len(self.observations)

class ExchangeRateData(ECBSeriesData):
    """EUR/USD exchange rate specific data"""
    
    def get_percentage_change(self, days: int = 1) -> Optional[float]:
        """Calculate percentage change over specified number of days"""
        if len(self.observations) < days + 1:
            return None
            
        sorted_obs = sorted(self.observations, key=lambda x: x.period)
        if len(sorted_obs) < days + 1:
            return None
            
        current = sorted_obs[-1].value
        previous = sorted_obs[-(days + 1)].value
        
        if current is None or previous is None or previous == 0:
            return None
            
        return ((current - previous) / previous) * 100

class InflationData(ECBSeriesData):
    """Inflation rate specific data"""
    
    @property
    def target_deviation(self) -> Optional[float]:
        """Calculate deviation from ECB's 2% target"""
        latest = self.latest_value
        if latest is None:
            return None
        return latest - 2.0

class InterestRateData(ECBSeriesData):
    """Interest rate specific data"""
    pass

class ECBAPIResponse(BaseModel):
    """Raw response from ECB API"""
    dataSets: List[Dict[str, Any]] = Field(default_factory=list)
    structure: Dict[str, Any] = Field(default_factory=dict)
    
class DataFetchResult(BaseModel):
    """Result of data fetching operation"""
    success: bool
    series_key: str
    data: Optional[ECBSeriesData] = None
    error_message: Optional[str] = None
    fetch_timestamp: datetime = Field(default_factory=datetime.now)
    observations_count: int = 0
    
class RefreshResult(BaseModel):
    """Result of data refresh operation"""
    total_series: int
    successful: int
    failed: int
    results: List[DataFetchResult] = Field(default_factory=list)
    start_time: datetime
    end_time: datetime
    
    @property
    def duration_seconds(self) -> float:
        """Calculate operation duration in seconds"""
        return (self.end_time - self.start_time).total_seconds()

class ChartData(BaseModel):
    """Data structure for chart rendering"""
    title: str
    x_values: List[str] = Field(default_factory=list)
    y_values: List[float] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class DashboardData(BaseModel):
    """Complete dashboard data"""
    exchange_rates: Optional[ExchangeRateData] = None
    inflation: Optional[InflationData] = None
    interest_rates: Optional[InterestRateData] = None
    last_refresh: Optional[datetime] = None
    
    @property
    def has_data(self) -> bool:
        """Check if any data is available"""
        return any([
            self.exchange_rates and self.exchange_rates.observations,
            self.inflation and self.inflation.observations,
            self.interest_rates and self.interest_rates.observations
        ])
