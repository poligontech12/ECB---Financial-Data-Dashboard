"""
ECB API client for fetching financial data
"""
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

from utils.config import get_config
from utils.logging_config import get_logger
from utils.helpers import format_date_for_api, parse_ecb_date, get_default_date_range
from api.data_models import (
    ECBAPIResponse, ECBSeriesData, ECBObservation, SeriesMetadata, 
    ExchangeRateData, InflationData, InterestRateData, DataFetchResult,
    SeriesFrequency, ObservationStatus
)

logger = get_logger(__name__)

class ECBAPIException(Exception):
    """ECB API related exceptions"""
    pass

class RateLimitException(ECBAPIException):
    """Rate limiting exception"""
    pass

class SeriesNotFoundException(ECBAPIException):
    """Series not found exception"""
    pass

class DataParsingException(ECBAPIException):
    """Data parsing exception"""
    pass

class ECBClient:
    """Client for ECB SDMX API"""
    
    def __init__(self):
        self.config = get_config()
        self.api_config = self.config["ecb_api"]
        self.series_config = self.config["series_config"]
        self.base_url = self.api_config["base_url"]
        self.session = requests.Session()
        self.last_request_time = 0
        
        # Configure session
        self.session.headers.update({
            "User-Agent": "ECB-Financial-Visualizer/1.0",
            "Accept": "application/json"
        })
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 60 / self.api_config["rate_limit_per_minute"]
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, series_config: dict, start_date: str = None, end_date: str = None, 
                     max_observations: int = None) -> Dict[str, Any]:
        """Make request to ECB API with SDMX REST format"""
        
        # Apply rate limiting
        self._rate_limit()
        
        # Build ECB SDMX REST URL: /data/{FLOW_ID}/{key} (not the complex SDMX format)
        # According to ECB documentation: https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A
        url_path = f"data/{series_config['resource']}/{series_config['key']}"
        url = f"{self.base_url}/{url_path}"
        
        # Build parameters - use ECB standard format
        params = {}
        
        if start_date and end_date:
            params["startPeriod"] = start_date
            params["endPeriod"] = end_date
        elif start_date:
            params["startPeriod"] = start_date
        elif end_date:
            params["endPeriod"] = end_date
            
        if max_observations:
            params["lastNObservations"] = max_observations
        
        # Retry logic
        for attempt in range(self.api_config["max_retries"]):
            try:
                logger.info(f"Making API request: {url} with params: {params}")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.api_config["timeout"]
                )
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Log the actual 404 response content to understand what's available
                    try:
                        error_content = response.json()
                        logger.error(f"404 Response content: {error_content}")
                    except:
                        logger.error(f"404 Response text: {response.text[:200]}")
                    
                    series_id = f"{series_config['resource']}.{series_config['key']}"
                    logger.error(f"Series not found: {series_id}")
                    raise SeriesNotFoundException(f"Series not found: {series_id}")
                elif response.status_code == 429:
                    logger.error("Rate limit exceeded")
                    raise RateLimitException("Rate limit exceeded")
                else:
                    logger.error(f"API request failed with status {response.status_code}: {response.text[:500]}")
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt == self.api_config["max_retries"] - 1:
                    raise ECBAPIException("Request timeout after all retries")
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error (attempt {attempt + 1})")
                if attempt == self.api_config["max_retries"] - 1:
                    raise ECBAPIException("Connection error after all retries")
                    
            except Exception as e:
                if attempt == self.api_config["max_retries"] - 1:
                    raise ECBAPIException(f"API request failed: {str(e)}")
            
            # Wait before retry
            if attempt < self.api_config["max_retries"] - 1:
                sleep_time = self.api_config["retry_delay"] * (2 ** attempt)
                logger.debug(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        
        raise ECBAPIException("All retry attempts failed")
    
    def _parse_response(self, response_data: Dict[str, Any], series_key: str) -> ECBSeriesData:
        """Parse ECB API response to internal data structure"""
        try:
            # Create API response model
            api_response = ECBAPIResponse(**response_data)
            
            if not api_response.dataSets:
                raise DataParsingException("No datasets in response")
            
            dataset = api_response.dataSets[0]
            structure = api_response.structure
            
            # Extract metadata
            metadata = self._extract_metadata(structure, series_key)
            
            # Extract observations
            observations = self._extract_observations(dataset, structure)
            
            # Create appropriate data model based on series type
            if "EXR" in series_key:
                return ExchangeRateData(metadata=metadata, observations=observations)
            elif "ICP" in series_key:
                return InflationData(metadata=metadata, observations=observations)
            elif "FM" in series_key:
                return InterestRateData(metadata=metadata, observations=observations)
            else:
                return ECBSeriesData(metadata=metadata, observations=observations)
                
        except Exception as e:
            raise DataParsingException(f"Failed to parse response: {str(e)}")
    
    def _extract_metadata(self, structure: Dict[str, Any], series_key: str) -> SeriesMetadata:
        """Extract metadata from API response structure"""
        try:
            # Get title from structure
            title = "Unknown"
            if "attributes" in structure:
                for attr in structure["attributes"].get("series", []):
                    if attr.get("id") == "TITLE":
                        values = attr.get("values", [])
                        if values:
                            title = values[0].get("name", "Unknown")
                        break
            
            # Determine frequency from series key
            frequency = SeriesFrequency.DAILY
            if series_key.startswith("EXR.D"):
                frequency = SeriesFrequency.DAILY
            elif series_key.startswith("EXR.M") or "M." in series_key:
                frequency = SeriesFrequency.MONTHLY
            
            # Extract unit
            unit = None
            if "attributes" in structure:
                for attr in structure["attributes"].get("series", []):
                    if attr.get("id") == "UNIT":
                        values = attr.get("values", [])
                        if values:
                            unit = values[0].get("name")
                        break
            
            return SeriesMetadata(
                series_key=series_key,
                title=title,
                unit=unit,
                frequency=frequency,
                source_agency="ECB",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return SeriesMetadata(
                series_key=series_key,
                title=f"ECB Series {series_key}",
                frequency=SeriesFrequency.DAILY
            )
    
    def _extract_observations(self, dataset: Dict[str, Any], structure: Dict[str, Any]) -> List[ECBObservation]:
        """Extract observations from dataset"""
        observations = []
        
        try:
            series_data = dataset.get("series", {})
            if not series_data:
                return observations
            
            # Get the first (and usually only) series
            first_series_key = next(iter(series_data.keys()), None)
            if not first_series_key:
                return observations
            
            series = series_data[first_series_key]
            obs_data = series.get("observations", {})
            
            # Get time dimension
            time_dimension = None
            if "dimensions" in structure and "observation" in structure["dimensions"]:
                for dim in structure["dimensions"]["observation"]:
                    if dim.get("id") == "TIME_PERIOD":
                        time_dimension = dim
                        break
            
            if not time_dimension:
                logger.warning("No TIME_PERIOD dimension found")
                return observations
            
            # Extract time values
            time_values = time_dimension.get("values", [])
            
            # Process observations
            for obs_index, obs_value in obs_data.items():
                try:
                    index = int(obs_index)
                    if index < len(time_values):
                        period = time_values[index].get("id", "")
                        value = obs_value[0] if obs_value and len(obs_value) > 0 else None
                        
                        # Convert value to float if possible
                        if value is not None:
                            try:
                                value = float(value)
                            except (ValueError, TypeError):
                                value = None
                        
                        if period and value is not None:
                            observations.append(ECBObservation(
                                period=period,
                                value=value,
                                status=ObservationStatus.NORMAL
                            ))
                            
                except (ValueError, IndexError) as e:
                    logger.warning(f"Skipping malformed observation {obs_index}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to extract observations: {e}")
        
        return observations
    
    def fetch_exchange_rates(self, start_date: str = None, end_date: str = None) -> DataFetchResult:
        """Fetch EUR/USD exchange rates"""
        series_config = self.series_config["EUR_USD_DAILY"]
        
        if not start_date or not end_date:
            start_date, end_date = get_default_date_range()
        
        return self._fetch_series(series_config, start_date, end_date)
    
    def fetch_inflation_data(self, start_date: str = None, end_date: str = None) -> DataFetchResult:
        """Fetch inflation data"""
        series_config = self.series_config["INFLATION_MONTHLY"]
        
        if not start_date or not end_date:
            start_date, end_date = get_default_date_range()
        
        return self._fetch_series(series_config, start_date, end_date)
    
    def fetch_interest_rates(self, start_date: str = None, end_date: str = None) -> DataFetchResult:
        """Fetch interest rates"""
        series_config = self.series_config["ECB_MAIN_RATE"]
        
        if not start_date or not end_date:
            start_date, end_date = get_default_date_range()
        
        return self._fetch_series(series_config, start_date, end_date)
    
    def _fetch_series(self, series_config: dict, start_date: str, end_date: str) -> DataFetchResult:
        """Generic method to fetch any series"""
        try:
            series_id = f"{series_config['resource']}.{series_config['key']}"
            logger.info(f"Fetching series {series_id} from {start_date} to {end_date}")
            
            # Make API request
            response_data = self._make_request(series_config, start_date, end_date)
            
            # Parse response
            series_data = self._parse_response(response_data, series_id)
            
            logger.info(f"Successfully fetched {len(series_data.observations)} observations for {series_id}")
            
            return DataFetchResult(
                success=True,
                series_key=series_id,
                data=series_data,
                observations_count=len(series_data.observations)
            )
            
        except Exception as e:
            series_id = f"{series_config['resource']}.{series_config['key']}"
            logger.error(f"Failed to fetch series {series_id}: {e}")
            return DataFetchResult(
                success=False,
                series_key=series_id,
                error_message=str(e)
            )
    
    def browse_dataflows(self) -> bool:
        """Browse available dataflows to understand the structure"""
        try:
            # Try to get dataflow information using ECB format
            browse_url = f"{self.base_url}/dataflow/ECB"
            logger.debug(f"Browsing dataflows: {browse_url}")

            # The dataflow endpoint returns SDMX structure (XML). Use appropriate Accept header.
            response = self.session.get(
                browse_url,
                timeout=30,
                headers={
                    "Accept": "application/vnd.sdmx.structure+xml;version=2.1, application/xml"
                }
            )
            logger.debug(f"Dataflow browse status: {response.status_code}")

            if response.status_code == 200:
                logger.debug(f"Dataflow content length: {len(response.text)}")
                return True
            elif response.status_code == 406:
                # Not acceptable is expected if Accept header not supported; treat as non-fatal
                logger.debug("Dataflow endpoint responded 406 Not Acceptable (structure formats only)")
                # Consider browse non-critical
                return False
            else:
                logger.debug(f"Dataflow browse response (truncated): {response.text[:200]}")
                
            # Also try browsing just the EXR dataflow structure
            exr_url = f"{self.base_url}/data/EXR"
            logger.debug(f"Browsing EXR data structure: {exr_url}")
            response = self.session.get(exr_url, params={"detail": "serieskeysonly"}, timeout=30)
            logger.debug(f"EXR browse status: {response.status_code}")
            if response.status_code == 200:
                logger.debug(f"EXR series keys content length: {len(response.text)}")
                return True
                
        except Exception as e:
            logger.debug(f"Failed to browse dataflows (non-critical): {e}")
            
        return False
    
    def test_connection(self) -> bool:
        """Test API connectivity"""
        try:
            # First, try browsing dataflows
            logger.info("Browsing available dataflows...")
            self.browse_dataflows()
            
            # Attempt a basic API health check (optional; many deployments return 404)
            health_url = f"{self.base_url}/health"
            try:
                health_response = self.session.get(health_url, timeout=10)
                if health_response.status_code != 200:
                    logger.debug(f"Health endpoint status: {health_response.status_code} (expected 404 in most cases)")
            except Exception:
                logger.debug("Health endpoint not available; skipping")
            
            # Try to browse available series with wildcard
            logger.info("Trying to browse available exchange rate series...")
            try:
                test_config = self.series_config["EUR_USD_TEST1"]
                browse_result = self._make_request(test_config, max_observations=1)
                logger.info(f"Browse result available: {bool(browse_result)}")
                if browse_result:
                    return True
            except Exception as e:
                logger.info(f"Browse failed: {e}")
            
            # Try to fetch data with minimal parameters using SDMX REST format
            eur_usd_config = self.series_config["EUR_USD_DAILY"]
            result = self._make_request(
                eur_usd_config, 
                max_observations=1
            )
            return bool(result)
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            # Try with a simpler request - no parameters
            try:
                logger.info("Trying simple request without parameters...")
                eur_usd_config = self.series_config["EUR_USD_DAILY"]
                simple_result = self._make_request(eur_usd_config)
                return bool(simple_result)
            except Exception as e2:
                logger.error(f"Simple API connection test also failed: {e2}")
                return False
