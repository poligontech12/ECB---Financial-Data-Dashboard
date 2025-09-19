"""
Authentication middleware for Flask routes
"""
from functools import wraps
from flask import request, session, jsonify, redirect, url_for
from typing import Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

def require_authentication(f):
    """
    Decorator to require authentication for Flask routes
    Checks for valid session token in request headers or session
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get auth service instance (will be injected by app)
            auth_service = getattr(require_authentication, 'auth_service', None)
            if not auth_service:
                logger.error("Authentication service not initialized")
                return _handle_unauthenticated_request()
            
            # Check for session token in different places
            session_token = _get_session_token()
            
            if not session_token:
                logger.debug("No session token found in request")
                return _handle_unauthenticated_request()
            
            # Validate session
            if not auth_service.is_session_valid(session_token):
                logger.debug(f"Invalid session token: {session_token[:8]}...")
                return _handle_unauthenticated_request()
            
            # Session is valid, proceed with request
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return _handle_unauthenticated_request()
    
    return decorated_function

def _get_session_token() -> Optional[str]:
    """
    Get session token from request headers, cookies, or session
    
    Returns:
        Session token if found, None otherwise
    """
    # Check Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    
    # Check session cookie
    if 'session_token' in session:
        return session['session_token']
    
    # Check custom header
    session_token = request.headers.get('X-Session-Token')
    if session_token:
        return session_token
    
    # Check cookie directly
    session_token = request.cookies.get('session_token')
    if session_token:
        return session_token
    
    return None

def _handle_unauthenticated_request():
    """
    Handle requests that are not authenticated
    Returns appropriate response based on request type
    """
    # Check if this is an API request
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Authentication required',
            'redirect': '/auth/login'
        }), 401
    
    # For web requests, redirect to login page
    return redirect(url_for('auth_login'))

def inject_auth_service(auth_service):
    """
    Inject authentication service into middleware
    This should be called during app initialization
    """
    require_authentication.auth_service = auth_service
    logger.info("Authentication service injected into middleware")

def get_current_session_token() -> Optional[str]:
    """
    Get current session token from request context
    Useful for services that need to access session info
    """
    return _get_session_token()

def clear_session():
    """
    Clear session data
    """
    if 'session_token' in session:
        del session['session_token']
    
    # Also attempt to clear from auth service if available
    auth_service = getattr(require_authentication, 'auth_service', None)
    if auth_service:
        session_token = _get_session_token()
        if session_token:
            auth_service.destroy_session(session_token)