#!/usr/bin/env python3
"""
ECB Data Download Script

This script downloads all ECB financial indicators configured in the application
and saves them as raw XML files in the data/raw-data directory.

This allows the application to work offline or when the ECB API is not accessible
(e.g., behind corporate firewalls/VPNs).

Usage:
    python scripts/download_ecb_data.py
    python scripts/download_ecb_data.py --indicators EUR_USD_DAILY,INFLATION_MONTHLY
    python scripts/download_ecb_data.py --date-range 2020-01-01,2025-12-31
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import time

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import ECB_SERIES_CONFIG, ECB_API_CONFIG

class ECBDataDownloader:
    """Downloads ECB financial data and saves it locally"""
    
    def __init__(self, output_dir: str = None):
        self.base_url = ECB_API_CONFIG["base_url"]
        self.timeout = ECB_API_CONFIG["timeout"]
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "data" / "raw-data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session with reasonable defaults
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ECB-Financial-Dashboard/1.0 (Data Download Script)',
            'Accept': 'application/vnd.sdmx.genericdata+xml;version=2.1, application/xml',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🌐 ECB API base URL: {self.base_url}")
    
    def build_api_url(self, series_config: Dict[str, str]) -> str:
        """Build the complete API URL for a series"""
        resource = series_config["resource"]
        key = series_config["key"]
        return f"{self.base_url}/data/{resource}/{key}"
    
    def download_series(self, series_name: str, series_config: Dict[str, str], 
                       start_date: Optional[str] = None, end_date: Optional[str] = None) -> bool:
        """Download a single series and save it locally"""
        
        print(f"\n📊 Downloading {series_name}...")
        print(f"   Resource: {series_config['resource']}")
        print(f"   Key: {series_config['key']}")
        
        try:
            # Build URL and parameters
            url = self.build_api_url(series_config)
            params = {}
            
            # Add date range if specified
            if start_date:
                params['startPeriod'] = start_date
            if end_date:
                params['endPeriod'] = end_date
            
            # Make the request
            print(f"   🔗 URL: {url}")
            if params:
                print(f"   📅 Parameters: {params}")
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            print(f"   📡 Status: {response.status_code} {response.reason}")
            print(f"   📏 Content Length: {len(response.content)} bytes")
            print(f"   📋 Content Type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                # Save the raw XML response
                filename = f"{series_name}.xml"
                filepath = self.output_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"   ✅ Saved to: {filepath}")
                
                # Save metadata
                metadata = {
                    'series_name': series_name,
                    'resource': series_config['resource'],
                    'key': series_config['key'],
                    'download_timestamp': datetime.now().isoformat(),
                    'api_url': url,
                    'parameters': params,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'content_type': response.headers.get('content-type'),
                    'response_headers': dict(response.headers)
                }
                
                metadata_file = self.output_dir / f"{series_name}_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                print(f"   📝 Metadata saved to: {metadata_file}")
                return True
                
            else:
                print(f"   ❌ Failed: {response.status_code} {response.reason}")
                if response.text:
                    print(f"   📄 Error response: {response.text[:200]}...")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False
    
    def download_all_series(self, indicators: Optional[List[str]] = None,
                          start_date: Optional[str] = None, end_date: Optional[str] = None) -> None:
        """Download all configured series or specified indicators"""
        
        # Filter indicators if specified
        if indicators:
            series_to_download = {k: v for k, v in ECB_SERIES_CONFIG.items() if k in indicators}
            if not series_to_download:
                print(f"❌ No matching indicators found for: {indicators}")
                return
        else:
            # Skip test configurations for full download
            series_to_download = {k: v for k, v in ECB_SERIES_CONFIG.items() 
                                if not k.startswith('EUR_USD_TEST')}
        
        print(f"🚀 Starting download of {len(series_to_download)} indicators...")
        print(f"📅 Date range: {start_date or 'default'} to {end_date or 'default'}")
        
        successful_downloads = 0
        failed_downloads = 0
        
        for series_name, series_config in series_to_download.items():
            success = self.download_series(series_name, series_config, start_date, end_date)
            
            if success:
                successful_downloads += 1
            else:
                failed_downloads += 1
            
            # Rate limiting - be nice to the ECB API
            time.sleep(1)
        
        print(f"\n📈 Download Summary:")
        print(f"   ✅ Successful: {successful_downloads}")
        print(f"   ❌ Failed: {failed_downloads}")
        print(f"   📁 Files saved in: {self.output_dir}")
        
        # Create a summary file
        summary = {
            'download_timestamp': datetime.now().isoformat(),
            'total_indicators': len(series_to_download),
            'successful_downloads': successful_downloads,
            'failed_downloads': failed_downloads,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'indicators': list(series_to_download.keys())
        }
        
        summary_file = self.output_dir / f"download_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   📋 Summary saved to: {summary_file}")

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Download ECB financial data for offline use",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all indicators with default date range
  python scripts/download_ecb_data.py
  
  # Download specific indicators
  python scripts/download_ecb_data.py --indicators EUR_USD_DAILY,INFLATION_MONTHLY
  
  # Download with custom date range
  python scripts/download_ecb_data.py --date-range 2020-01-01,2025-12-31
  
  # Download specific indicators with date range
  python scripts/download_ecb_data.py --indicators EUR_USD_DAILY --date-range 2024-01-01,2025-12-31
        """
    )
    
    parser.add_argument(
        '--indicators',
        help='Comma-separated list of indicators to download (default: all)',
        type=str
    )
    
    parser.add_argument(
        '--date-range',
        help='Date range in format: start_date,end_date (YYYY-MM-DD)',
        type=str
    )
    
    parser.add_argument(
        '--output-dir',
        help='Output directory for downloaded files',
        type=str,
        default=None
    )
    
    parser.add_argument(
        '--list-indicators',
        help='List all available indicators and exit',
        action='store_true'
    )
    
    args = parser.parse_args()
    
    # List indicators if requested
    if args.list_indicators:
        print("📊 Available ECB Financial Indicators:")
        print("=" * 50)
        for name, config in ECB_SERIES_CONFIG.items():
            print(f"  {name}")
            print(f"    Resource: {config['resource']}")
            print(f"    Key: {config['key']}")
            print()
        return
    
    # Parse indicators
    indicators = None
    if args.indicators:
        indicators = [i.strip() for i in args.indicators.split(',')]
        print(f"🎯 Selected indicators: {indicators}")
    
    # Parse date range
    start_date = None
    end_date = None
    if args.date_range:
        try:
            dates = args.date_range.split(',')
            if len(dates) != 2:
                raise ValueError("Date range must be in format: start_date,end_date")
            start_date = dates[0].strip()
            end_date = dates[1].strip()
            
            # Validate date format
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            
        except ValueError as e:
            print(f"❌ Invalid date range: {e}")
            print("   Expected format: YYYY-MM-DD,YYYY-MM-DD")
            return
    else:
        # Default to last 2 years
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        print(f"📅 Using default date range: {start_date} to {end_date}")
    
    # Create downloader and start download
    downloader = ECBDataDownloader(output_dir=args.output_dir)
    downloader.download_all_series(indicators=indicators, start_date=start_date, end_date=end_date)

if __name__ == "__main__":
    main()