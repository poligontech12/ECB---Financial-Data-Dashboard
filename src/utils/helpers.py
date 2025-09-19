"""
Utility helper functions
"""
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from pathlib import Path

def format_currency(value: float, currency: str = "EUR") -> str:
    """Format currency value for display"""
    if currency == "EUR":
        return f"€{value:.4f}"
    elif currency == "USD":
        return f"${value:.4f}"
    else:
        return f"{value:.4f} {currency}"

def format_percentage(value: float, decimal_places: int = 2) -> str:
    """Format percentage value for display"""
    return f"{value:.{decimal_places}f}%"

def format_date_for_api(date: datetime) -> str:
    """Format date for ECB API (YYYY-MM-DD)"""
    return date.strftime("%Y-%m-%d")

def parse_ecb_date(date_str: str) -> datetime:
    """Parse ECB date string to datetime object"""
    try:
        # Try different ECB date formats
        for fmt in ["%Y-%m-%d", "%Y-%m", "%Y"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unable to parse date: {date_str}")
    except Exception as e:
        raise ValueError(f"Invalid date format: {date_str}") from e

def get_default_date_range() -> tuple[str, str]:
    """Get default date range for data queries (last 12 months)"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 12 months
    
    return (
        format_date_for_api(start_date),
        format_date_for_api(end_date)
    )

def save_json_cache(data: Dict[str, Any], filename: str, cache_dir: Path) -> bool:
    """Save data to JSON cache file"""
    try:
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"{filename}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return True
    except Exception:
        return False

def load_json_cache(filename: str, cache_dir: Path) -> Optional[Dict[str, Any]]:
    """Load data from JSON cache file"""
    try:
        cache_file = cache_dir / f"{filename}.json"
        
        if not cache_file.exists():
            return None
            
        with open(cache_file, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100

def validate_date_range(start_date: str, end_date: str) -> bool:
    """Validate that date range is logical"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return start <= end
    except ValueError:
        return False
