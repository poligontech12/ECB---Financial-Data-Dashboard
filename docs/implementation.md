# ECB Financial Data Visualizer - Implementation Plan

<!-- generated: 2025-08-29T00:00:00Z · agent: Architecture & Delivery Planner -->

## ASSUMPTIONS

| ID | Assumption | Rationale | Risk if Wrong | Owner |
|----|------------|-----------|---------------|-------|
| A1 | Flask is optimal for Python web development | Best balance of flexibility, production readiness, and professional presentation | May need framework change if rapid prototyping needed | Dev Team |
| A2 | Plotly for charting library | Excellent interactive charts, financial time series features, professional styling | Performance issues with large datasets | Dev Team |
| A3 | Local SQLite for data persistence | Simplicity for local app, structured storage | May need migration if scaling required | Dev Team |
| A4 | Daily data refresh is sufficient | Most ECB data updated daily | May miss intraday changes for some indicators | Product Owner |
| A5 | SDMX JSON format from ECB API | API supports jsondata format via ?format=jsondata parameter | XML fallback available, but JSON preferred | Dev Team |
| A6 | Specific ECB series keys are stable | EXR, ICP, FM dataflows provide required financial indicators | Series may be deprecated or restructured | Dev Team |

## TRADE-OFFS

**Decision**: Flask + HTML/CSS/JS over FastAPI + React/Streamlit + Plotly
- **Alternatives considered**: FastAPI+React, Streamlit+Plotly, Dash
- **Consequences**: 
  - **Operational**: Production-ready deployment, full control over UI
  - **Cost**: Moderate development time, better long-term maintainability
  - **Complexity**: Complete frontend flexibility, professional presentation

**Decision**: SQLite over PostgreSQL/MySQL
- **Alternatives considered**: PostgreSQL, MySQL, File-based JSON
- **Consequences**:
  - **Operational**: No database server setup required
  - **Cost**: Zero infrastructure cost
  - **Complexity**: Simple backup/restore, limited concurrent access

## 1. Module Overview

```
ecb-financial-visualizer/
├── docs/
│   └── implementation.md
├── src/
│   ├── __init__.py
│   ├── main.py                    # Flask app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ecb_client.py          # ECB API client
│   │   └── data_models.py         # Pydantic data models
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── database.py            # Database connection/session
│   │   └── migrations/            # Database migrations
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_service.py        # Data fetching/storage logic
│   │   └── chart_service.py       # Chart generation logic
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   ├── charts.py          # Chart components
│   │   │   ├── data_display.py    # Data tables/cards
│   │   │   └── controls.py        # UI controls/filters
│   │   └── pages/
│   │       ├── __init__.py
│   │       ├── dashboard.py       # Main dashboard
│   │       ├── exchange_rates.py  # EUR/USD exchange rates
│   │       ├── inflation.py       # Inflation data
│   │       └── interest_rates.py  # Interest rates
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       ├── logging_config.py      # Logging setup
│       └── helpers.py             # Utility functions
├── data/
│   ├── cache/                     # Local JSON cache
│   └── database.db               # SQLite database
├── tests/
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   └── test_ui/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 2. Technology Stack Proposal

### Backend & Framework
- **Python**: 3.11+ (latest stable)
- **Flask**: 2.3+ (web framework for production-ready applications)
- **SQLAlchemy**: 2.0+ (ORM for database operations)
- **Pydantic**: 2.4+ (data validation and serialization)

### Data & Visualization
- **Plotly**: 5.17+ (interactive charting library with financial time series features)
- **Pandas**: 2.1+ (data manipulation and analysis)
- **Requests**: 2.31+ (HTTP client for ECB API)
- **Numpy**: 1.24+ (numerical computations for chart data processing)

### Database & Storage
- **SQLite**: 3.x (embedded database for local storage)
- **JSON**: Native Python support for API cache

### Styling & UI
- **Bootstrap**: 5.x CSS framework for responsive design
- **Custom CSS**: Professional ECB theming and financial dashboard styling
- **JavaScript/AJAX**: Dynamic chart updates and interactive controls
- **Plotly.js**: Client-side rendering for interactive financial charts
- **Financial UI Patterns**: Range selectors, zoom controls, multi-timeframe views

### Development & Testing
- **pytest**: 7.4+ (testing framework)
- **black**: 23.9+ (code formatting)
- **mypy**: 1.6+ (type checking)

## 3. System Flows

### 3.1 Startup Flow

```
[App Start] → [Load Config] → [Initialize DB] → [Setup Logging] → [Launch UI]
     |             |              |               |              |
     v             v              v               v              v
