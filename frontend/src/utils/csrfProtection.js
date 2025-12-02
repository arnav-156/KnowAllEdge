/**
 * CSRF Protection Utility
 * Generates and validates CSRF tokens for state-changing requests
 * 
 * Requirements: 5.3 - Implement CSRF protection
 */

class CSRFProtection {
  constructor() {
    this.tokenKey = 'csrf_token';
    this.headerName = 'X-CSRF-Token';
  }

  /**
   * Generate a cryptographically secure random token
   * @returns {string} CSRF token
   */
  generateToken() {
    const array = new Uint8Array(32);
    window.crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Get current CSRF token, generating one if it doesn't exist
   * @returns {string} CSRF token
   */
  getToken() {
    let token = sessionStorage.getItem(this.tokenKey);
    if (!token) {
      token = this.generateToken();
      this.setToken(token);
    }
    return token;
  }

  /**
   * Set CSRF token in session storage
   * @param {string} token - CSRF token to store
   */
  setToken(token) {
    sessionStorage.setItem(this.tokenKey, token);
  }

  /**
   * Clear CSRF token from session storage
   */
  clearToken() {
    sessionStorage.removeItem(this.tokenKey);
  }

  /**
   * Get CSRF token as header object for fetch requests
   * @returns {Object} Header object with CSRF token
   */
  getHeader() {
    return {
      [this.headerName]: this.getToken()
    };
  }

  /**
   * Add CSRF token to fetch options
   * @param {Object} options - Fetch options object
   * @returns {Object} Options with CSRF header added
   */
  addTokenToRequest(options = {}) {
    const headers = options.headers || {};
    return {
      ...options,
      headers: {
        ...headers,
        ...this.getHeader()
      }
    };
  }

  /**
   * Check if request method requires CSRF protection
   * @param {string} method - HTTP method
   * @returns {boolean} True if method requires CSRF protection
   */
  requiresToken(method) {
    const safeMethods = ['GET', 'HEAD', 'OPTIONS', 'TRACE'];
    return !safeMethods.includes(method.toUpperCase());
  }

  /**
   * Refresh CSRF token (call after login)
   */
  refreshToken() {
    const newToken = this.generateToken();
    this.setToken(newToken);
    return newToken;
  }

  /**
   * Initialize CSRF protection
   * Fetches token from server on app load
   * @param {string} endpoint - API endpoint to fetch token from
   * @returns {Promise<string>} CSRF token
   */
  async initialize(endpoint = '/api/csrf-token') {
    try {
      const response = await fetch(endpoint, {
        method: 'GET',
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.csrf_token) {
          this.setToken(data.csrf_token);
          return data.csrf_token;
        }
      }

      // Fallback to client-generated token
      return this.getToken();
    } catch (error) {
      console.error('Failed to initialize CSRF token:', error);
      // Fallback to client-generated token
      return this.getToken();
    }
  }
}

// Export singleton instance
const csrfProtection = new CSRFProtection();
export default csrfProtection;
