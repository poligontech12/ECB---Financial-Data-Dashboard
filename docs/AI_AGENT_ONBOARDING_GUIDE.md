# ECB Financial Data Visualizer – AI Agent Onboarding Guide

## Mission Statement

You are tasked with **understanding, maintaining, and enhancing** the ECB Financial Data Visualizer - a professional Flask-based financial dashboard. Your goal is to become proficient enough to make informed modifications, debug issues, and extend functionality while preserving the sophisticated architecture.

## Primary Objectives & Deliverables

### **Immediate Goals (First Session)**
1. **Understand Core Architecture**: Analyze module structure, data flow, and dependencies.
2. **Document Key Modules**: Build a table of primary exports, their responsibilities, and usage.
3. **Trace Error Pathways**: Identify how errors are handled and propagated.
4. **Review Session/State Management**: Understand state flow and lifecycle.
5. **Modification Readiness Assessment**: Confirm understanding before making changes

## Architecture Overview - Critical Understanding

### Module & Directory Structure
```
ecb-financial-visualizer/
├── app.py                         # Flask application entry point (CRITICAL)
├── src/
│   ├── api/
│   │   ├── ecb_client.py          # ECB SDMX API client with rate limiting
│   │   └── data_models.py         # Pydantic data models for validation
│   ├── database/
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   └── database.py            # Database connection & session management
│   ├── services/
│   │   ├── data_service.py        # Business logic orchestration layer
│   │   └── chart_service.py       # Plotly chart generation with ECB styling
│   ├── ui/
│   │   ├── components/            # Reusable UI components
│   │   └── pages/                 # Page-specific layouts
│   └── utils/
│       ├── config.py              # Centralized configuration management
│       ├── logging_config.py      # Session-based logging with UUIDs
│       └── helpers.py             # Utility functions
├── templates/
│   ├── base.html                  # Bootstrap base template
│   ├── dashboard.html             # Main dashboard interface
│   └── error.html                 # Error handling template
├── static/
│   ├── css/ecb-theme.css          # ECB corporate styling
│   └── js/dashboard.js            # AJAX chart management
└── data/
    ├── database.db               # SQLite persistence
    └── cache/                    # JSON cache directory
```

**Key Layers:**
- **API Layer**: ECB SDMX integration with error handling and rate limiting
- **Database Layer**: SQLAlchemy models with intelligent caching
- **Service Layer**: Business logic for data fetching and chart generation
- **UI Layer**: Flask templates + Bootstrap + JavaScript for responsive dashboard
- **Utils**: Configuration, logging with session tracking, and helper utilities

### Design Patterns & Conventions
- **Service-Oriented Architecture**: Clean separation between API, business logic, and presentation
- **Dependency Inversion**: Services depend on abstractions, not concrete implementations
- **Repository Pattern**: Database operations abstracted through SQLAlchemy ORM
- **Factory Pattern**: Chart generation based on data types (ExchangeRateData, InflationData, etc.)
- **Configuration Centralization**: All settings in `src/utils/config.py` with typed constants
- **Error Layering**: Custom exceptions with graceful degradation at each layer

### Data Flow
```
[ECB API] → [ECBClient] → [DataService] → [Database] → [ChartService] → [Flask API] → [Frontend]
     ↓           ↓            ↓             ↓             ↓              ↓            ↓
Rate Limiting → Parsing → Validation → Persistence → Chart Gen → JSON API → AJAX Updates
```

**Configuration Flow**: `config.py` → All modules reference centralized settings
**Input Flow**: User actions → AJAX calls → Flask routes → Services → ECB API
**Output Flow**: ECB data → Database storage → Chart generation → JSON response → Plotly.js rendering

## **State & Session Lifecycle**

```python
# Application Initialization Flow
def initialize_services():
    # 1. Database initialization with auto-schema creation
    init_success = init_database()
    
    # 2. Service instantiation with dependency injection
    data_service = DataService()  # Contains ECBClient internally
    ecb_client = ECBClient()      # Rate-limited API client
    
    # 3. Session-based logging with unique UUID
    logger = get_logger(__name__)  # Includes SESSION_ID in all logs
```

### **Key Analysis Points**:
1. **State Loading**: Services initialized on first Flask request, cached globally for session
2. **State Persistence**: SQLite database with automatic initialization, JSON cache for performance
3. **Separation of Responsibilities**: 
   - `DataService` orchestrates data operations
   - `ChartService` handles visualization logic
   - `ECBClient` manages API communication
4. **Parameter Passing**: Pydantic models ensure type safety across all layer boundaries

## **Error Handling Strategy**

### Error Categories & Representative Codes:
```python
# API Layer Exceptions
class ECBAPIException(Exception): pass        # Base ECB API errors
class RateLimitException(ECBAPIException): pass   # 429 rate limiting
class SeriesNotFoundException(ECBAPIException): pass  # 404 series not found
class DataParsingException(ECBAPIException): pass     # SDMX parsing failures

# Service Layer Error Flow
try:
    result = ecb_client.fetch_exchange_rates()
    if result.success:
        data_service._store_series_data(result.data)
    else:
        logger.error(f"Fetch failed: {result.error_message}")
except ECBAPIException as e:
    return jsonify({'success': False, 'error': str(e)})
```