Check .env    Load settings   Create tables   Setup handlers   Render dashboard
     |             |              |               |              |
     v             v              v               v              v
[Ready State: App accessible on localhost:5000 with Flask development server]
```

**Ready State**: Application responds on http://localhost:8501 with dashboard loaded

**Sad Paths**:
- Config missing → Use defaults, log warning
- DB creation fails → Exit with error message
- Port occupied → Try alternative ports (8502, 8503)

### 3.2 Data Fetch Flow

```
[User clicks Fetch] → [Validate Request] → [Call ECB API] → [Process Data] → [Store Data] → [Update UI]
         |                    |               |              |            |             |
         v                    v               v              v            v             v
    Check params        Validate series     HTTP request   Parse SDMX   Save to DB   Refresh charts
         |                    |               |              |            |             |
         v                    v               v              v            v             v
    [Rate Limiting] → [Retry Logic] → [Cache Response] → [Data Validation] → [Success Notification]
```

**API Request Format**:
```
GET https://data-api.ecb.europa.eu/service/data/{dataflow}/{key}?format=jsondata&startPeriod={start}&endPeriod={end}

Example:
GET https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=jsondata&startPeriod=2024-01-01&endPeriod=2024-08-29
```

**SDMX JSON Response Structure**:
```json
{
  "dataSets": [{
    "series": {
      "0:0:0:0:0": {
        "observations": {
          "0": [1.0856], "1": [1.0823], "2": [1.0798]
        }
      }
    }
  }],
  "structure": {
    "dimensions": {
      "series": [
        {"id": "FREQ", "name": "Frequency"},
        {"id": "CURRENCY", "name": "Currency"},
        {"id": "CURRENCY_DENOM", "name": "Currency denominator"}
      ],
      "observation": [{"id": "TIME_PERIOD", "name": "Time period"}]
    }
  }
}
```

**Ready State**: New data visible in charts, success message displayed, last updated timestamp shown

**Sad Paths**:
- API unavailable → Show cached data, display warning banner
- Invalid response → Log error, show user-friendly message with retry option
- Rate limit exceeded → Implement exponential backoff, show countdown timer
- Network timeout → Fallback to cached data, schedule retry

**Retries**: 3 attempts with exponential backoff (1s, 2s, 4s)
**Rate Limiting**: Max 10 requests per minute per data series (ECB recommended limit)

### 3.3 Chart Update Flow

```
[Data Change] → [Detect Change] → [Prepare Chart Data] → [Update Plotly] → [Render]
      |              |                   |                  |            |
      v              v                   v                  v            v
  DB trigger    Compare hashes      Transform data      Update figure   Display
      |              |                   |                  |            |
      v              v                   v                  v            v
[Ready State: Charts display latest data with smooth transitions]
```

**Ready State**: Charts updated with latest data, animations complete, interactive features working

## 4. Module Specifications

### 4.1 ECB API Client (`api/ecb_client.py`)

**Purpose**: Handle all communication with ECB's SDMX RESTful API

**Responsibilities**:
- Construct proper ECB API URLs with correct series keys
- Handle JSON response parsing from SDMX format
- Manage request retries and error handling
- Implement rate limiting and caching strategies

**Key Methods**:
```python
class ECBClient:
    def fetch_exchange_rates(self, start_date: str, end_date: str) -> ExchangeRateData
    def fetch_inflation_data(self, start_date: str, end_date: str) -> InflationData  
    def fetch_interest_rates(self, start_date: str, end_date: str) -> InterestRateData
    def get_available_series(self) -> List[DataSeries]
    def _make_request(self, series_key: str, params: Dict[str, str]) -> Dict[str, Any]
```

**ECB API Endpoints & Series Keys**:
```python
# Base URL
API_BASE_URL = "https://data-api.ecb.europa.eu/service"

# Series Keys (verified from ECB documentation)
SERIES_KEYS = {
    "EUR_USD_DAILY": "EXR.D.USD.EUR.SP00.A",           # Daily EUR/USD exchange rate
    "EUR_USD_MONTHLY": "EXR.M.USD.EUR.SP00.A",         # Monthly EUR/USD exchange rate  
    "INFLATION_MONTHLY": "ICP.M.U2.N.000000.4.ANR",    # HICP inflation rate (annual)
    "ECB_MAIN_RATE": "FM.D.U2.EUR.4F.KR.DFR.LEV",      # ECB main refinancing rate
    "ECB_DEPOSIT_RATE": "FM.D.U2.EUR.4F.KR.DEPOSIT.LEV" # ECB deposit facility rate
}

