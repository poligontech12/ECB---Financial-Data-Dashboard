"""
Advanced UI components for financial data visualization
"""
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, Any

from services.chart_service import ChartService
from services.data_service import DataService
from api.data_models import ExchangeRateData, InflationData, InterestRateData
from utils.logging_config import get_logger

logger = get_logger(__name__)

class ChartComponent:
    """Base component for displaying financial charts"""
    
    def __init__(self, chart_service: ChartService):
        self.chart_service = chart_service
    
    def render_chart_with_controls(self, fig: go.Figure, data_info: dict = None):
        """Render a chart with controls and information"""
        
        # Chart controls row
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if data_info:
                st.caption(f"📊 {data_info.get('observations', 0)} data points | "
                          f"Last updated: {data_info.get('last_updated', 'Unknown')}")
        
        with col2:
            if st.button("🔄 Refresh Chart", key=f"refresh_{id(fig)}"):
                st.rerun()
        
        with col3:
            show_info = st.checkbox("ℹ️ Show Info", key=f"info_{id(fig)}")
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'scrollZoom': False,
            'doubleClick': 'reset+autosize'
        })
        
        # Show additional information if requested
        if show_info and data_info:
            with st.expander("📈 Chart Information"):
                for key, value in data_info.items():
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")

class ExchangeRateChart(ChartComponent):
    """Component for EUR/USD exchange rate charts"""
    
    def render(self, data: Optional[ExchangeRateData]) -> bool:
        """Render exchange rate chart"""
        try:
            if not data or not data.observations:
                st.warning("⚠️ No exchange rate data available for charting")
                return False
            
            # Create chart
            fig = self.chart_service.create_exchange_rate_chart(data)
            
            # Prepare data info
            data_info = {
                'observations': len(data.observations),
                'last_updated': data.metadata.last_updated.strftime('%Y-%m-%d %H:%M') if data.metadata.last_updated else 'Unknown',
                'frequency': data.metadata.frequency.value if data.metadata.frequency else 'Unknown',
                'latest_rate': f"{data.latest_value:.4f}" if data.latest_value else 'N/A',
                'series_title': data.metadata.title or 'EUR/USD Exchange Rate'
            }
            
            # Show current rate prominently
            if data.latest_value:
                change = data.get_percentage_change(1)
                delta = f"{change:+.4f}%" if change else None
                st.metric(
                    "Current EUR/USD Rate", 
                    f"{data.latest_value:.4f}",
                    delta=delta
                )
            
            # Render chart with controls
            self.render_chart_with_controls(fig, data_info)
            
            return True
            
        except Exception as e:
            logger.error(f"Error rendering exchange rate chart: {e}")
            st.error(f"❌ Error displaying chart: {str(e)}")
            return False

class InflationChart(ChartComponent):
    """Component for inflation charts"""
    
    def render(self, data: Optional[InflationData]) -> bool:
        """Render inflation chart"""
        try:
            if not data or not data.observations:
                st.warning("⚠️ No inflation data available for charting")
                return False
            
            # Create chart
            fig = self.chart_service.create_inflation_chart(data)
            
            # Prepare data info
            data_info = {
                'observations': len(data.observations),
                'last_updated': data.metadata.last_updated.strftime('%Y-%m-%d %H:%M') if data.metadata.last_updated else 'Unknown',
                'frequency': data.metadata.frequency.value if data.metadata.frequency else 'Unknown',
                'latest_rate': f"{data.latest_value:.1f}%" if data.latest_value else 'N/A',
                'ecb_target': '2.0%',
                'series_title': data.metadata.title or 'Inflation Rate (HICP)'
            }
            
            # Show current inflation with target comparison
            if data.latest_value:
                deviation = data.target_deviation
                if deviation is not None:
                    delta_text = f"{deviation:+.1f}% vs target"
                    delta_color = "normal" if abs(deviation) < 0.5 else "inverse"
                else:
                    delta_text = None
                    delta_color = "normal"
                
                st.metric(
                    "Current Inflation Rate", 
                    f"{data.latest_value:.1f}%",
                    delta=delta_text
                )
                
                # Target status
                if deviation is not None:
                    if abs(deviation) < 0.5:
                        st.success(f"🎯 Close to ECB target (2.0%)")
                    else:
                        st.info(f"📊 Deviation from ECB target: {deviation:+.1f}%")
            
            # Render chart with controls
            self.render_chart_with_controls(fig, data_info)
            
            return True
            
        except Exception as e:
            logger.error(f"Error rendering inflation chart: {e}")
            st.error(f"❌ Error displaying chart: {str(e)}")
            return False

