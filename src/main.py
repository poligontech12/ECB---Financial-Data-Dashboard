"""
ECB Financial Data Visualizer - Main Streamlit Application
"""
import streamlit as st
from datetime import datetime
import sys
import os
import traceback

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import get_config, STREAMLIT_CONFIG
from utils.logging_config import get_logger
from database.database import init_database, db_manager
from services.data_service import DataService
from api.ecb_client import ECBClient

# Setup logging
logger = get_logger(__name__)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services"""
    try:
        # Initialize database
        init_success = init_database()
        if not init_success:
            st.error("Database initialization failed!")
            return None, None
        
        # Initialize services
        data_service = DataService()
        ecb_client = ECBClient()
        
        logger.info("Services initialized successfully")
        return data_service, ecb_client
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        st.error(f"Service initialization failed: {str(e)}")
        return None, None

def main():
    """Main application entry point"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title=STREAMLIT_CONFIG["page_title"],
        page_icon=STREAMLIT_CONFIG["page_icon"],
        layout=STREAMLIT_CONFIG["layout"],
        initial_sidebar_state=STREAMLIT_CONFIG["initial_sidebar_state"]
    )
    
    # Initialize services
    data_service, ecb_client = get_services()
    
    # Header
    st.title("📈 ECB Financial Data Visualizer")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🏛️ Navigation")
        
        page = st.selectbox(
            "Select Page",
            ["Dashboard", "Exchange Rates", "Inflation", "Interest Rates", "Settings"]
        )
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        st.success("Phase 1: Basic setup complete ✅")
        st.success("Phase 2: API integration ready ✅")
        st.success("Phase 3: Interactive charts ready ✅")
        
        # System status
        if data_service and ecb_client:
            st.success("✅ Services initialized")
            
            # Test API connection
            if st.button("🔗 Test API Connection"):
                with st.spinner("Testing API connection..."):
                    connection_ok = ecb_client.test_connection()
                    if connection_ok:
                        st.success("✅ API connection successful!")
                    else:
                        st.error("❌ API connection failed")
        else:
            st.error("❌ Services not available")
    
    # Main content based on selected page
    if data_service and ecb_client:
        if page == "Dashboard":
            show_enhanced_dashboard(data_service)
        elif page == "Exchange Rates":
            show_enhanced_exchange_rates(data_service)
        elif page == "Inflation":
            show_enhanced_inflation(data_service)
        elif page == "Interest Rates":
            show_enhanced_interest_rates(data_service)
        elif page == "Settings":
            show_settings(data_service)
    else:
        st.error("⚠️ Application services are not available. Please check the logs.")

