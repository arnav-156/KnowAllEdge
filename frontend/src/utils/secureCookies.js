/**
 * Secure Cookie Utility
 * Handles cookies with proper security flags
 * 
 * Requirements: 5.5 - Implement secure cookie handling
 */

class SecureCookies {
  constructor() {
    this.isProduction = import.meta.env.MODE === 'production';
  }

  /**
   * Set a cookie with security flags
   * @param {string} name - Cookie name
   * @param {string} value - Cookie value
   * @param {Object} options - Cookie options
   * @param {number} options.maxAge - Max age in seconds
   * @param {string} options.path - Cookie path
   * @param {boolean} options.httpOnly - HttpOnly flag (note: can't be set from JS)
   * @param {boolean} options.secure - Secure flag
   * @param {string} options.sameSite - SameSite policy ('Strict', 'Lax', 'None')
   */
  setCookie(name, value, options = {}) {
    const {
      maxAge = 86400, // 24 hours default
      path = '/',
      secure = this.isProduction, // Secure flag in production
      sameSite = 'Strict' // Strict by default
    } = options;

    let cookieString = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;
    
    // Add max age
    if (maxAge) {
      cookieString += `; Max-Age=${maxAge}`;
    }
    
    // Add path
    cookieString += `; Path=${path}`;
    
    // Add Secure flag (only works over HTTPS)
    if (secure) {
      cookieString += '; Secure';
    }
    
    // Add SameSite policy
    if (sameSite) {
      cookieString += `; SameSite=${sameSite}`;
    }

    // Note: HttpOnly cannot be set from JavaScript
    // It must be set by the server in Set-Cookie header
    
    document.cookie = cookieString;
  }

  /**
   * Get a cookie value
   * @param {string} name - Cookie name
   * @returns {string|null} Cookie value or null if not found
   */
  getCookie(name) {
    const nameEQ = encodeURIComponent(name) + '=';
    const cookies = document.cookie.split(';');
    
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.indexOf(nameEQ) === 0) {
        return decodeURIComponent(cookie.substring(nameEQ.length));
      }
    }
    
    return null;
  }

  /**
   * Delete a cookie
   * @param {string} name - Cookie name
   * @param {string} path - Cookie path
   */
  deleteCookie(name, path = '/') {
    this.setCookie(name, '', {
      maxAge: -1,
      path: path
    });
  }

  /**
   * Check if a cookie exists
   * @param {string} name - Cookie name
   * @returns {boolean} True if cookie exists
   */
  hasCookie(name) {
    return this.getCookie(name) !== null;
  }

  /**
   * Get all cookies as an object
   * @returns {Object} Object with cookie name-value pairs
   */
  getAllCookies() {
    const cookies = {};
    const cookieStrings = document.cookie.split(';');
    
    for (let cookie of cookieStrings) {
      cookie = cookie.trim();
      const [name, value] = cookie.split('=');
      if (name && value) {
        cookies[decodeURIComponent(name)] = decodeURIComponent(value);
      }
    }
    
    return cookies;
  }

  /**
   * Clear all cookies
   */
  clearAllCookies() {
    const cookies = this.getAllCookies();
    for (let name in cookies) {
      this.deleteCookie(name);
    }
  }

  /**
   * Set authentication cookie with secure flags
   * @param {string} token - Authentication token
   * @param {number} maxAge - Max age in seconds (default 24 hours)
   */
  setAuthCookie(token, maxAge = 86400) {
    this.setCookie('auth_token', token, {
      maxAge: maxAge,
      secure: this.isProduction,
      sameSite: 'Strict',
      path: '/'
    });
  }

  /**
   * Get authentication cookie
   * @returns {string|null} Authentication token or null
   */
  getAuthCookie() {
    return this.getCookie('auth_token');
  }

  /**
   * Clear authentication cookie
   */
  clearAuthCookie() {
    this.deleteCookie('auth_token');
  }

  /**
   * Set session cookie (expires when browser closes)
   * @param {string} name - Cookie name
   * @param {string} value - Cookie value
   */
  setSessionCookie(name, value) {
    this.setCookie(name, value, {
      maxAge: null, // Session cookie
      secure: this.isProduction,
      sameSite: 'Strict'
    });
  }

  /**
   * Validate cookie security settings
   * Checks if cookies are being set with proper security flags
   * @returns {Object} Validation results
   */
  validateCookieSecurity() {
    const results = {
      secure: true,
      sameSite: true,
      issues: []
    };

    // In production, check if we're on HTTPS
    if (this.isProduction && window.location.protocol !== 'https:') {
      results.secure = false;
      results.issues.push('Not using HTTPS in production - Secure flag will not work');
    }

    // Check if cookies exist without proper flags
    // Note: We can't actually check the flags from JavaScript
    // This is more of a reminder/documentation
    const cookies = this.getAllCookies();
    if (Object.keys(cookies).length > 0 && !this.isProduction) {
      results.issues.push('Development mode - cookies may not have Secure flag');
    }

    return results;
  }
}

// Export singleton instance
const secureCookies = new SecureCookies();
export default secureCookies;
