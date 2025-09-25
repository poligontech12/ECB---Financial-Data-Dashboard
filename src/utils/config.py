"""
Configuration management for ECB Financial Data Visualizer
"""
import os
from pathlib import Path
from typing import Dict, Any

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
DATABASE_PATH = DATA_DIR / "database.db"

# ECB API Configuration
ECB_API_CONFIG = {
    "base_url": "https://data-api.ecb.europa.eu/service",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1,  # seconds
    "rate_limit_per_minute": 10,
    "use_local_data": True,  # Switch to use local raw-data files instead of API
    "local_data_dir": "data/raw-data"  # Directory containing downloaded XML files
}

# ECB SDMX REST API Configuration (simplified ECB format)
ECB_SERIES_CONFIG = {
    "EUR_USD_DAILY": {
        "resource": "EXR",  # Exchange Rates dataflow
        "key": "D.USD.EUR.SP00.A"  # Daily.USD.EUR.Spot.Average
    },
    "EUR_USD_MONTHLY": {
        "resource": "EXR",
        "key": "M.USD.EUR.SP00.A"  # Monthly.USD.EUR.Spot.Average
    },
    "INFLATION_MONTHLY": {
        "resource": "ICP",  # Index of Consumer Prices
        "key": "M.U2.N.000000.4.ANR"  # Monthly.Euro area.Index.Overall HICP.Annual rate
    },
    "ECB_MAIN_RATE": {
        "resource": "FM",  # Financial Markets
        "key": "D.U2.EUR.4F.KR.DFR.LEV"  # Daily ECB deposit facility rate (original working configuration)
    },
    "EUR_GBP_DAILY": {
        "resource": "EXR",  # Exchange Rates dataflow
        "key": "D.GBP.EUR.SP00.A"  # Daily.GBP.EUR.Spot.Average
    },
    # Test configurations
    "EUR_USD_TEST1": {
        "resource": "EXR",
        "key": "D.USD.EUR.SP00.A"  # Standard daily EUR/USD rate
    },
    "EUR_USD_TEST2": {
        "resource": "EXR",
        "key": "M.USD.EUR.SP00.A"  # Monthly EUR/USD rate
    },
    "EUR_USD_TEST3": {
        "resource": "EXR",
        "key": "D..EUR.SP00.A"  # All currencies against EUR (wildcard)
    },
    "EUR_USD_TEST4": {
        "resource": "EXR",
        "key": ""  # Empty key to browse all EXR series
    }
}

# Streamlit Configuration
STREAMLIT_CONFIG = {
    "page_title": "ECB Financial Data Visualizer",
    "page_icon": "📈",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Chart Configuration
CHART_CONFIG = {
    "responsive": True,
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "scrollZoom": False,
    "doubleClick": "reset+autosize"
}

# Range Selector Buttons for Financial Data
RANGE_SELECTOR_BUTTONS = [
    {"count": 7, "label": "7D", "step": "day", "stepmode": "backward"},
    {"count": 30, "label": "30D", "step": "day", "stepmode": "backward"},
    {"count": 3, "label": "3M", "step": "month", "stepmode": "backward"},
    {"count": 6, "label": "6M", "step": "month", "stepmode": "backward"},
    {"count": 1, "label": "1Y", "step": "year", "stepmode": "backward"},
    {"step": "all", "label": "All"}
]

# Database Configuration
DATABASE_CONFIG = {
    "sqlite_url": f"sqlite:///{DATABASE_PATH}",
    "echo": False,  # Set to True for SQL debugging
    "pool_pre_ping": True
}

# Security Configuration
SECURITY_CONFIG = {
    "pin_hash": "$2b$12$yoH9SuJWxxfnV8oLpWj/tueHNOvbqqvpetJrZS99JRbu2rrO28cee",  # bcrypt hash for PIN "112233"
    "session_timeout_minutes": 30,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 15,
    "database_encryption_enabled": True,
    "session_secret_key": "ecb-financial-visualizer-security-key-change-in-production"
}

def ensure_directories():
    """Ensure all required directories exist"""
    DATA_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)

def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary"""
    ensure_directories()
    return {
        "paths": {
            "project_root": PROJECT_ROOT,
            "data_dir": DATA_DIR,
            "cache_dir": CACHE_DIR,
            "database_path": DATABASE_PATH
        },
        "ecb_api": ECB_API_CONFIG,
        "series_config": ECB_SERIES_CONFIG,
        "streamlit": STREAMLIT_CONFIG,
        "chart": CHART_CONFIG,
        "range_selector": RANGE_SELECTOR_BUTTONS,
        "database": DATABASE_CONFIG,
        "security": SECURITY_CONFIG
    }