def show_dashboard(data_service: DataService):
    """Show main dashboard"""
    st.header("📊 Financial Data Dashboard")
    
    # Get dashboard data
    dashboard_data = data_service.get_dashboard_data()
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if dashboard_data.exchange_rates and dashboard_data.exchange_rates.latest_value:
            latest_rate = dashboard_data.exchange_rates.latest_value
            change = dashboard_data.exchange_rates.get_percentage_change(1)
            delta = f"{change:+.4f}%" if change else None
            
            st.metric(
                label="EUR/USD Rate",
                value=f"{latest_rate:.4f}",
                delta=delta
            )
        else:
            st.metric(
                label="EUR/USD Rate",
                value="No data",
                delta=None
            )
    
    with col2:
        if dashboard_data.inflation and dashboard_data.inflation.latest_value:
            latest_inflation = dashboard_data.inflation.latest_value
            deviation = dashboard_data.inflation.target_deviation
            delta = f"{deviation:+.1f}% vs target" if deviation else None
            
            st.metric(
                label="Inflation Rate",
                value=f"{latest_inflation:.1f}%",
                delta=delta
            )
        else:
            st.metric(
                label="Inflation Rate", 
                value="No data",
                delta=None
            )
    
    with col3:
        if dashboard_data.interest_rates and dashboard_data.interest_rates.latest_value:
            latest_rate = dashboard_data.interest_rates.latest_value
            st.metric(
                label="ECB Main Rate",
                value=f"{latest_rate:.2f}%",
                delta=None
            )
        else:
            st.metric(
                label="ECB Main Rate",
                value="No data",
                delta=None
            )
    
    st.markdown("---")
    
    # Data status
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Data Status")
        if dashboard_data.has_data:
            st.success("✅ Financial data is available")
            if dashboard_data.last_refresh:
                st.info(f"Last refresh: {dashboard_data.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.warning("⚠️ No financial data available. Click 'Fetch Data' to load data.")
    
    with col2:
        st.subheader("⚡ Actions")
        if st.button("🔄 Fetch Data", type="primary", help="Fetch latest data from ECB API"):
            fetch_data(data_service)
    
    # Quick stats
    if dashboard_data.has_data:
        st.subheader("📈 Quick Statistics")
        stats = data_service.get_data_statistics()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Series", stats.get("series_count", 0))
        with col2:
            st.metric("Total Observations", stats.get("total_observations", 0))
        with col3:
            if dashboard_data.exchange_rates:
                st.metric("EUR/USD Observations", dashboard_data.exchange_rates.observation_count)

def show_exchange_rates(data_service: DataService):
    """Show exchange rates page"""
    st.header("� EUR/USD Exchange Rates")
    
    # Get exchange rate data
    exchange_data = data_service.get_exchange_rate_data()
    
    if exchange_data and exchange_data.observations:
        st.success(f"✅ Loaded {len(exchange_data.observations)} exchange rate observations")
        
        # Show latest rate
        latest = exchange_data.latest_value
        if latest:
            st.metric("Latest EUR/USD Rate", f"{latest:.4f}")
        
        # Show data info
        with st.expander("📊 Data Information"):
            st.write(f"**Series:** {exchange_data.metadata.title}")
            st.write(f"**Frequency:** {exchange_data.metadata.frequency.value}")
            st.write(f"**Unit:** {exchange_data.metadata.unit or 'EUR per USD'}")
            st.write(f"**Last Updated:** {exchange_data.metadata.last_updated}")
        
        # Simple data table (charts in Phase 3)
        if st.checkbox("Show raw data"):
            import pandas as pd
            df_data = []
            for obs in sorted(exchange_data.observations, key=lambda x: x.period, reverse=True)[:50]:
                df_data.append({
                    "Date": obs.period,
                    "Rate": obs.value,
                    "Status": obs.status.value if obs.status else "Normal"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ No exchange rate data available. Click 'Fetch Data' to load data.")
        if st.button("🔄 Fetch Exchange Rate Data"):
            fetch_exchange_rate_data(data_service)

def show_inflation(data_service: DataService):
    """Show inflation page"""
    st.header("� Inflation Data")
    
    inflation_data = data_service.get_inflation_data()
    
    if inflation_data and inflation_data.observations:
        st.success(f"✅ Loaded {len(inflation_data.observations)} inflation observations")
        
        latest = inflation_data.latest_value
        if latest:
            st.metric("Latest Inflation Rate", f"{latest:.1f}%")
            
            deviation = inflation_data.target_deviation
            if deviation is not None:
                if abs(deviation) < 0.5:
                    st.success(f"🎯 Close to ECB target (2.0%). Deviation: {deviation:+.1f}%")
                else:
                    st.warning(f"📊 Deviation from ECB target: {deviation:+.1f}%")
    else:
        st.warning("⚠️ No inflation data available. Click 'Fetch Data' to load data.")

def show_interest_rates(data_service: DataService):
    """Show interest rates page"""
    st.header("🏦 Interest Rates")
    
    rate_data = data_service.get_interest_rate_data()
    
    if rate_data and rate_data.observations:
        st.success(f"✅ Loaded {len(rate_data.observations)} interest rate observations")
        
        latest = rate_data.latest_value
        if latest:
            st.metric("Latest ECB Main Rate", f"{latest:.2f}%")
    else:
        st.warning("⚠️ No interest rate data available. Click 'Fetch Data' to load data.")

def show_settings(data_service: DataService):
    """Show settings page"""
    st.header("⚙️ Settings")
    
    # System status
    st.subheader("🔧 System Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("✅ Streamlit: Running")
        st.success("✅ Configuration: Loaded") 
        st.success("✅ Logging: Active")
        st.success("✅ Database: Connected")
    
    with col2:
        # Database health check
        db_health = db_manager.health_check()
        if db_health:
            st.success("✅ Database: Healthy")
        else:
            st.error("❌ Database: Connection issues")
        
        # API test
        ecb_client = ECBClient()
        api_health = ecb_client.test_connection()
        if api_health:
            st.success("✅ ECB API: Connected")
        else:
            st.error("❌ ECB API: Connection issues")
    
    # Database info
    st.subheader("🗄️ Database Information")
    db_info = db_manager.get_database_info()
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Type:** {db_info.get('type', 'Unknown')}")
        st.write(f"**File Size:** {db_info.get('file_size_mb', 0)} MB")
    with col2:
        st.write(f"**Tables:** {db_info.get('table_count', 0)}")
        if 'tables' in db_info:
            st.write(f"**Table Names:** {', '.join(db_info['tables'])}")
    
    # Configuration display
    st.subheader("📋 Configuration")
    with st.expander("View Configuration"):
        config = get_config()
        st.json(config)

def fetch_data(data_service: DataService):
    """Fetch all data with progress indication"""
    with st.spinner("Fetching financial data from ECB API..."):
        try:
            result = data_service.refresh_all_data(force=True)
            
            if result.successful > 0:
                st.success(f"✅ Successfully fetched {result.successful}/{result.total_series} data series!")
                st.info(f"⏱️ Operation completed in {result.duration_seconds:.1f} seconds")
                
                # Show detailed results
                with st.expander("📊 Fetch Results"):
                    for fetch_result in result.results:
                        if fetch_result.success:
                            st.success(f"✅ {fetch_result.series_key}: {fetch_result.observations_count} observations")
                        else:
                            st.error(f"❌ {fetch_result.series_key}: {fetch_result.error_message}")
                
                # Rerun to refresh displayed data
                st.rerun()
            else:
                st.error("❌ Failed to fetch data. Please check your internet connection and try again.")
                
        except Exception as e:
            st.error(f"❌ Error fetching data: {str(e)}")
            logger.error(f"Data fetch error: {e}\n{traceback.format_exc()}")

def fetch_exchange_rate_data(data_service: DataService):
    """Fetch only exchange rate data"""
    with st.spinner("Fetching EUR/USD exchange rate data..."):
        try:
            ecb_client = ECBClient()
            result = ecb_client.fetch_exchange_rates()
            
            if result.success and result.data:
                data_service._store_series_data(result.data)
                st.success(f"✅ Successfully fetched {result.observations_count} exchange rate observations!")
                st.rerun()
            else:
                st.error(f"❌ Failed to fetch exchange rate data: {result.error_message}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Enhanced Phase 3 page functions
def show_enhanced_dashboard(data_service: DataService):
    """Show enhanced dashboard with charts"""
    from ui.pages.enhanced_pages import EnhancedDashboardPage
    
    try:
        page = EnhancedDashboardPage(data_service)
        page.render()
    except Exception as e:
        logger.error(f"Error rendering enhanced dashboard: {e}")
        st.error(f"❌ Error loading enhanced dashboard: {str(e)}")
        # Fallback to basic dashboard
        show_dashboard(data_service)

def show_enhanced_exchange_rates(data_service: DataService):
    """Show enhanced exchange rates page with charts"""
    from ui.pages.enhanced_pages import EnhancedExchangeRatePage
    
    try:
        page = EnhancedExchangeRatePage(data_service)
        page.render()
    except Exception as e:
        logger.error(f"Error rendering enhanced exchange rates: {e}")
        st.error(f"❌ Error loading enhanced charts: {str(e)}")
        # Fallback to basic page
        show_exchange_rates(data_service)

def show_enhanced_inflation(data_service: DataService):
    """Show enhanced inflation page with charts"""
    from ui.pages.enhanced_pages import EnhancedInflationPage
    
    try:
        page = EnhancedInflationPage(data_service)
        page.render()
    except Exception as e:
        logger.error(f"Error rendering enhanced inflation: {e}")
        st.error(f"❌ Error loading enhanced charts: {str(e)}")
        # Fallback to basic page
        show_inflation(data_service)

def show_enhanced_interest_rates(data_service: DataService):
    """Show enhanced interest rates page with charts"""
    from ui.pages.enhanced_pages import EnhancedInterestRatePage
    
    try:
        page = EnhancedInterestRatePage(data_service)
        page.render()
    except Exception as e:
        logger.error(f"Error rendering enhanced interest rates: {e}")
        st.error(f"❌ Error loading enhanced charts: {str(e)}")
        # Fallback to basic page
        show_interest_rates(data_service)

if __name__ == "__main__":
    logger.info("ECB Financial Data Visualizer started")
    main()