# Request format
# https://data-api.ecb.europa.eu/service/data/{dataflow}/{key}?format=jsondata&startPeriod={start}&endPeriod={end}
```

**Data Structures**:
```python
@dataclass
class ECBResponse:
    series_key: str
    observations: List[Observation]
    metadata: Dict[str, Any]
    last_updated: datetime
    frequency: str

@dataclass  
class Observation:
    period: str
    value: float
    status: Optional[str]
    
@dataclass
class SeriesMetadata:
    title: str
    unit: str
    frequency: str
    source_agency: str
```

**Error Handling**: 
- HTTP errors → `ECBAPIException`
- Rate limits → `RateLimitException` 
- Invalid series → `SeriesNotFoundException`
- SDMX parsing errors → `DataParsingException`

### 4.2 Data Service (`services/data_service.py`)

**Purpose**: Orchestrate data fetching, caching, and storage operations

**Responsibilities**:
- Coordinate API calls and database operations
- Implement caching strategies
- Handle data validation and transformation
- Manage update schedules

**Key Methods**:
```python
class DataService:
    def refresh_all_data(self) -> RefreshResult
    def get_cached_data(self, series: str, date_range: DateRange) -> Optional[SeriesData]
    def update_series(self, series: str, force: bool = False) -> UpdateResult
```

### 4.3 Chart Service (`services/chart_service.py`)

**Purpose**: Generate interactive financial charts using Plotly with time series best practices

**Responsibilities**:
- Create professional time series charts for financial data
- Apply consistent styling with Streamlit theme integration
- Handle chart interactivity, range selectors, and zoom functionality
- Generate comparative visualizations and multi-series charts

**Key Methods**:
```python
class ChartService:
    def create_exchange_rate_chart(self, data: ExchangeRateData) -> plotly.Figure
    def create_inflation_chart(self, data: InflationData) -> plotly.Figure
    def create_interest_rate_chart(self, data: InterestRateData) -> plotly.Figure
    def create_comparison_chart(self, datasets: List[SeriesData]) -> plotly.Figure
    def create_dashboard_overview(self, all_data: DashboardData) -> plotly.Figure
```

**Chart Design Patterns**:
```python
# Time Series Configuration Template
CHART_CONFIG = {
    "responsive": True,
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "scrollZoom": False,  # Prevent conflicts with page scrolling
    "doubleClick": "reset+autosize"
}

# Range Selector Buttons for Financial Data
RANGE_SELECTOR = {
    "buttons": [
        {"count": 7, "label": "7D", "step": "day", "stepmode": "backward"},
        {"count": 30, "label": "30D", "step": "day", "stepmode": "backward"},
        {"count": 3, "label": "3M", "step": "month", "stepmode": "backward"},
        {"count": 6, "label": "6M", "step": "month", "stepmode": "backward"},
        {"count": 1, "label": "1Y", "step": "year", "stepmode": "backward"},
        {"step": "all", "label": "All"}
    ]
}

# Time Series Styling
FINANCIAL_CHART_LAYOUT = {
    "hovermode": "x unified",
    "showlegend": True,
    "xaxis": {
        "rangeslider": {"visible": True},
        "rangeselector": RANGE_SELECTOR,
        "type": "date",
        "tickformat": "%b %Y",
        "tickformatstops": [
            {"dtickrange": [None, 86400000], "value": "%H:%M\n%b %d"},
            {"dtickrange": [86400000, "M1"], "value": "%b %d"},
            {"dtickrange": ["M1", "M12"], "value": "%b %Y"},
            {"dtickrange": ["M12", None], "value": "%Y"}
        ]
    },
    "yaxis": {
        "fixedrange": False,
        "showgrid": True,
        "gridcolor": "rgba(128,128,128,0.2)"
    }
}
```

**Chart Types & Features**:
- **Exchange Rate Charts**: Line charts with trend indicators, percentage change annotations
- **Inflation Charts**: Line charts with target lines (2% ECB target), period-over-period comparisons
- **Interest Rate Charts**: Step charts for policy rates, multi-series for different rate types
- **Comparison Charts**: Multi-axis charts for different indicator scales
- **Range Breaks**: Hide weekends/holidays for daily financial data

### 4.4 Database Models (`database/models.py`)

**Purpose**: Define data structure for local storage

```python
class FinancialSeries(Base):
    __tablename__ = 'financial_series'
    
    id: int = Column(Integer, primary_key=True)
    series_key: str = Column(String, unique=True, nullable=False)
    name: str = Column(String, nullable=False)
    frequency: str = Column(String, nullable=False)
    last_updated: datetime = Column(DateTime, nullable=False)

