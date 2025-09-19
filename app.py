"""
ECB Financial Data Visualizer - Flask Application
Workshop-ready implementation for financial data visualization with security

This Flask application preserves all existing backend services while providing
a modern, flexible web interface with PIN-based authentication and database encryption.
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import sys
import os
import traceback
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from utils.config import get_config, STREAMLIT_CONFIG
    from utils.logging_config import get_logger
    from database.database import init_database, db_manager
    from services.data_service import DataService
    from api.ecb_client import ECBClient
    from auth.auth_service import AuthService
    from auth.crypto_service import DatabaseCryptoService
    from auth.middleware import require_authentication, inject_auth_service, get_current_session_token, clear_session
    import plotly
    import plotly.utils
    import json
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed and src/ directory is accessible")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config = get_config()
app.config['SECRET_KEY'] = config["security"]["session_secret_key"]

# Setup logging
logger = get_logger(__name__)

# Global services (initialized on first request)
data_service = None
ecb_client = None
auth_service = None
crypto_service = None
database_initialized = False

def plotly_to_json(fig):
    """Convert Plotly figure to JSON safely"""
    try:
        # Use fig.to_dict() directly to avoid serialization issues
        chart_dict = fig.to_dict()
        
        # Ensure data arrays are properly formatted
        if 'data' in chart_dict and len(chart_dict['data']) > 0:
            for trace in chart_dict['data']:
                # Convert any string arrays back to proper arrays
                if 'x' in trace and isinstance(trace['x'], str):
                    trace['x'] = trace['x'].split()
                if 'y' in trace and isinstance(trace['y'], str):
                    trace['y'] = [float(val) for val in trace['y'].split()]
                
                # Ensure numeric arrays are lists, not numpy arrays
                if 'x' in trace and hasattr(trace['x'], 'tolist'):
                    trace['x'] = trace['x'].tolist()
                if 'y' in trace and hasattr(trace['y'], 'tolist'):
                    trace['y'] = trace['y'].tolist()
        
        # Debug logging for chart data
        if 'data' in chart_dict and len(chart_dict['data']) > 0:
            trace = chart_dict['data'][0]
            if 'y' in trace:
                y_values = trace['y']
                logger.debug(f"Chart conversion - Y values count: {len(y_values)}")
                logger.debug(f"Chart conversion - Y values type: {type(y_values)}")
                if isinstance(y_values, list) and len(y_values) > 0:
                    logger.debug(f"Chart conversion - First 3 Y values: {y_values[:3]}")
                    logger.debug(f"Chart conversion - Last 3 Y values: {y_values[-3:]}")
                    logger.debug(f"Chart conversion - Min Y: {min(y_values)}, Max Y: {max(y_values)}")
        
        return chart_dict
    except Exception as e:
        logger.error(f"Chart conversion failed: {e}")
        # Fallback to basic dict conversion
        return fig.to_dict()

def initialize_services():
    """Initialize services once"""
    global data_service, ecb_client, auth_service, crypto_service, database_initialized
    
    if not database_initialized:
        try:
            logger.info("Initializing ECB services with security...")
            
            # Initialize authentication and encryption services
            auth_service = AuthService()
            crypto_service = DatabaseCryptoService()
            
            # Inject auth service into middleware
            inject_auth_service(auth_service)
            
            # Check if database needs to be decrypted
            if crypto_service.is_database_encrypted():
                logger.info("Database is encrypted - requires PIN for access")
                # Database will be decrypted when user provides PIN
                return True
            else:
                # Database is not encrypted, proceed with normal initialization
                return initialize_database_and_services()
                
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            return False
    
    return True

def initialize_database_and_services():
    """Initialize database and business services after authentication"""
    global data_service, ecb_client, database_initialized
    
    try:
        # Initialize database
        init_success = init_database()
        if not init_success:
            logger.error("Database initialization failed!")
            return False
        
        # Initialize business services
        data_service = DataService()
        ecb_client = ECBClient()
        
        database_initialized = True
        logger.info("Database and services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database and services initialization failed: {e}")
        return False

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route('/auth/login')
def auth_login():
    """PIN entry page"""
    try:
        # Initialize auth services
        if not initialize_services():
            return render_template('error.html', 
                                 error="Service initialization failed"), 500
        
        return render_template('pin_entry.html')
    
    except Exception as e:
        logger.error(f"Auth login error: {e}")
        return render_template('error.html', 
                             error=f"Authentication error: {str(e)}"), 500

@app.route('/auth/validate', methods=['POST'])
def auth_validate():
    """Validate PIN and create session"""
    try:
        if not auth_service:
            return jsonify({
                'success': False,
                'error': 'Authentication service not available'
            }), 500
        
        data = request.get_json()
        pin = data.get('pin', '').strip()
        client_ip = request.remote_addr or 'unknown'
        
        # Validate PIN
        is_valid, error_message = auth_service.validate_pin(pin, client_ip)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 401
        
        # PIN is valid, now decrypt database if needed
        if crypto_service.is_database_encrypted():
            decrypt_success, decrypt_error = crypto_service.decrypt_database(pin)
            if not decrypt_success:
                logger.error(f"Database decryption failed: {decrypt_error}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid PIN - cannot access secure data'
                }), 401
        
        # Initialize database and services now that we have access
        if not database_initialized:
            if not initialize_database_and_services():
                crypto_service.lock_database()  # Lock database again on failure
                return jsonify({
                    'success': False,
                    'error': 'Failed to initialize application services'
                }), 500
        
        # Create session
        session_token = auth_service.create_session(client_ip)
        
        # Store session token in Flask session for cookie-based access
        session['session_token'] = session_token
        session['authenticated'] = True
        
        logger.info(f"Successful authentication from {client_ip}")
        
        return jsonify({
            'success': True,
            'session_token': session_token,
            'message': 'Authentication successful'
        })
        
    except Exception as e:
        logger.error(f"Auth validation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Authentication error occurred'
        }), 500

@app.route('/auth/check-session')
def auth_check_session():
    """Check if current session is valid"""
    try:
        if not auth_service:
            return jsonify({'valid': False}), 401
        
        # Get session token from request
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header[7:]
        else:
            session_token = session.get('session_token')
        
        if not session_token:
            return jsonify({'valid': False}), 401
        
        # Check session validity
        is_valid = auth_service.is_session_valid(session_token)
        
        if is_valid:
            session_info = auth_service.get_session_info(session_token)
            return jsonify({
                'valid': True,
                'session_info': session_info
            })
        else:
            clear_session()
            return jsonify({'valid': False}), 401
            
    except Exception as e:
        logger.error(f"Session check error: {e}")
        return jsonify({'valid': False}), 500

@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    """Logout and destroy session"""
    try:
        if auth_service:
            # Get session token
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                session_token = auth_header[7:]
            else:
                session_token = session.get('session_token')
            
            if session_token:
                auth_service.destroy_session(session_token)
        
        # Clear Flask session
        clear_session()
        
        # Lock database
        if crypto_service:
            crypto_service.lock_database()
        
        logger.info("User logged out successfully")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'Logout error occurred'
        }), 500

# =============================================================================
# PROTECTED APPLICATION ROUTES
# =============================================================================

@app.route('/')
@require_authentication
def dashboard():
    """Main dashboard page"""
    try:
        # Ensure services are initialized
        if not initialize_services():
            return render_template('error.html', 
                                 error="Service initialization failed"), 500
        
        return render_template('dashboard.html')
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('error.html', 
                             error=f"Dashboard error: {str(e)}"), 500

@app.route('/exchange-rates')
@require_authentication
def exchange_rates_page():
    """Dedicated EUR/USD exchange rates page"""
    try:
        # Ensure services are initialized
        if not initialize_services():
            return render_template('error.html', 
                                 error="Service initialization failed"), 500
        
        return render_template('exchange_rates.html')
    
    except Exception as e:
        logger.error(f"Exchange rates page error: {e}")
        return render_template('error.html', 
                             error=f"Exchange rates page error: {str(e)}"), 500

@app.route('/inflation')
@require_authentication
def inflation_page():
    """Dedicated HICP inflation page"""
    try:
        # Ensure services are initialized
        if not initialize_services():
            return render_template('error.html', 
                                 error="Service initialization failed"), 500
        
        return render_template('inflation.html')
    
    except Exception as e:
        logger.error(f"Inflation page error: {e}")
        return render_template('error.html', 
                             error=f"Inflation page error: {str(e)}"), 500

@app.route('/interest-rates')
@require_authentication
def interest_rates_page():
    """Dedicated ECB interest rates page"""
    try:
        # Ensure services are initialized
        if not initialize_services():
            return render_template('error.html', 
                                 error="Service initialization failed"), 500
        
        return render_template('interest_rates.html')
    
    except Exception as e:
        logger.error(f"Interest rates page error: {e}")
        return render_template('error.html', 
                             error=f"Interest rates page error: {str(e)}"), 500

@app.route('/api/test')
@require_authentication
def api_test():
    """Test API endpoint to verify services"""
    try:
        if not initialize_services():
            return jsonify({'error': 'Services not initialized'}), 500
        
        # Test ECB client connection
        connection_ok = ecb_client.test_connection() if hasattr(ecb_client, 'test_connection') else True
        
        return jsonify({
            'status': 'success',
            'message': 'ECB Flask API is running',
            'services': {
                'data_service': data_service is not None,
                'ecb_client': ecb_client is not None,
                'database': True,  # If we got here, DB is working
                'api_connection': connection_ok
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"API test error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/exchange-rates')
@require_authentication
def api_exchange_rates():
    """Get exchange rate chart data"""
    try:
        if not initialize_services():
            return jsonify({'error': 'Services not initialized'}), 500
        
        logger.info("Fetching exchange rate data for API")
        data = data_service.get_exchange_rate_data()
        
        if data and data.observations:
            # Import chart service here to avoid circular imports
            from services.chart_service import ChartService
            chart_service = ChartService()
            
            # Generate chart
            fig = chart_service.create_exchange_rate_chart(data)
            
            # Convert to JSON format for frontend
            chart_json = plotly_to_json(fig)
            
            return jsonify({
                'success': True,
                'chart': chart_json,
                'latest_rate': data.latest_value,
                'data_points': len(data.observations),
                'last_updated': data.metadata.last_updated.isoformat() if data.metadata.last_updated else None,
                'series_title': data.metadata.title,
                'unit': data.metadata.unit or 'EUR per USD'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No exchange rate data available',
                'message': 'Try refreshing the data first'
            })
    
    except Exception as e:
        logger.error(f"Exchange rates API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Exchange rates API error: {str(e)}'
        }), 500

@app.route('/api/inflation')
@require_authentication
def api_inflation():
    """Get inflation chart data"""
    try:
        if not initialize_services():
            return jsonify({'error': 'Services not initialized'}), 500
        
        logger.info("Fetching inflation data for API")
        data = data_service.get_inflation_data()
        
        if data and data.observations:
            # Import chart service here to avoid circular imports
            from services.chart_service import ChartService
            chart_service = ChartService()
            
            # Generate chart
            fig = chart_service.create_inflation_chart(data)
            
            # Convert to JSON format for frontend
            chart_json = plotly_to_json(fig)
            
            return jsonify({
                'success': True,
                'chart': chart_json,
                'latest_rate': data.latest_value,
                'target_deviation': data.target_deviation,
                'data_points': len(data.observations),
                'last_updated': data.metadata.last_updated.isoformat() if data.metadata.last_updated else None,
                'series_title': data.metadata.title,
                'unit': data.metadata.unit or 'Percent'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No inflation data available',
                'message': 'Try refreshing the data first'
            })
    
    except Exception as e:
        logger.error(f"Inflation API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Inflation API error: {str(e)}'
        }), 500

@app.route('/api/refresh-data')
@require_authentication
def api_refresh_data():
    """Refresh all data from ECB API"""
    try:
        if not initialize_services():
            return jsonify({'error': 'Services not initialized'}), 500
        
        logger.info("Refreshing all data from ECB API")
        result = data_service.refresh_all_data(force=True)
        
        return jsonify({
            'success': True,
            'total_series': result.total_series,
            'successful': result.successful,
            'failed': result.failed,
            'duration': str(result.end_time - result.start_time)
        })
        
    except Exception as e:
        logger.error(f"Data refresh API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Data refresh error: {str(e)}'
        }), 500

@app.route('/api/interest-rates')
@require_authentication
def api_interest_rates():
    """Get interest rate chart data"""
    try:
        if not initialize_services():
            return jsonify({'error': 'Services not initialized'}), 500
        
        logger.info("Fetching interest rate data for API")
        data = data_service.get_interest_rate_data()
        
        if data and data.observations:
            # Debug: Log actual data values
            logger.info(f"Interest rate data - Observations: {len(data.observations)}")
            logger.info(f"Interest rate data - Latest value: {data.latest_value}")
            logger.info(f"Interest rate data - Series title: {data.metadata.title if data.metadata else 'N/A'}")
            
            # Log recent values for debugging
            recent_values = sorted(data.observations, key=lambda x: x.period)[-5:]
            for obs in recent_values:
                    logger.debug(f"Interest rate observation: {obs.period} = {obs.value}%")
            
            # Import chart service here to avoid circular imports
            from services.chart_service import ChartService
            chart_service = ChartService()
            
            # Generate chart
            fig = chart_service.create_interest_rate_chart(data)
            
            # Convert to JSON format for frontend
            chart_json = plotly_to_json(fig)
            
            return jsonify({
                'success': True,
                'chart': chart_json,
                'latest_rate': data.latest_value,
                'data_points': len(data.observations),
                'last_updated': data.metadata.last_updated.isoformat() if data.metadata.last_updated else None,
                'series_title': data.metadata.title,
                'unit': data.metadata.unit or 'Percent'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No interest rate data available',
                'message': 'Try refreshing the data first'
            })
    
    except Exception as e:
        logger.error(f"Interest rates API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Interest rates API error: {str(e)}'
        }), 500

@app.route('/api/refresh/<data_type>', methods=['POST', 'GET'])
@require_authentication
def refresh_data(data_type):
    """Refresh specific data type"""
    try:
        if not initialize_services():
            return jsonify({'error': 'Services not initialized'}), 500
        
        logger.info(f"Refreshing data for: {data_type}")
        
        if data_type == 'exchange-rates':
            result = ecb_client.fetch_exchange_rates()
        elif data_type == 'inflation':
            result = ecb_client.fetch_inflation_data()
        elif data_type == 'interest-rates':
            result = ecb_client.fetch_interest_rates()
        else:
            return jsonify({
                'success': False,
                'error': f'Invalid data type: {data_type}',
                'valid_types': ['exchange-rates', 'inflation', 'interest-rates']
            }), 400
        
        if result.success:
            # Store the data if fetch was successful
            if result.data:
                data_service._store_series_data(result.data)
            
            return jsonify({
                'success': True,
                'message': f'{data_type} data refreshed successfully',
                'observations_count': result.observations_count,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': result.error_message,
                'timestamp': datetime.now().isoformat()
            })
    
    except Exception as e:
        logger.error(f"Data refresh error for {data_type}: {e}")
        return jsonify({
            'success': False,
            'error': f'Data refresh failed: {str(e)}'
        }), 500

@app.route('/api/refresh-all', methods=['POST'])
@require_authentication
def refresh_all_data():
    """Refresh all data types"""
    try:
        if not initialize_services():
            return jsonify({'error': 'Services not initialized'}), 500
        
        logger.info("Refreshing all data")
        
        # Use the existing refresh_all_data method
        refresh_result = data_service.refresh_all_data(force=True)
        
        return jsonify({
            'success': refresh_result.successful > 0,
            'total_series': refresh_result.total_series,
            'successful': refresh_result.successful,
            'failed': refresh_result.failed,
            'duration_seconds': refresh_result.duration_seconds,
            'results': [
                {
                    'series_key': r.series_key,
                    'success': r.success,
                    'error_message': r.error_message,
                    'observations_count': r.observations_count
                }
                for r in refresh_result.results
            ],
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Refresh all data error: {e}")
        return jsonify({
            'success': False,
            'error': f'Refresh all failed: {str(e)}'
        }), 500

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'application': 'ECB Financial Data Visualizer',
        'version': '2.0.0-flask',
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    """Custom 404 error handler"""
    return render_template('error.html', 
                         error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 error handler"""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', 
                         error="Internal server error"), 500

if __name__ == '__main__':
    print("🏛️  ECB Financial Data Visualizer - Flask Edition")
    print("🚀 Starting application...")
    print("📊 Workshop-ready financial data visualization")
    print("=" * 50)
    
    # Initialize services on startup
    if initialize_services():
        print("✅ Services initialized successfully")
        print("🌐 Access dashboard at: http://localhost:5000")
        print("🔧 API test at: http://localhost:5000/api/test")
        print("=" * 50)
        
        # Run Flask development server
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=False  # Prevent double initialization
        )
    else:
        print("❌ Service initialization failed")
        print("🔍 Check logs for details")
        sys.exit(1)