### Error Flow Across Layers:
1. **API Layer**: HTTP errors → Custom exceptions with retry logic
2. **Service Layer**: Business logic errors → Logged with session correlation
3. **Flask Layer**: API endpoint errors → JSON error responses with user-friendly messages
4. **Frontend Layer**: AJAX errors → Bootstrap alerts with recovery options

## **Common Pitfalls & Misconceptions**

- **DO NOT** bypass the `DataService` layer - always use service orchestration for data operations
- **DO NOT** hardcode ECB series keys - use configuration in `ECB_SERIES_CONFIG` 
- **DO NOT** return raw pandas/numpy in Flask JSON responses - convert to native Python types
- **DO NOT** skip rate limiting - ECB API will block excessive requests
- **DO NOT** modify database models without considering migration impact on existing data
- **DO NOT** assume simple REST API - this is a sophisticated SDMX 2.1 integration
- **DO NOT** overlook the critical chart data serialization fix for pandas/numpy types
- **DO NOT** ignore session-based logging - correlation IDs are essential for debugging

## **Documentation Context & Analysis Approach**

### **Recommended Document Set**:
- `README.md` – Project overview, features, and setup instructions
- `docs/implementation.md` – Detailed technical implementation and design decisions
- `.github/copilot-instructions.md` – Development patterns and critical implementation details
- `src/utils/config.py` – Configuration reference and ECB series definitions
- `app.py` – Flask application structure and API endpoint reference

### **Suggested Analysis Order**:
1. Start with `README.md` for high-level overview and current status
2. Review `.github/copilot-instructions.md` for critical development patterns
3. Examine `docs/implementation.md` for technical architecture decisions
4. Analyze `src/utils/config.py` for ECB series configuration and settings
5. Study `app.py` for Flask API endpoints and service initialization
6. Validate everything against actual code implementation

## **Specific Analysis Tasks**

### **Priority 1: Core Understanding**
1. **Read `app.py`** (lines 1-100) - Understand Flask route structure and service initialization
2. **Analyze `src/api/ecb_client.py`** - ECB SDMX API integration patterns and rate limiting
3. **Study `src/services/data_service.py`** - Data orchestration and caching strategies
4. **Examine `src/database/models.py`** - SQLAlchemy schema and relationships

### **Priority 2: Data Flow Analysis**
1. **Trace API endpoint**: `/api/exchange-rates` → `data_service.get_exchange_rate_data()` → Database
2. **Follow chart generation**: `ChartService.create_exchange_rate_chart()` → Plotly figure → JSON serialization
3. **Understand configuration flow**: `config.py` → Service initialization → ECB API calls
4. **Validate error handling**: API failures → Exception propagation → User-friendly messages

### **Priority 3: Frontend Integration**
1. **Review `templates/dashboard.html`** - Bootstrap layout and AJAX integration points
2. **Study `static/js/dashboard.js`** - Chart loading and refresh functionality
3. **Examine `static/css/ecb-theme.css`** - ECB corporate styling and responsive design
4. **Test critical user flows**: Data refresh → Chart updates → Error recovery

### **Priority 4: Critical Implementation Details**
1. **Chart serialization fix** in `app.py` `plotly_to_json()` function
2. **ECB series configuration** in `src/utils/config.py` `ECB_SERIES_CONFIG`
3. **Session-based logging** in `src/utils/logging_config.py` with UUID correlation
4. **Database auto-initialization** in `src/database/database.py`

## **Success Criteria & Validation**

✅ **Architecture Mastery**: Can explain the service-oriented architecture and layer responsibilities  
✅ **Data Flow Understanding**: Can trace data from ECB API → Database → Charts → Frontend  
✅ **Error Handling Comprehension**: Can describe error propagation and recovery mechanisms  
✅ **Configuration Knowledge**: Understands ECB series configuration and Flask API endpoints  
✅ **Frontend Integration**: Can explain AJAX patterns and chart update mechanisms  
✅ **Critical Fixes Awareness**: Knows about pandas/numpy JSON serialization requirements  
✅ **Production Readiness**: Understands logging, caching, and deployment considerations  

## **Final Instructions**

• **Treat as Production System**: This is enterprise-grade financial software with intentional design choices
• **Complete Analysis First**: Master all architecture components before making any modifications  
• **Validate Understanding**: Document findings and cross-check against actual code implementation
• **Respect Existing Patterns**: Understand the rationale behind current patterns before proposing changes
• **Test Critical Paths**: Always verify ECB API integration, chart generation, and error handling
• **Maintain Session Logging**: Preserve correlation IDs and debugging capabilities in all modifications
• **Follow ECB Compliance**: Respect rate limiting, series key formats, and SDMX standards

**Remember**: This project integrates real financial data from the European Central Bank. Accuracy, reliability, and professional presentation are paramount.