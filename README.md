# ECB Financial Data Visualizer

A modern, secure web application for visualizing European Central Bank financial data including exchange rates, inflation, and interest rates. Built with Flask and featuring interactive Plotly charts with professional ECB theming and PIN-based authentication.

## 🎓 Workshop Version

This is the **secure workshop edition** featuring:
- 🔏 **PIN Authentication** (PIN: `112233`)
- 🛡️ **Database Encryption** 
- 📊 **Interactive Financial Charts**
- 🏦 **Professional ECB Styling**

**For workshop participants:** See [WORKSHOP_SETUP.md](WORKSHOP_SETUP.md) for detailed setup instructions.

## 🚀 Quick Start

### Prerequisites
- **Python 3.13.7** - installed on your system (https://www.python.org/downloads)
- **Visual Studio Code** - (https://code.visualstudio.com/)
- **Git** - (for repository cloning) 
- **Github Copilot Pro** - The Pro version is required in order to use GPT5 and Claude Sonnet 4 models.     

### Installation

1. **Clone or download** this repository
2. **Navigate** to the project directory:
   ```bash
   cd "ECB - Financial Data Visualizer"
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the dashboard**:
   - Open browser to `http://localhost:5000`
   - Enter PIN: `112233`
   - Explore financial data visualizations!

### Running the Application

Start the Flask application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 📊 Features

### Completed
- ✅ **Phase 1**: Foundation
  - Project structure and configuration
  - Logging system with unique session tracking
  - Development environment setup
  - SQLite database with automated initialization

- ✅ **Phase 2**: ECB API Integration
  - SDMX 2.1 compliant API client
  - EUR/USD exchange rate data fetching
  - Inflation (HICP) data integration
  - ECB interest rate data (Deposit Facility Rate)
  - SQLite database storage with intelligent caching
  - 12-month historical data optimization
  - Error handling and recovery mechanisms

- ✅ **Phase 3**: Interactive Visualizations
  - Interactive Plotly charts for all data types
  - Professional ECB-themed styling and branding
  - Range selectors (1M, 3M, 6M, 1Y, All)
  - Zoom, pan, and hover functionality
  - ECB target lines for inflation analysis
  - Step charts for policy rate visualization
  - Real-time data refresh capabilities

### Architecture Highlights
- **RESTful API Design**: Clean separation between backend data services and frontend presentation
- **Professional UI/UX**: Bootstrap-based responsive dashboard with ECB corporate styling
- **Data Integrity**: Comprehensive logging and debugging for data accuracy verification
- **Performance Optimized**: Efficient caching and serialization for smooth user experience

## 🏗️ Project Structure

```
ecb-financial-visualizer/
├── app.py                         # Flask application entry point
├── src/
│   ├── api/
│   │   ├── ecb_client.py          # ECB SDMX API client
│   │   └── data_models.py         # Pydantic data models
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models
│   │   └── database.py            # Database connection & management
│   ├── services/
│   │   ├── data_service.py        # Data fetching/storage logic
│   │   └── chart_service.py       # Interactive Plotly chart generation
│   ├── ui/
│   │   ├── components/
│   │   │   └── advanced_components.py  # Interactive chart components
│   │   └── pages/
│   │       └── enhanced_pages.py       # Enhanced page layouts
│   └── utils/
│       ├── config.py              # Configuration management
│       ├── logging_config.py      # Logging setup with session tracking
│       └── helpers.py             # Utility functions
├── templates/
│   ├── base.html                  # Base template with ECB styling
│   ├── dashboard.html             # Main dashboard interface
│   └── error.html                 # Error page template
├── static/
│   └── css/
│       └── ecb-theme.css          # Professional ECB styling
├── data/
│   ├── cache/                     # Local JSON cache
│   ├── database.db               # SQLite database
│   └── *.log                     # Application logs
├── docs/
│   ├── implementation.md          # Development history
│   └── onboarding_prompt.md       # Project documentation
└── requirements.txt               # Python dependencies
```
│       ├── logging_config.py      # Logging setup
│       └── helpers.py             # Utility functions
├── data/
│   ├── cache/                     # Local JSON cache
│   └── database.db               # SQLite database
├── docs/
│   └── implementation.md          # Detailed implementation plan
└── requirements.txt
```

## 🌐 API Endpoints

The Flask application provides RESTful API endpoints:

### Core Data APIs
- `GET /api/exchange-rates` - EUR/USD exchange rate chart data
- `GET /api/inflation` - HICP inflation chart data  
- `GET /api/interest-rates` - ECB deposit facility rate chart data

### Utility APIs
- `GET /api/test` - System health check and service status
- `POST /api/refresh/<data_type>` - Force refresh specific data series
- `POST /api/refresh-all` - Refresh all data series

### Web Interface
- `GET /` - Main dashboard with interactive charts
- All endpoints return JSON data optimized for frontend consumption

## 📈 Data Sources

All data is sourced from the official European Central Bank API:
- **API Base**: https://data-api.ecb.europa.eu/service
- **Format**: SDMX 2.1 JSON (modern standard)
- **Series**: 
  - **Exchange Rates (EXR)**: EUR/USD daily rates - `D.USD.EUR.SP00.A`
  - **Inflation (ICP)**: Harmonised Index of Consumer Prices - `M.U2.N.000000.4.ANR`
  - **Interest Rates (FM)**: ECB Deposit Facility Rate - `D.U2.EUR.4F.KR.DFR.LEV`
- **Data Period**: 12 months of historical data by default
- **Caching**: Local SQLite database for offline access and performance
- **Update Frequency**: Real-time refresh capabilities with manual controls

## 📈 Interactive Features

### Chart Functionality
- **Professional ECB Styling**: Corporate colors, fonts, and layout standards
- **Time Range Selection**: Quick navigation with 1M, 3M, 6M, 1Y, and All data buttons
- **Interactive Exploration**: Zoom, pan, and hover tooltips for detailed analysis
- **Reference Lines**: ECB inflation target (2.0%) and policy rate visualizations
- **Step Charts**: Policy rate changes displayed with appropriate step visualization
- **Real-time Updates**: Individual chart refresh controls for latest data

### Data Visualizations
- **EUR/USD Exchange Rates**: Daily exchange rate trends with currency pair analysis
- **Inflation (HICP)**: Year-over-year inflation with ECB target comparison
- **Interest Rates**: ECB Deposit Facility Rate with policy change tracking
- **Integrated Dashboard**: Combined view of all financial indicators with synchronized controls

### Enhanced User Experience
- **Responsive Design**: Bootstrap-based UI optimized for desktop and mobile
- **Real-time Data Refresh**: Force refresh capabilities for individual or all data series
- **Comprehensive Error Handling**: User-friendly error messages with recovery options
- **Performance Optimized**: Efficient data loading, caching, and chart rendering
- **Professional Theming**: ECB corporate identity with institutional-grade presentation

## 🛠️ Development

### Technology Stack
- **Backend**: Flask 2.3+ with RESTful API design
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript ES6+
- **Charts**: Plotly 5.17+ for interactive financial visualizations
- **Data Layer**: SQLAlchemy 2.0+ with SQLite for persistence
- **API Integration**: ECB SDMX 2.1 REST API with Pydantic 2.4+ data models
- **Python**: 3.11+ with comprehensive type hints and modern async patterns

### Recent Critical Bug Fixes
- **Chart Data Serialization**: Resolved pandas/NumPy JSON serialization issues
- **Data Type Conversion**: Explicit Python type conversion for chart stability
- **API Response Handling**: Enhanced error handling for ECB API edge cases
- **Frontend-Backend Integration**: Improved data pipeline between Flask and JavaScript

### Code Quality
The project follows enterprise-grade standards:
- **Type Safety**: Comprehensive type hints with MyPy validation
- **Error Handling**: Robust exception handling with detailed logging
- **Performance**: Optimized database queries and caching strategies
- **Security**: Input validation and secure API endpoint design

### Logging & Debugging
- **Session Tracking**: Unique session IDs for request tracing
- **Comprehensive Logging**: Application logs with timestamp and severity levels
- **Debug Information**: Chart data validation and API response tracking
- **Error Diagnostics**: Detailed error messages for troubleshooting

### Database Management
- **Automatic Initialization**: Database schema creation on first run
- **Data Caching**: Intelligent caching with timestamp-based validation
- **Performance Optimization**: Indexed queries for fast data retrieval

## 📝 License

This project is for educational and personal use. Data is provided by the European Central Bank under their terms of use.

## 🆘 Troubleshooting

### Common Issues

1. **ImportError or Module Not Found**: 
   - Ensure the virtual environment is activated: `.venv\Scripts\activate` (Windows)
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Check Python version: requires 3.11+

2. **Port 5000 occupied**: 
   - Kill existing Flask processes or change port in `app.py`
   - Use `netstat -ano | findstr :5000` to identify blocking processes

3. **API connection issues**: 
   - Check internet connection and ECB API status
   - Verify ECB API endpoints: https://data-api.ecb.europa.eu/service
   - Review logs in `data/` directory for detailed error information

4. **Chart display issues**: 
   - Clear browser cache and reload page
   - Check JavaScript console for frontend errors
   - Verify API endpoints return valid JSON: `http://localhost:5000/api/test`

5. **Database errors**:
   - Delete `data/database.db` to reinitialize (will lose cached data)
   - Ensure write permissions in the `data/` directory
   - Check disk space for SQLite operations

### Performance Optimization

- **Data Refresh**: Use individual chart refresh rather than refresh-all for better performance
- **Browser**: Modern browsers (Chrome, Firefox, Edge) provide optimal chart performance
- **Memory**: Close unused browser tabs when working with large datasets

### Development Debugging

- **Flask Debug Mode**: Set `debug=True` in `app.py` for detailed error messages
- **API Testing**: Use `/api/test` endpoint to verify system health
- **Log Analysis**: Check `data/ecb_visualizer_YYYYMMDD.log` for session-specific debugging
- **Chart Data**: Use browser developer tools to inspect API responses

### Support Resources

- **Implementation Details**: Review `docs/implementation.md` for technical specifications
- **ECB API Documentation**: https://data.ecb.europa.eu/help/api/overview
- **Project Structure**: All components documented in code with comprehensive docstrings
- **Error Logs**: Detailed logging with unique session IDs for issue tracking

---

**Built with** 🐍 Python, 🌐 Flask, 📊 Bootstrap, 📈 Plotly, 🏛️ ECB SDMX API, and 💾 SQLite

**Status**: ✅ Production Ready | 🔄 Workshop Ready | 📊 Data Validated | 🎨 Professional UI
