"""
Data service for orchestrating data fetching, caching, and storage
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from api.ecb_client import ECBClient
from api.data_models import (
    ECBSeriesData, ExchangeRateData, InflationData, InterestRateData,
    DataFetchResult, RefreshResult, DashboardData
)
from database.database import get_db_session
from database.models import FinancialSeries, Observation, DataFetchLog
from utils.logging_config import get_logger
from utils.helpers import get_default_date_range, save_json_cache, load_json_cache
from utils.config import get_config

logger = get_logger(__name__)

class DataService:
    """Service for managing financial data fetching and storage"""
    
    def __init__(self):
        self.config = get_config()
        self.ecb_client = ECBClient()
    
    def refresh_all_data(self, force: bool = False) -> RefreshResult:
        """Refresh all financial data series"""
        start_time = datetime.now()
        results = []
        
        # Define series to refresh
        series_to_fetch = [
            ("EUR_USD_DAILY", self.ecb_client.fetch_exchange_rates),
            ("INFLATION_MONTHLY", self.ecb_client.fetch_inflation_data),
            ("ECB_MAIN_RATE", self.ecb_client.fetch_interest_rates)
        ]
        
        for series_name, fetch_func in series_to_fetch:
            try:
                # Check if we need to refresh this series
                if not force and not self._should_refresh_series(series_name):
                    logger.info(f"Skipping {series_name} - recently updated")
                    continue
                
                # Fetch data
                result = fetch_func()
                results.append(result)
                
                # Store in database if successful
                if result.success and result.data:
                    self._store_series_data(result.data)
                    self._log_fetch_operation(result)
                
            except Exception as e:
                logger.error(f"Error refreshing {series_name}: {e}")
                results.append(DataFetchResult(
                    success=False,
                    series_key=series_name,
                    error_message=str(e)
                ))
        
        end_time = datetime.now()
        
        # Calculate summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        refresh_result = RefreshResult(
            total_series=len(results),
            successful=successful,
            failed=failed,
            results=results,
            start_time=start_time,
            end_time=end_time
        )
        
        logger.info(f"Data refresh completed: {successful}/{len(results)} successful")
        return refresh_result
    
    def _get_series_key(self, series_name: str) -> str:
        """Get series key from series configuration"""
        series_config = self.config["series_config"][series_name]
        return f"{series_config['resource']}.{series_config['key']}"
    
    def get_exchange_rate_data(self, days: int = 365) -> Optional[ExchangeRateData]:
        """Get EUR/USD exchange rate data from database"""
        try:
            series_key = self._get_series_key("EUR_USD_DAILY")
            with get_db_session() as session:
                series = session.query(FinancialSeries).filter(
                    FinancialSeries.series_key == series_key
                ).first()
                
                if not series:
                    return None
                
                # Get recent observations
                cutoff_date = datetime.now() - timedelta(days=days)
                observations = session.query(Observation).filter(
                    Observation.series_id == series.id,
                    Observation.created_at >= cutoff_date
                ).order_by(Observation.period).all()
                
                if not observations:
                    return None
                
                # Convert to data model
                return self._db_to_exchange_rate_data(series, observations)
                
        except Exception as e:
            logger.error(f"Error getting exchange rate data: {e}")
            return None
    
    def get_inflation_data(self, months: int = 12) -> Optional[InflationData]:
        """Get inflation data from database"""
        try:
            series_key = self._get_series_key("INFLATION_MONTHLY")
            with get_db_session() as session:
                series = session.query(FinancialSeries).filter(
                    FinancialSeries.series_key == series_key
                ).first()
                
                if not series:
                    return None
                
                # Get recent observations
                cutoff_date = datetime.now() - timedelta(days=months * 30)
                observations = session.query(Observation).filter(
                    Observation.series_id == series.id,
                    Observation.created_at >= cutoff_date
                ).order_by(Observation.period).all()
                
                if not observations:
                    return None
                
                # Convert to data model
                return self._db_to_inflation_data(series, observations)
                
        except Exception as e:
            logger.error(f"Error getting inflation data: {e}")
            return None
    
    def get_interest_rate_data(self, days: int = 365) -> Optional[InterestRateData]:
        """Get interest rate data from database"""
        try:
            series_key = self._get_series_key("ECB_MAIN_RATE")
            with get_db_session() as session:
                series = session.query(FinancialSeries).filter(
                    FinancialSeries.series_key == series_key
                ).first()
                
                if not series:
                    return None
                
                # Get recent observations
                cutoff_date = datetime.now() - timedelta(days=days)
                observations = session.query(Observation).filter(
                    Observation.series_id == series.id,
                    Observation.created_at >= cutoff_date
                ).order_by(Observation.period).all()
                
                if not observations:
                    return None
                
                # Convert to data model
                return self._db_to_interest_rate_data(series, observations)
                
        except Exception as e:
            logger.error(f"Error getting interest rate data: {e}")
            return None
    
    def get_dashboard_data(self) -> DashboardData:
        """Get complete dashboard data"""
        return DashboardData(
            exchange_rates=self.get_exchange_rate_data(),
            inflation=self.get_inflation_data(),
            interest_rates=self.get_interest_rate_data(),
            last_refresh=self._get_last_refresh_time()
        )
    
    def _should_refresh_series(self, series_key: str) -> bool:
        """Check if series should be refreshed based on last update time"""
        try:
            with get_db_session() as session:
                series = session.query(FinancialSeries).filter(
                    FinancialSeries.series_key == series_key
                ).first()
                
                if not series:
                    return True  # No data exists, should refresh
                
                # Check if last update was more than 1 hour ago
                time_threshold = datetime.now() - timedelta(hours=1)
                return series.last_updated < time_threshold
                
        except Exception as e:
            logger.warning(f"Error checking refresh status for {series_key}: {e}")
            return True
    
    def _store_series_data(self, series_data: ECBSeriesData):
        """Store series data in database"""
        try:
            with get_db_session() as session:
                # Get or create series
                series = session.query(FinancialSeries).filter(
                    FinancialSeries.series_key == series_data.metadata.series_key
                ).first()
                
                if not series:
                    series = FinancialSeries(
                        series_key=series_data.metadata.series_key,
                        name=series_data.metadata.title,
                        frequency=series_data.metadata.frequency.value,
                        unit=series_data.metadata.unit,
                        source_agency=series_data.metadata.source_agency
                    )
                    session.add(series)
                    session.flush()  # Get the ID
                else:
                    # Update metadata
                    series.name = series_data.metadata.title
                    series.unit = series_data.metadata.unit
                    series.last_updated = datetime.now()
                
                # Clear existing observations for the date range
                # (This is a simple approach - could be optimized)
                session.query(Observation).filter(
                    Observation.series_id == series.id
                ).delete()
                
                # Add new observations
                for obs in series_data.observations:
                    if obs.value is not None:
                        db_obs = Observation(
                            series_id=series.id,
                            period=obs.period,
                            value=obs.value,
                            status=obs.status.value if obs.status else None
                        )
                        session.add(db_obs)
                
                session.commit()
                logger.info(f"Stored {len(series_data.observations)} observations for {series_data.metadata.series_key}")
                
        except Exception as e:
            logger.error(f"Error storing series data: {e}")
            raise
    
    def _log_fetch_operation(self, result: DataFetchResult):
        """Log fetch operation to database"""
        try:
            with get_db_session() as session:
                log_entry = DataFetchLog(
                    series_key=result.series_key,
                    fetch_timestamp=result.fetch_timestamp,
                    success="success" if result.success else "error",
                    observations_count=result.observations_count,
                    error_message=result.error_message
                )
                session.add(log_entry)
                session.commit()
                
        except Exception as e:
            logger.warning(f"Failed to log fetch operation: {e}")
    
    def _get_last_refresh_time(self) -> Optional[datetime]:
        """Get the timestamp of the last successful data refresh"""
        try:
            with get_db_session() as session:
                last_log = session.query(DataFetchLog).filter(
                    DataFetchLog.success == "success"
                ).order_by(desc(DataFetchLog.fetch_timestamp)).first()
                
                return last_log.fetch_timestamp if last_log else None
                
        except Exception as e:
            logger.warning(f"Error getting last refresh time: {e}")
            return None
    
    def _db_to_exchange_rate_data(self, series: FinancialSeries, observations: List[Observation]) -> ExchangeRateData:
        """Convert database objects to ExchangeRateData"""
        from api.data_models import SeriesMetadata, ECBObservation, SeriesFrequency, ObservationStatus
        
        metadata = SeriesMetadata(
            series_key=series.series_key,
            title=series.name,
            unit=series.unit,
            frequency=SeriesFrequency(series.frequency),
            source_agency=series.source_agency,
            last_updated=series.last_updated
        )
        
        obs_list = [
            ECBObservation(
                period=obs.period,
                value=obs.value,
                status=ObservationStatus(obs.status) if obs.status else ObservationStatus.NORMAL
            )
            for obs in observations
        ]
        
        return ExchangeRateData(metadata=metadata, observations=obs_list)
    
    def _db_to_inflation_data(self, series: FinancialSeries, observations: List[Observation]) -> InflationData:
        """Convert database objects to InflationData"""
        from api.data_models import SeriesMetadata, ECBObservation, SeriesFrequency, ObservationStatus
        
        metadata = SeriesMetadata(
            series_key=series.series_key,
            title=series.name,
            unit=series.unit,
            frequency=SeriesFrequency(series.frequency),
            source_agency=series.source_agency,
            last_updated=series.last_updated
        )
        
        obs_list = [
            ECBObservation(
                period=obs.period,
                value=obs.value,
                status=ObservationStatus(obs.status) if obs.status else ObservationStatus.NORMAL
            )
            for obs in observations
        ]
        
        return InflationData(metadata=metadata, observations=obs_list)
    
    def _db_to_interest_rate_data(self, series: FinancialSeries, observations: List[Observation]) -> InterestRateData:
        """Convert database objects to InterestRateData"""
        from api.data_models import SeriesMetadata, ECBObservation, SeriesFrequency, ObservationStatus
        
        metadata = SeriesMetadata(
            series_key=series.series_key,
            title=series.name,
            unit=series.unit,
            frequency=SeriesFrequency(series.frequency),
            source_agency=series.source_agency,
            last_updated=series.last_updated
        )
        
        obs_list = [
            ECBObservation(
                period=obs.period,
                value=obs.value,
                status=ObservationStatus(obs.status) if obs.status else ObservationStatus.NORMAL
            )
            for obs in observations
        ]
        
        return InterestRateData(metadata=metadata, observations=obs_list)
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        try:
            with get_db_session() as session:
                # Count series
                series_count = session.query(FinancialSeries).count()
                
                # Count observations
                obs_count = session.query(Observation).count()
                
                # Get latest updates
                latest_series = session.query(FinancialSeries).order_by(
                    desc(FinancialSeries.last_updated)
                ).limit(5).all()
                
                return {
                    "series_count": series_count,
                    "total_observations": obs_count,
                    "latest_updates": [
                        {
                            "series_key": s.series_key,
                            "name": s.name,
                            "last_updated": s.last_updated.isoformat()
                        }
                        for s in latest_series
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting data statistics: {e}")
            return {"error": str(e)}
