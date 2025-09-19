"""
Chart service for generating interactive financial charts using Plotly
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd

from api.data_models import ExchangeRateData, InflationData, InterestRateData, DashboardData
from utils.config import CHART_CONFIG, RANGE_SELECTOR_BUTTONS
from utils.logging_config import get_logger

logger = get_logger(__name__)

class ChartService:
    """Service for generating interactive financial charts"""
    
    def __init__(self):
        # Range selector configuration for financial charts
        self.range_selector = {
            "buttons": RANGE_SELECTOR_BUTTONS,
            "rangeselector": {"visible": True}
        }
        
        # Financial chart theme colors
        self.colors = {
            "primary": "#1f77b4",      # Blue for main data
            "secondary": "#ff7f0e",    # Orange for comparisons
            "target": "#d62728",       # Red for targets/thresholds
            "positive": "#2ca02c",     # Green for positive changes
            "negative": "#d62728",     # Red for negative changes
            "grid": "rgba(128,128,128,0.2)"
        }
    
    def create_exchange_rate_chart(self, data: ExchangeRateData) -> go.Figure:
        """Create EUR/USD exchange rate time series chart"""
        logger.info("Creating exchange rate chart")
        
        if not data or not data.observations:
            return self._create_empty_chart("No EUR/USD exchange rate data available")
        
        # Prepare data
        df = self._prepare_exchange_rate_data(data)
        
        # Create figure
        fig = go.Figure()
        
        # Add main line chart
        # Convert DataFrame values to native Python types to avoid JSON serialization issues
        dates = df['date'].dt.strftime('%Y-%m-%d').tolist()  # Convert to ISO date strings for JSON
        rates = df['rate'].astype(float).tolist()       # Convert to Python float list
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=rates,
            mode='lines',
            name='EUR/USD Rate',
            line=dict(color=self.colors["primary"], width=2),
            hovertemplate='<b>Date:</b> %{x}<br><b>Rate:</b> %{y:.4f}<extra></extra>'
        ))
        
        # Update layout with financial styling
        fig.update_layout(
            title={
                'text': 'EUR/USD Exchange Rate',
                'x': 0.5,
                'font': {'size': 20}
            },
            xaxis=dict(
                title='Date',
                type='date',
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=RANGE_SELECTOR_BUTTONS,
                    bgcolor="rgba(150, 150, 150, 0.1)",
                    activecolor="rgba(150, 150, 150, 0.3)"
                ),
                showgrid=True,
                gridcolor=self.colors["grid"]
            ),
            yaxis=dict(
                title='Exchange Rate',
                showgrid=True,
                gridcolor=self.colors["grid"],
                tickformat='.4f'
            ),
            hovermode='x unified',
            showlegend=True,
            height=500,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Config is for display in Streamlit, not layout
        
        return fig
    
    def create_inflation_chart(self, data: InflationData) -> go.Figure:
        """Create inflation rate time series chart with ECB target"""
        logger.info("Creating inflation chart")
        
        if not data or not data.observations:
            return self._create_empty_chart("No inflation data available")
        
        # Prepare data
        df = self._prepare_inflation_data(data)
        
        # Create figure
        fig = go.Figure()
        
        # Add inflation line
        # Convert DataFrame values to native Python types to avoid JSON serialization issues
        dates = df['date'].dt.strftime('%Y-%m-%d').tolist()  # Convert to ISO date strings for JSON
        rates = df['rate'].astype(float).tolist()       # Convert to Python float list
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=rates,
            mode='lines+markers',
            name='Inflation Rate',
            line=dict(color=self.colors["primary"], width=2),
            marker=dict(size=4),
            hovertemplate='<b>Date:</b> %{x}<br><b>Rate:</b> %{y:.1f}%<extra></extra>'
        ))
        
        # Add ECB target line (2%)
        if len(df) > 0:
            fig.add_hline(
                y=2.0,
                line_dash="dash",
                line_color=self.colors["target"],
                annotation_text="ECB Target (2%)",
                annotation_position="bottom right"
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Inflation Rate (HICP)',
                'x': 0.5,
                'font': {'size': 20}
            },
            xaxis=dict(
                title='Date',
                type='date',
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=RANGE_SELECTOR_BUTTONS,
                    bgcolor="rgba(150, 150, 150, 0.1)",
                    activecolor="rgba(150, 150, 150, 0.3)"
                ),
                showgrid=True,
                gridcolor=self.colors["grid"]
            ),
            yaxis=dict(
                title='Inflation Rate (%)',
                showgrid=True,
                gridcolor=self.colors["grid"],
                tickformat='.1f'
            ),
            hovermode='x unified',
            showlegend=True,
            height=500,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Config is for display in Streamlit, not layout
        
        return fig
    
    def create_interest_rate_chart(self, data: InterestRateData) -> go.Figure:
        """Create interest rate time series chart"""
        logger.info("Creating interest rate chart")
        
        if not data or not data.observations:
            return self._create_empty_chart("No interest rate data available")
        
        # Prepare data
        df = self._prepare_interest_rate_data(data)
        
        # Create figure
        fig = go.Figure()
        
        # Add interest rate line (step chart for policy rates)
        series_name = data.metadata.title.split(' - ')[0] if data.metadata and data.metadata.title else 'ECB Rate'
        
        # Convert DataFrame values to native Python types to avoid JSON serialization issues
        dates = df['date'].dt.strftime('%Y-%m-%d').tolist()  # Convert to ISO date strings for JSON
        rates = df['rate'].astype(float).tolist()       # Convert to Python float list
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=rates,
            mode='lines',
            name=series_name,
            line=dict(color=self.colors["primary"], width=2, shape='hv'),  # Step chart
            hovertemplate='<b>Date:</b> %{x}<br><b>Rate:</b> %{y:.2f}%<extra></extra>'
        ))
        
        # Update layout with actual series title
        series_title = data.metadata.title if data.metadata and data.metadata.title else 'ECB Interest Rate'
        fig.update_layout(
            title={
                'text': series_title,
                'x': 0.5,
                'font': {'size': 20}
            },
            xaxis=dict(
                title='Date',
                type='date',
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=RANGE_SELECTOR_BUTTONS,
                    bgcolor="rgba(150, 150, 150, 0.1)",
                    activecolor="rgba(150, 150, 150, 0.3)"
                ),
                showgrid=True,
                gridcolor=self.colors["grid"]
            ),
            yaxis=dict(
                title='Interest Rate (%)',
                showgrid=True,
                gridcolor=self.colors["grid"],
                tickformat='.2f'
            ),
            hovermode='x unified',
            showlegend=True,
            height=500,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Config is for display in Streamlit, not layout
        
        return fig
    
    def create_dashboard_overview(self, dashboard_data: DashboardData) -> go.Figure:
        """Create overview chart with all indicators"""
        logger.info("Creating dashboard overview chart")
        
        # Create subplots for multiple indicators
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('EUR/USD Exchange Rate', 'Inflation Rate (%)', 'ECB Main Rate (%)'),
            vertical_spacing=0.12,
            specs=[[{"secondary_y": False}],
                   [{"secondary_y": False}],
                   [{"secondary_y": False}]]
        )
        
        # Add exchange rate if available
        if dashboard_data.exchange_rates and dashboard_data.exchange_rates.observations:
            df_eur = self._prepare_exchange_rate_data(dashboard_data.exchange_rates)
            fig.add_trace(
                go.Scatter(
                    x=df_eur['date'],
                    y=df_eur['rate'],
                    mode='lines',
                    name='EUR/USD',
                    line=dict(color=self.colors["primary"], width=1.5),
                    hovertemplate='%{y:.4f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Add inflation if available
        if dashboard_data.inflation and dashboard_data.inflation.observations:
            df_inf = self._prepare_inflation_data(dashboard_data.inflation)
            fig.add_trace(
                go.Scatter(
                    x=df_inf['date'],
                    y=df_inf['rate'],
                    mode='lines',
                    name='Inflation',
                    line=dict(color=self.colors["secondary"], width=1.5),
                    hovertemplate='%{y:.1f}%<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Add ECB target line
            if len(df_inf) > 0:
                fig.add_hline(
                    y=2.0,
                    line_dash="dash",
                    line_color=self.colors["target"],
                    row=2,
                    annotation_text="Target"
                )
        
        # Add interest rate if available
        if dashboard_data.interest_rates and dashboard_data.interest_rates.observations:
            df_rate = self._prepare_interest_rate_data(dashboard_data.interest_rates)
            fig.add_trace(
                go.Scatter(
                    x=df_rate['date'],
                    y=df_rate['rate'],
                    mode='lines',
                    name='ECB Rate',
                    line=dict(color=self.colors["primary"], width=1.5, shape='hv'),
                    hovertemplate='%{y:.2f}%<extra></extra>'
                ),
                row=3, col=1
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Financial Indicators Overview',
                'x': 0.5,
                'font': {'size': 24}
            },
            height=800,
            showlegend=False,
            hovermode='x unified'
        )
        
        # Update x-axes
        fig.update_xaxes(showgrid=True, gridcolor=self.colors["grid"])
        fig.update_yaxes(showgrid=True, gridcolor=self.colors["grid"])
        
        return fig
    
    def _prepare_exchange_rate_data(self, data: ExchangeRateData) -> pd.DataFrame:
        """Convert exchange rate data to DataFrame for plotting"""
        records = []
        for obs in sorted(data.observations, key=lambda x: x.period):
            try:
                date = pd.to_datetime(obs.period)
                records.append({
                    'date': date,
                    'rate': obs.value
                })
            except Exception as e:
                logger.warning(f"Skipping invalid observation: {obs.period} - {e}")
        
        return pd.DataFrame(records)
    
    def _prepare_inflation_data(self, data: InflationData) -> pd.DataFrame:
        """Convert inflation data to DataFrame for plotting"""
        records = []
        for obs in sorted(data.observations, key=lambda x: x.period):
            try:
                date = pd.to_datetime(obs.period)
                records.append({
                    'date': date,
                    'rate': obs.value
                })
            except Exception as e:
                logger.warning(f"Skipping invalid observation: {obs.period} - {e}")
        
        return pd.DataFrame(records)
    
    def _prepare_interest_rate_data(self, data: InterestRateData) -> pd.DataFrame:
        """Convert interest rate data to DataFrame for plotting"""
        records = []
        
        logger.info(f"Preparing chart data from {len(data.observations)} observations")
        
        for obs in sorted(data.observations, key=lambda x: x.period):
            try:
                date = pd.to_datetime(obs.period)
                records.append({
                    'date': date,
                    'rate': obs.value
                })
            except Exception as e:
                logger.warning(f"Skipping invalid observation: {obs.period} - {e}")
        
        df = pd.DataFrame(records)
        logger.info(f"Chart DataFrame created with {len(df)} rows")
        if len(df) > 0:
            logger.info(f"Sample values: {df['rate'].head().tolist()}")
            logger.info(f"Value range: {df['rate'].min():.2f} to {df['rate'].max():.2f}")
        
        return df
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with a message"""
        fig = go.Figure()
        
        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text=message,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