class InterestRateChart(ChartComponent):
    """Component for interest rate charts"""
    
    def render(self, data: Optional[InterestRateData]) -> bool:
        """Render interest rate chart"""
        try:
            if not data or not data.observations:
                st.warning("⚠️ No interest rate data available for charting")
                return False
            
            # Create chart
            fig = self.chart_service.create_interest_rate_chart(data)
            
            # Prepare data info
            data_info = {
                'observations': len(data.observations),
                'last_updated': data.metadata.last_updated.strftime('%Y-%m-%d %H:%M') if data.metadata.last_updated else 'Unknown',
                'frequency': data.metadata.frequency.value if data.metadata.frequency else 'Unknown',
                'latest_rate': f"{data.latest_value:.2f}%" if data.latest_value else 'N/A',
                'series_title': data.metadata.title or 'ECB Main Refinancing Rate'
            }
            
            # Show current rate
            if data.latest_value:
                # Calculate change if possible
                change = data.get_percentage_change(1) if hasattr(data, 'get_percentage_change') else None
                delta = f"{change:+.2f}%" if change else None
                
                st.metric(
                    "Current ECB Main Rate", 
                    f"{data.latest_value:.2f}%",
                    delta=delta
                )
            
            # Render chart with controls
            self.render_chart_with_controls(fig, data_info)
            
            return True
            
        except Exception as e:
            logger.error(f"Error rendering interest rate chart: {e}")
            st.error(f"❌ Error displaying chart: {str(e)}")
            return False

class DashboardOverviewChart(ChartComponent):
    """Component for dashboard overview chart"""
    
    def render(self, data_service: DataService) -> bool:
        """Render dashboard overview chart"""
        try:
            # Get all data
            dashboard_data = data_service.get_dashboard_data()
            
            if not dashboard_data.has_data:
                st.info("📊 No data available for overview chart. Fetch data first.")
                return False
            
            # Create overview chart
            fig = self.chart_service.create_dashboard_overview(dashboard_data)
            
            # Prepare summary info
            data_info = {
                'last_refresh': dashboard_data.last_refresh.strftime('%Y-%m-%d %H:%M') if dashboard_data.last_refresh else 'Never',
                'exchange_rates': 'Available' if dashboard_data.exchange_rates else 'Not available',
                'inflation': 'Available' if dashboard_data.inflation else 'Not available',
                'interest_rates': 'Available' if dashboard_data.interest_rates else 'Not available'
            }
            
            # Show summary metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if dashboard_data.exchange_rates and dashboard_data.exchange_rates.latest_value:
                    change = dashboard_data.exchange_rates.get_percentage_change(1)
                    st.metric(
                        "EUR/USD", 
                        f"{dashboard_data.exchange_rates.latest_value:.4f}",
                        delta=f"{change:+.4f}%" if change else None
                    )
                else:
                    st.metric("EUR/USD", "No data")
            
            with col2:
                if dashboard_data.inflation and dashboard_data.inflation.latest_value:
                    deviation = dashboard_data.inflation.target_deviation
                    st.metric(
                        "Inflation", 
                        f"{dashboard_data.inflation.latest_value:.1f}%",
                        delta=f"{deviation:+.1f}% vs target" if deviation is not None else None
                    )
                else:
                    st.metric("Inflation", "No data")
            
            with col3:
                if dashboard_data.interest_rates and dashboard_data.interest_rates.latest_value:
                    st.metric(
                        "ECB Rate", 
                        f"{dashboard_data.interest_rates.latest_value:.2f}%"
                    )
                else:
                    st.metric("ECB Rate", "No data")
            
            # Render chart with controls
            self.render_chart_with_controls(fig, data_info)
            
            return True
            
        except Exception as e:
            logger.error(f"Error rendering dashboard overview: {e}")
            st.error(f"❌ Error displaying overview: {str(e)}")
            return False

def create_chart_components(data_service: DataService) -> dict:
    """Factory function to create all chart components"""
    chart_service = ChartService()
    
    return {
        'exchange_rate': ExchangeRateChart(chart_service),
        'inflation': InflationChart(chart_service),
        'interest_rate': InterestRateChart(chart_service),
        'dashboard_overview': DashboardOverviewChart(chart_service)
    }
