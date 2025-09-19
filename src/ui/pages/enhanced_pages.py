"""
Enhanced pages with integrated charts for Phase 3
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

from services.data_service import DataService
from ui.components.advanced_components import create_chart_components
from utils.logging_config import get_logger

logger = get_logger(__name__)

class EnhancedExchangeRatePage:
    """Enhanced exchange rate page with interactive charts"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.chart_components = create_chart_components(data_service)
    
    def render(self):
        """Render the enhanced exchange rate page"""
        st.header("💱 EUR/USD Exchange Rates")
        
        # Page controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("**Interactive time series chart with zoom, pan, and range selection**")
        
        with col2:
            if st.button("🔄 Fetch Latest Data", key="fetch_exchange_rate"):
                self._fetch_data()
        
        with col3:
            show_raw_data = st.checkbox("📋 Show Raw Data", key="show_exchange_raw")
        
        # Get data
        exchange_data = self.data_service.get_exchange_rate_data()
        
        if exchange_data and exchange_data.observations:
            # Success message
            st.success(f"✅ Loaded {len(exchange_data.observations)} exchange rate observations")
            
            # Render chart
            chart_rendered = self.chart_components['exchange_rate'].render(exchange_data)
            
            # Show additional information
            if chart_rendered:
                with st.expander("📊 Data Information", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Series:** {exchange_data.metadata.title}")
                        st.write(f"**Frequency:** {exchange_data.metadata.frequency.value}")
                        st.write(f"**Unit:** {exchange_data.metadata.unit or 'EUR per USD'}")
                    
                    with col2:
                        st.write(f"**Last Updated:** {exchange_data.metadata.last_updated}")
                        st.write(f"**Data Points:** {len(exchange_data.observations)}")
                        if exchange_data.latest_value:
                            st.write(f"**Latest Rate:** {exchange_data.latest_value:.4f}")
            
            # Show raw data if requested
            if show_raw_data:
                self._show_raw_data(exchange_data)
                
        else:
            st.warning("⚠️ No exchange rate data available.")
            if st.button("🚀 Fetch Exchange Rate Data", key="initial_fetch"):
                self._fetch_data()
    
    def _fetch_data(self):
        """Fetch exchange rate data"""
        with st.spinner("Fetching EUR/USD exchange rate data..."):
            try:
                result = self.data_service.ecb_client.fetch_exchange_rates()
                if result.success:
                    st.success("✅ Exchange rate data fetched successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to fetch data: {result.error_message}")
            except Exception as e:
                st.error(f"❌ Error fetching data: {str(e)}")
                logger.error(f"Exchange rate fetch error: {e}")
    
    def _show_raw_data(self, data):
        """Display raw data table"""
        st.subheader("📋 Raw Data")
        
        import pandas as pd
        
        # Prepare data for display
        df_data = []
        for obs in sorted(data.observations, key=lambda x: x.period, reverse=True)[:100]:  # Limit to 100 most recent
            df_data.append({
                "Date": obs.period,
                "Exchange Rate": f"{obs.value:.4f}",
                "Status": obs.status.value if obs.status else "Normal"
            })
        
        df = pd.DataFrame(df_data)
        
        # Display with download option
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(df, use_container_width=True, height=400)
        
        with col2:
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"eur_usd_rates_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

class EnhancedInflationPage:
    """Enhanced inflation page with interactive charts"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.chart_components = create_chart_components(data_service)
    
    def render(self):
        """Render the enhanced inflation page"""
        st.header("📈 Inflation Data (HICP)")
        
        # Page controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("**Harmonised Index of Consumer Prices with ECB 2% target reference**")
        
        with col2:
            if st.button("🔄 Fetch Latest Data", key="fetch_inflation"):
                self._fetch_data()
        
        with col3:
            show_raw_data = st.checkbox("📋 Show Raw Data", key="show_inflation_raw")
        
        # Get data
        inflation_data = self.data_service.get_inflation_data()
        
        if inflation_data and inflation_data.observations:
            # Success message
            st.success(f"✅ Loaded {len(inflation_data.observations)} inflation observations")
            
            # Render chart
            chart_rendered = self.chart_components['inflation'].render(inflation_data)
            
            # Show target analysis
            if chart_rendered and inflation_data.latest_value:
                self._show_target_analysis(inflation_data)
            
            # Show additional information
            if chart_rendered:
                with st.expander("📊 Data Information", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Series:** {inflation_data.metadata.title}")
                        st.write(f"**Frequency:** {inflation_data.metadata.frequency.value}")
                        st.write(f"**Unit:** Percentage")
                    
                    with col2:
                        st.write(f"**Last Updated:** {inflation_data.metadata.last_updated}")
                        st.write(f"**Data Points:** {len(inflation_data.observations)}")
                        st.write(f"**ECB Target:** 2.0%")
            
            # Show raw data if requested
            if show_raw_data:
                self._show_raw_data(inflation_data)
                
        else:
            st.warning("⚠️ No inflation data available.")
            if st.button("🚀 Fetch Inflation Data", key="initial_fetch_inflation"):
                self._fetch_data()
    
    def _fetch_data(self):
        """Fetch inflation data"""
        with st.spinner("Fetching inflation data..."):
            try:
                result = self.data_service.ecb_client.fetch_inflation_data()
                if result.success:
                    st.success("✅ Inflation data fetched successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to fetch data: {result.error_message}")
            except Exception as e:
                st.error(f"❌ Error fetching data: {str(e)}")
                logger.error(f"Inflation fetch error: {e}")
    
    def _show_target_analysis(self, data):
        """Show ECB target analysis"""
        with st.expander("🎯 ECB Target Analysis", expanded=True):
            deviation = data.target_deviation
            
            if deviation is not None:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Rate", f"{data.latest_value:.1f}%")
                
                with col2:
                    st.metric("ECB Target", "2.0%")
                
                with col3:
                    color = "normal" if abs(deviation) < 0.5 else "inverse"
                    st.metric("Deviation", f"{deviation:+.1f}%")
                
                # Analysis text
                if abs(deviation) < 0.2:
                    st.success("🎯 **Perfect alignment** with ECB target")
                elif abs(deviation) < 0.5:
                    st.info("📊 **Close to target** - within acceptable range")
                elif deviation > 0.5:
                    st.warning("📈 **Above target** - inflationary pressure")
                else:
                    st.warning("📉 **Below target** - deflationary risk")
    
    def _show_raw_data(self, data):
        """Display raw data table"""
        st.subheader("📋 Raw Data")
        
        import pandas as pd
        
        # Prepare data for display
        df_data = []
        for obs in sorted(data.observations, key=lambda x: x.period, reverse=True)[:100]:
            df_data.append({
                "Date": obs.period,
                "Inflation Rate (%)": f"{obs.value:.1f}",
                "Deviation from Target": f"{obs.value - 2.0:+.1f}%",
                "Status": obs.status.value if obs.status else "Normal"
            })
        
        df = pd.DataFrame(df_data)
        
        # Display with download option
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(df, use_container_width=True, height=400)
        
        with col2:
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"inflation_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

class EnhancedInterestRatePage:
    """Enhanced interest rate page with interactive charts"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.chart_components = create_chart_components(data_service)
    
    def render(self):
        """Render the enhanced interest rate page"""
        st.header("🏦 ECB Interest Rates")
        
        # Page controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("**ECB Main Refinancing Rate - Step chart showing policy changes**")
        
        with col2:
            if st.button("🔄 Fetch Latest Data", key="fetch_interest_rate"):
                self._fetch_data()
        
        with col3:
            show_raw_data = st.checkbox("📋 Show Raw Data", key="show_interest_raw")
        
        # Get data
        rate_data = self.data_service.get_interest_rate_data()
        
        if rate_data and rate_data.observations:
            # Success message
            st.success(f"✅ Loaded {len(rate_data.observations)} interest rate observations")
            
            # Render chart
            chart_rendered = self.chart_components['interest_rate'].render(rate_data)
            
            # Show additional information
            if chart_rendered:
                with st.expander("📊 Data Information", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Series:** {rate_data.metadata.title}")
                        st.write(f"**Frequency:** {rate_data.metadata.frequency.value}")
                        st.write(f"**Unit:** Percentage")
                    
                    with col2:
                        st.write(f"**Last Updated:** {rate_data.metadata.last_updated}")
                        st.write(f"**Data Points:** {len(rate_data.observations)}")
                        if rate_data.latest_value:
                            st.write(f"**Current Rate:** {rate_data.latest_value:.2f}%")
            
            # Show raw data if requested
            if show_raw_data:
                self._show_raw_data(rate_data)
                
        else:
            st.warning("⚠️ No interest rate data available.")
            if st.button("🚀 Fetch Interest Rate Data", key="initial_fetch_rates"):
                self._fetch_data()
    
    def _fetch_data(self):
        """Fetch interest rate data"""
        with st.spinner("Fetching interest rate data..."):
            try:
                result = self.data_service.ecb_client.fetch_interest_rates()
                if result.success:
                    st.success("✅ Interest rate data fetched successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to fetch data: {result.error_message}")
            except Exception as e:
                st.error(f"❌ Error fetching data: {str(e)}")
                logger.error(f"Interest rate fetch error: {e}")
    
    def _show_raw_data(self, data):
        """Display raw data table"""
        st.subheader("📋 Raw Data")
        
        import pandas as pd
        
        # Prepare data for display
        df_data = []
        for obs in sorted(data.observations, key=lambda x: x.period, reverse=True)[:100]:
            df_data.append({
                "Date": obs.period,
                "Interest Rate (%)": f"{obs.value:.2f}",
                "Status": obs.status.value if obs.status else "Normal"
            })
        
        df = pd.DataFrame(df_data)
        
        # Display with download option
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(df, use_container_width=True, height=400)
        
        with col2:
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"ecb_rates_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

class EnhancedDashboardPage:
    """Enhanced dashboard page with overview chart"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.chart_components = create_chart_components(data_service)
    
    def render(self):
        """Render the enhanced dashboard page"""
        st.header("📊 Financial Data Dashboard")
        
        # Dashboard controls
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown("**Real-time ECB financial indicators with interactive charts**")
        
        with col2:
            if st.button("🔄 Refresh All", key="refresh_dashboard"):
                self._refresh_all_data()
        
        with col3:
            show_overview_btn = st.button("📊 Overview Chart", key="show_overview")
        
        with col4:
            auto_refresh = st.checkbox("🔄 Auto-refresh", key="auto_refresh")
        
        # Get dashboard data
        dashboard_data = self.data_service.get_dashboard_data()
        
        # Show overview chart if data available
        if dashboard_data.has_data:
            # Initialize the session state if not present
            if 'dashboard_show_overview' not in st.session_state:
                st.session_state.dashboard_show_overview = True
            
            # Toggle overview chart visibility based on button click
            if show_overview_btn:
                st.session_state.dashboard_show_overview = not st.session_state.dashboard_show_overview
            
            if st.session_state.dashboard_show_overview:
                st.subheader("📈 Overview Chart")
                self.chart_components['dashboard_overview'].render(self.data_service)
                st.divider()
        
        # Individual sections
        self._render_individual_sections(dashboard_data)
        
        # Data refresh status
        if dashboard_data.last_refresh:
            st.caption(f"🕒 Last refreshed: {dashboard_data.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.caption("🕒 No data refresh recorded")
    
    def _refresh_all_data(self):
        """Refresh all financial data"""
        with st.spinner("Refreshing all financial data..."):
            try:
                result = self.data_service.refresh_all_data(force=True)
                if result.successful > 0:
                    st.success(f"✅ Successfully refreshed {result.successful} of {result.total_series} data series!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to refresh data: {result.failed} of {result.total_series} series failed")
            except Exception as e:
                st.error(f"❌ Error refreshing data: {str(e)}")
                logger.error(f"Dashboard refresh error: {e}")
    
    def _render_individual_sections(self, dashboard_data):
        """Render individual data sections"""
        
        # Quick metrics row
        st.subheader("📊 Current Values")
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
                delta = f"{deviation:+.1f}% vs target" if deviation is not None else None
                
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
                    value=f"{latest_rate:.2f}%"
                )
            else:
                st.metric(
                    label="ECB Main Rate",
                    value="No data"
                )
        
        # Data availability status
        st.subheader("📋 Data Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if dashboard_data.exchange_rates:
                st.success("✅ Exchange Rates Available")
                st.caption(f"{len(dashboard_data.exchange_rates.observations)} observations")
            else:
                st.error("❌ Exchange Rates Not Available")
        
        with col2:
            if dashboard_data.inflation:
                st.success("✅ Inflation Data Available")
                st.caption(f"{len(dashboard_data.inflation.observations)} observations")
            else:
                st.error("❌ Inflation Data Not Available")
        
        with col3:
            if dashboard_data.interest_rates:
                st.success("✅ Interest Rates Available")
                st.caption(f"{len(dashboard_data.interest_rates.observations)} observations")
            else:
                st.error("❌ Interest Rates Not Available")
        
        # Quick actions
        if not dashboard_data.has_data:
            st.warning("⚠️ No financial data available. Please fetch data to begin.")
            if st.button("🚀 Fetch All Data", key="fetch_all_dashboard"):
                self._refresh_all_data()
