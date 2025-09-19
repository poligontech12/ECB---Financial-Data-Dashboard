/*
 * ECB Financial Data Visualizer - Authentication JavaScript
 * Handles PIN entry, validation, and session management
 */

console.log('🔒 ECB Authentication - Loading');

const ECBAuth = {
    
    // Configuration
    config: {
        maxPinLength: 6,
        redirectDelay: 1000,
        sessionCheckInterval: 300000, // 5 minutes
        dashboardUrl: '/',
        apiBaseUrl: '/auth'
    },

    // Initialize authentication interface
    init: function() {
        console.log('🔒 ECB Authentication - Initializing');
        
        // Bind event listeners
        this.bindEvents();
        
        // Focus on PIN input
        const pinInput = document.getElementById('pinInput');
        if (pinInput) {
            pinInput.focus();
        }
        
        // Check if user is already authenticated
        this.checkExistingSession();
        
        console.log('✅ Authentication interface ready');
    },

    // Bind event listeners
    bindEvents: function() {
        const pinForm = document.getElementById('pinForm');
        const pinInput = document.getElementById('pinInput');

        // Handle form submission
        if (pinForm) {
            pinForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handlePinSubmission();
            });
        }

        // Handle PIN input formatting
        if (pinInput) {
            pinInput.addEventListener('input', (e) => {
                this.formatPinInput(e.target);
            });

            pinInput.addEventListener('keypress', (e) => {
                // Only allow numbers
                if (!/[0-9]/.test(e.key) && !['Backspace', 'Delete', 'Tab', 'Enter'].includes(e.key)) {
                    e.preventDefault();
                }

                // Submit on Enter
                if (e.key === 'Enter') {
                    this.handlePinSubmission();
                }
            });

            pinInput.addEventListener('paste', (e) => {
                e.preventDefault();
                const paste = (e.clipboardData || window.clipboardData).getData('text');
                const numbers = paste.replace(/\D/g, '').substring(0, this.config.maxPinLength);
                pinInput.value = numbers;
                this.formatPinInput(pinInput);
            });
        }
    },

    // Format PIN input
    formatPinInput: function(input) {
        // Remove non-numeric characters
        let value = input.value.replace(/\D/g, '');
        
        // Limit to 6 digits
        value = value.substring(0, this.config.maxPinLength);
        
        // Update input value
        input.value = value;
        
        // Update validation state
        this.updateValidationState(input);
    },

    // Update validation state
    updateValidationState: function(input) {
        const isValid = input.value.length === this.config.maxPinLength;
        
        if (isValid) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            input.classList.remove('is-valid');
            if (input.value.length > 0) {
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        }
    },

    // Handle PIN submission
    handlePinSubmission: async function() {
        const pinInput = document.getElementById('pinInput');
        const pin = pinInput.value.trim();
        
        // Validate PIN format
        if (pin.length !== this.config.maxPinLength || !/^\d{6}$/.test(pin)) {
            this.showAlert('Please enter a valid 6-digit PIN', 'danger');
            pinInput.focus();
            return;
        }

        // Show loading state
        this.setLoadingState(true);

        try {
            // Submit PIN for validation
            const response = await fetch(`${this.config.apiBaseUrl}/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ pin: pin })
            });

            const data = await response.json();

            if (data.success) {
                // Store session token
                if (data.session_token) {
                    this.storeSessionToken(data.session_token);
                }

                // Show success message
                this.showAlert('Access granted! Redirecting to dashboard...', 'success');
                
                // Redirect to dashboard
                setTimeout(() => {
                    window.location.href = this.config.dashboardUrl;
                }, this.config.redirectDelay);

            } else {
                // Show error message
                this.showAlert(data.error || 'Invalid PIN. Please try again.', 'danger');
                
                // Clear and focus PIN input
                pinInput.value = '';
                pinInput.classList.remove('is-valid', 'is-invalid');
                pinInput.focus();
            }

        } catch (error) {
            console.error('Authentication error:', error);
            this.showAlert('Connection error. Please try again.', 'danger');
            
            // Clear and focus PIN input
            pinInput.value = '';
            pinInput.classList.remove('is-valid', 'is-invalid');
            pinInput.focus();
        } finally {
            this.setLoadingState(false);
        }
    },

    // Set loading state
    setLoadingState: function(loading) {
        const loginBtn = document.getElementById('loginBtn');
        const loginBtnText = document.getElementById('loginBtnText');
        const loginSpinner = document.getElementById('loginSpinner');
        const pinInput = document.getElementById('pinInput');

        if (loading) {
            loginBtn.disabled = true;
            loginBtnText.textContent = 'Authenticating...';
            loginSpinner.classList.remove('d-none');
            pinInput.disabled = true;
        } else {
            loginBtn.disabled = false;
            loginBtnText.textContent = 'Access Dashboard';
            loginSpinner.classList.add('d-none');
            pinInput.disabled = false;
        }
    },

    // Show alert message
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
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                const alert = alertArea.querySelector('.alert');
                if (alert) {
                    alert.remove();
                }
            }, 3000);
        }
    },

    // Store session token
    storeSessionToken: function(token) {
        // Store in sessionStorage for security
        sessionStorage.setItem('session_token', token);
        
        // Also set as cookie for server-side access
        document.cookie = `session_token=${token}; path=/; secure; samesite=strict`;
    },

    // Get stored session token
    getSessionToken: function() {
        return sessionStorage.getItem('session_token') || this.getCookie('session_token');
    },

    // Get cookie value
    getCookie: function(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },

    // Check for existing session
    checkExistingSession: async function() {
        const token = this.getSessionToken();
        if (!token) return;

        try {
            const response = await fetch(`${this.config.apiBaseUrl}/check-session`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.valid) {
                    // Session is still valid, redirect to dashboard
                    this.showAlert('Session found. Redirecting to dashboard...', 'info');
                    setTimeout(() => {
                        window.location.href = this.config.dashboardUrl;
                    }, 1000);
                }
            }
        } catch (error) {
            console.log('No existing session found');
        }
    },

    // Clear session
    clearSession: function() {
        sessionStorage.removeItem('session_token');
        document.cookie = 'session_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    }
};

// Session management for authenticated pages
const ECBSession = {
    
    // Check session periodically
    startSessionCheck: function() {
        setInterval(() => {
            this.checkSession();
        }, ECBAuth.config.sessionCheckInterval);
    },

    // Check if session is still valid
    checkSession: async function() {
        const token = ECBAuth.getSessionToken();
        if (!token) {
            this.handleSessionExpired();
            return;
        }

        try {
            const response = await fetch('/auth/check-session', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Session check failed');
            }

            const data = await response.json();
            if (!data.valid) {
                this.handleSessionExpired();
            }
        } catch (error) {
            console.error('Session check error:', error);
            this.handleSessionExpired();
        }
    },

    // Handle session expiration
    handleSessionExpired: function() {
        ECBAuth.clearSession();
        alert('Your session has expired. Please log in again.');
        window.location.href = '/auth/login';
    },

    // Logout
    logout: async function() {
        const token = ECBAuth.getSessionToken();
        
        if (token) {
            try {
                await fetch('/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
            } catch (error) {
                console.error('Logout error:', error);
            }
        }
        
        ECBAuth.clearSession();
        window.location.href = '/auth/login';
    }
};

// Auto-initialize based on page
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('pinForm')) {
        // Login page
        ECBAuth.init();
    } else if (document.body.classList.contains('authenticated')) {
        // Authenticated page
        ECBSession.startSessionCheck();
    }
});

// Export for global access
window.ECBAuth = ECBAuth;
window.ECBSession = ECBSession;

console.log('🔒 Authentication JavaScript loaded successfully');