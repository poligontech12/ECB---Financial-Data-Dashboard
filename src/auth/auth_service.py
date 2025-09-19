"""
Authentication service for ECB Financial Data Visualizer
Handles PIN validation and secure session management
"""
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from utils.config import get_config
from utils.logging_config import get_logger
from utils.pin_hasher import PINHasher

logger = get_logger(__name__)

class AuthService:
    """Authentication service with bcrypt PIN validation"""
    
    def __init__(self):
        self.config = get_config()
        self.security_config = self.config["security"]
        self.pin_hash = self.security_config["pin_hash"]
        self.session_timeout = self.security_config["session_timeout_minutes"]
        self.max_attempts = self.security_config["max_login_attempts"]
        self.lockout_duration = self.security_config["lockout_duration_minutes"]
        
        # In-memory session storage (cleared on restart)
        self.active_sessions: Dict[str, dict] = {}
        self.failed_attempts: Dict[str, dict] = {}
        
        logger.info("Authentication service initialized with secure PIN hashing")
    
    def validate_pin(self, pin: str, client_ip: str = "unknown") -> Tuple[bool, str]:
        """
        Validate PIN against bcrypt hash
        
        Args:
            pin: 6-digit PIN to validate
            client_ip: Client IP for rate limiting
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if client is locked out
            if self._is_client_locked_out(client_ip):
                remaining_time = self._get_lockout_remaining_time(client_ip)
                logger.warning(f"Login attempt from locked out client {client_ip}")
                return False, f"Too many failed attempts. Try again in {remaining_time} minutes."

            # Validate PIN format
            if not pin or len(pin) != 6 or not pin.isdigit():
                self._record_failed_attempt(client_ip)
                logger.warning(f"Invalid PIN format from {client_ip}")
                return False, "PIN must be exactly 6 digits"

            # Verify PIN against bcrypt hash
            if PINHasher.verify_pin(pin, self.pin_hash):
                self._clear_failed_attempts(client_ip)
                logger.info(f"Successful PIN validation from {client_ip}")
                return True, ""
            else:
                self._record_failed_attempt(client_ip)
                attempts_left = self.max_attempts - self.failed_attempts[client_ip]["count"]
                logger.warning(f"Failed PIN validation from {client_ip}. Attempts left: {attempts_left}")
                return False, f"Invalid PIN. {attempts_left} attempts remaining."
                
        except Exception as e:
            logger.error(f"Error validating PIN: {e}")
            return False, "Authentication error. Please try again."
    
    def create_session(self, client_ip: str = "unknown") -> str:
        """
        Create a new authenticated session
        
        Args:
            client_ip: Client IP address for logging
            
        Returns:
            Session token
        """
        try:
            # Generate secure session token
            session_token = secrets.token_urlsafe(32)
            
            # Create session data
            session_data = {
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "client_ip": client_ip,
                "authenticated": True
            }
            
            # Store session
            self.active_sessions[session_token] = session_data
            
            logger.info(f"Created session {session_token[:8]}... for {client_ip}")
            return session_token
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def is_session_valid(self, session_token: str) -> bool:
        """
        Check if session is valid and not expired
        
        Args:
            session_token: Session token to validate
            
        Returns:
            True if session is valid
        """
        try:
            if not session_token or session_token not in self.active_sessions:
                return False
            
            session_data = self.active_sessions[session_token]
            
            # Check if session is expired
            last_activity = session_data["last_activity"]
            timeout_delta = timedelta(minutes=self.session_timeout)
            
            if datetime.now() - last_activity > timeout_delta:
                self._destroy_session(session_token)
                logger.info(f"Session {session_token[:8]}... expired")
                return False
            
            # Update last activity
            session_data["last_activity"] = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    def destroy_session(self, session_token: str) -> bool:
        """
        Destroy a session (logout)
        
        Args:
            session_token: Session token to destroy
            
        Returns:
            True if session was destroyed
        """
        return self._destroy_session(session_token)
    
    def _destroy_session(self, session_token: str) -> bool:
        """Internal method to destroy session"""
        try:
            if session_token in self.active_sessions:
                client_ip = self.active_sessions[session_token].get("client_ip", "unknown")
                del self.active_sessions[session_token]
                logger.info(f"Destroyed session {session_token[:8]}... for {client_ip}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error destroying session: {e}")
            return False
    
    def _is_client_locked_out(self, client_ip: str) -> bool:
        """Check if client is locked out due to failed attempts"""
        if client_ip not in self.failed_attempts:
            return False
        
        attempt_data = self.failed_attempts[client_ip]
        
        # Check if lockout period has expired
        if "locked_until" in attempt_data:
            if datetime.now() > attempt_data["locked_until"]:
                # Lockout expired, clear failed attempts
                del self.failed_attempts[client_ip]
                return False
            return True
        
        return False
    
    def _get_lockout_remaining_time(self, client_ip: str) -> int:
        """Get remaining lockout time in minutes"""
        if client_ip not in self.failed_attempts or "locked_until" not in self.failed_attempts[client_ip]:
            return 0
        
        locked_until = self.failed_attempts[client_ip]["locked_until"]
        remaining = locked_until - datetime.now()
        return max(0, int(remaining.total_seconds() / 60))
    
    def _record_failed_attempt(self, client_ip: str):
        """Record a failed login attempt"""
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = {"count": 0, "first_attempt": datetime.now()}
        
        self.failed_attempts[client_ip]["count"] += 1
        self.failed_attempts[client_ip]["last_attempt"] = datetime.now()
        
        # Check if client should be locked out
        if self.failed_attempts[client_ip]["count"] >= self.max_attempts:
            lockout_until = datetime.now() + timedelta(minutes=self.lockout_duration)
            self.failed_attempts[client_ip]["locked_until"] = lockout_until
            logger.warning(f"Client {client_ip} locked out until {lockout_until}")
    
    def _clear_failed_attempts(self, client_ip: str):
        """Clear failed attempts for successful login"""
        if client_ip in self.failed_attempts:
            del self.failed_attempts[client_ip]
    
    def get_session_info(self, session_token: str) -> Optional[dict]:
        """Get information about a session"""
        if session_token in self.active_sessions:
            session_data = self.active_sessions[session_token].copy()
            # Convert datetime objects to strings for JSON serialization
            session_data["created_at"] = session_data["created_at"].isoformat()
            session_data["last_activity"] = session_data["last_activity"].isoformat()
            return session_data
        return None
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (can be called periodically)"""
        try:
            current_time = datetime.now()
            timeout_delta = timedelta(minutes=self.session_timeout)
            expired_sessions = []
            
            for token, session_data in self.active_sessions.items():
                if current_time - session_data["last_activity"] > timeout_delta:
                    expired_sessions.append(token)
            
            for token in expired_sessions:
                self._destroy_session(token)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions"""
        return len(self.active_sessions)