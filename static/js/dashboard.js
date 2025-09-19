/* 
 * ECB Financial Data Visualizer - Dashboard JavaScript
 * Flask Edition - Chart Management and API Integration
 */

console.log('🏛️ ECB Financial Data Visualizer - Dashboard.js Loading');

// Configuration
const CHART_CONFIG = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    scrollZoom: false,
    doubleClick: 'reset+autosize'
};

// Utility Functions
const ECBDashboard = {
    
    // Show alert messages
    showAlert: function(message, type = 'info') {
        const alertArea = document.getElementById('alertArea');
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'danger' ? 'exclamation-triangle' : 'info'}-circle me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        alertArea.innerHTML = alertHtml;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            const alert = alertArea.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    },

    // Show loading state
    showLoading: function(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">${message}</span>
                </div>
                <p class="mt-2 text-muted">${message}</p>
            </div>
        `;
    },

    // Get chart and info IDs
    getChartId: function(dataType) {
        const mapping = {
            'exchange-rates': 'exchange-chart',
            'inflation': 'inflation-chart',
            'interest-rates': 'interest-chart'
        };
        return mapping[dataType] || `${dataType}-chart`;
    },

    getInfoId: function(dataType) {
        const mapping = {
            'exchange-rates': 'exchange-info',
            'inflation': 'inflation-info',
            'interest-rates': 'interest-info'
        };
        return mapping[dataType] || `${dataType}-info`;
    },

    // Create info HTML based on data type
    createInfoHtml: function(dataType, data) {
        if (dataType === 'exchange-rates') {
            return `
                <div class="row text-center">
                    <div class="col-4">
                        <div class="metric-label">Latest Rate</div>
                        <div class="metric-value">${data.latest_rate?.toFixed(4) || 'N/A'}</div>
                    </div>
                    <div class="col-4">
                        <div class="metric-label">Data Points</div>
                        <div class="metric-value">${data.data_points || 0}</div>
                    </div>
                    <div class="col-4">
                        <div class="metric-label">Last Updated</div>
                        <div class="metric-value" style="font-size: 0.9rem;">
                            ${data.last_updated ? new Date(data.last_updated).toLocaleDateString() : 'N/A'}
                        </div>
                    </div>
                </div>
            `;
        } else if (dataType === 'inflation') {
            const deviationClass = data.target_deviation > 0 ? 'change-negative' : 'change-positive';
            return `
                <div class="row text-center">
                    <div class="col-4">
                        <div class="metric-label">Current Rate</div>
                        <div class="metric-value">${data.latest_rate?.toFixed(1) || 'N/A'}%</div>
                    </div>
                    <div class="col-4">
                        <div class="metric-label">vs ECB Target (2%)</div>
                        <div class="metric-value ${deviationClass}">
                            ${data.target_deviation > 0 ? '+' : ''}${data.target_deviation?.toFixed(1) || 'N/A'}%
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="metric-label">Data Points</div>
                        <div class="metric-value">${data.data_points || 0}</div>
                    </div>
                </div>
            `;
        } else if (dataType === 'interest-rates') {
            return `
                <div class="row text-center">
                    <div class="col-4">
                        <div class="metric-label">Current Rate</div>
                        <div class="metric-value">${data.latest_rate?.toFixed(2) || 'N/A'}%</div>
                    </div>
                    <div class="col-4">
                        <div class="metric-label">Data Points</div>
                        <div class="metric-value">${data.data_points || 0}</div>
                    </div>
                    <div class="col-4">
                        <div class="metric-label">Last Updated</div>
                        <div class="metric-value" style="font-size: 0.9rem;">
                            ${data.last_updated ? new Date(data.last_updated).toLocaleDateString() : 'N/A'}
                        </div>
                    </div>
                </div>
            `;
        }
        return '';
    },

    // Load individual chart
    loadChart: async function(dataType, chartId, infoId) {
        try {
            console.log(`Loading chart: ${dataType}`);
            this.showLoading(chartId, `Loading ${dataType} data...`);
            
            const response = await fetch(`/api/${dataType}`);
            const data = await response.json();
            
            if (!data.success) {
                document.getElementById(chartId).innerHTML = 
                    `<div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${data.error || 'No data available'}
                        <br><small>${data.message || 'Try refreshing the data first'}</small>
                    </div>`;
                return;
            }
            
            // Render Plotly chart
            console.log(`Rendering chart for ${dataType}`);
            await Plotly.newPlot(chartId, data.chart.data, data.chart.layout, CHART_CONFIG);
            
            // Show info
            const infoHtml = this.createInfoHtml(dataType, data);
            document.getElementById(infoId).innerHTML = infoHtml;
            
            console.log(`Chart loaded successfully: ${dataType}`);
            
        } catch (error) {
            console.error(`Error loading chart ${dataType}:`, error);
            document.getElementById(chartId).innerHTML = 
                `<div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error loading chart: ${error.message}
                </div>`;
        }
    },

    // Initialize dashboard
    init: function() {
        console.log('🏛️ ECB Financial Data Visualizer - Dashboard Initializing');
        
        // Test API on page load
        this.testAPI();
        
        // Load all charts after brief delay
        setTimeout(() => {
            this.loadChart('exchange-rates', 'exchange-chart', 'exchange-info');
            this.loadChart('inflation', 'inflation-chart', 'inflation-info');
            this.loadChart('interest-rates', 'interest-chart', 'interest-info');
        }, 1000);
        
        console.log('📊 Dashboard initialization complete');
    }
};

// Export for global access
window.ECBDashboard = ECBDashboard;

console.log('📊 Dashboard.js loaded successfully');