class Observation(Base):
    __tablename__ = 'observations'
    
    id: int = Column(Integer, primary_key=True)
    series_id: int = Column(Integer, ForeignKey('financial_series.id'))
    period: str = Column(String, nullable=False)
    value: float = Column(Float, nullable=False)
    status: str = Column(String, nullable=True)
```

## 5. Naming Conventions

### Files & Modules
- Snake_case for Python files: `data_service.py`
- PascalCase for classes: `ECBClient`
- UPPERCASE for constants: `API_BASE_URL`

### Database
- Snake_case for tables: `financial_series`
- Snake_case for columns: `last_updated`
- Descriptive names: `observations` not `obs`

### API & Data
- ECB series keys: Use official ECB notation (e.g., `EXR.D.USD.EUR.SP00.A`)
- JSON cache files: `{series_key}_{date_range}.json`

## 6. Error Handling & Logging Strategy

### Error Taxonomy
```python
class ECBVisualizerException(Exception): pass
class ECBAPIException(ECBVisualizerException): pass  
class DataValidationException(ECBVisualizerException): pass
class DatabaseException(ECBVisualizerException): pass
```

### Logging Levels
- **DEBUG**: API request/response details, SQL queries
- **INFO**: User actions, data refresh completion, startup events
- **WARNING**: API rate limits, missing data, fallback to cache
- **ERROR**: API failures, database errors, validation failures
- **CRITICAL**: Application startup failures, unrecoverable errors

### Correlation IDs
- Generate UUID for each user session
- Include in all log messages for request tracing
- Format: `[session_id:operation_id] message`

## 7. Database Schema

### Tables

**financial_series**
```sql
CREATE TABLE financial_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    frequency VARCHAR(10) NOT NULL,
    last_updated DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**observations** 
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER NOT NULL,
    period VARCHAR(20) NOT NULL,
    value REAL NOT NULL,
    status VARCHAR(10),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (series_id) REFERENCES financial_series (id),
    UNIQUE(series_id, period)
);
```

**Indexes**:
```sql
CREATE INDEX idx_observations_series_period ON observations(series_id, period);
CREATE INDEX idx_observations_period ON observations(period);
CREATE INDEX idx_series_key ON financial_series(series_key);
```

### Migration Plan
- Phase 1: Initial schema creation
- Phase 2: Add performance indexes
- Phase 3: Add data validation constraints

## 8. Implementation Phases

| Phase | Goal | Key Tasks | Deliverables | Definition of Done |
|-------|------|-----------|--------------|-------------------|
| **P1 - Setup** | Project foundation | • Setup Python environment<br>• Create project structure<br>• Configure Streamlit<br>• Setup logging | • Working repo scaffold<br>• Basic Streamlit app<br>• Development environment | • App runs on localhost:8501<br>• Basic UI renders<br>• Logging configured |
| **P2 - Core API** | ECB data integration | • Implement ECB API client<br>• Create data models<br>• Build database layer<br>• Add basic error handling | • Functional API client<br>• Database schema<br>• Data persistence | • Can fetch EUR/USD rates<br>• Data persists in SQLite<br>• API errors handled gracefully |
| **P3 - Visualization** | Chart implementation | • Integrate Plotly charts<br>• Create chart components<br>• Implement data refresh UI<br>• Add styling | • Interactive charts<br>• Refresh functionality<br>• Styled interface | • Charts display historical data<br>• Fetch button works<br>• UI is visually appealing |
| **P4 - Enhancement** | Complete feature set | • Add inflation data<br>• Add interest rates<br>• Implement data comparison<br>• Add export functionality | • All 3 data types<br>• Comparison charts<br>• Data export | • All indicators available<br>• Charts can be compared<br>• Users can export data |

### Ready States & Success Criteria

**Phase 1 Ready State**:
- ✅ Flask app accessible at http://localhost:5000
- ✅ Basic dashboard layout renders without errors
- ✅ Logs written to console and file
- ✅ Database connection established

**Phase 2 Ready State**:
- ✅ EUR/USD exchange rate data fetched from ECB API
- ✅ Data stored in SQLite database
- ✅ API errors display user-friendly messages
- ✅ Can query historical data from database

**Phase 3 Ready State**:
- ✅ Interactive time series chart displays EUR/USD data
- ✅ Fetch button updates data and refreshes chart
- ✅ Chart includes zoom, pan, and hover functionality
- ✅ UI follows consistent styling theme

**Phase 4 Ready State**:
- ✅ Dashboard shows EUR/USD, inflation, and interest rates
- ✅ Users can select date ranges for all indicators
- ✅ Comparison charts overlay multiple data series
- ✅ Data can be exported as CSV/JSON
