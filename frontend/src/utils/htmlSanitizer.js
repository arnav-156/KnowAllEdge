/**
 * HTML Sanitization Utility
 * Sanitizes HTML content to prevent XSS attacks
 * Uses DOMPurify if available, falls back to basic sanitization
 * 
 * Requirements: 5.6 - Integrate DOMPurify for HTML sanitization
 */

// Try to import DOMPurify (install with: npm install dompurify)
let DOMPurify = null;
try {
  // Dynamic import to handle if DOMPurify is not installed
  const module = await import('dompurify');
  DOMPurify = module.default;
} catch (error) {
  console.warn('DOMPurify not installed. Using basic sanitization. Install with: npm install dompurify');
}

class HTMLSanitizer {
  constructor() {
    this.useDOMPurify = !!DOMPurify;
    
    // Basic sanitization config
    this.allowedTags = [
      'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'a', 'code', 'pre', 'blockquote', 'span', 'div'
    ];
    
    this.allowedAttributes = {
      'a': ['href', 'title', 'target', 'rel'],
      'span': ['class'],
      'div': ['class'],
      'code': ['class']
    };

    // DOMPurify config
    this.domPurifyConfig = {
      ALLOWED_TAGS: this.allowedTags,
      ALLOWED_ATTR: ['href', 'title', 'target', 'rel', 'class'],
      ALLOW_DATA_ATTR: false,
      ALLOW_UNKNOWN_PROTOCOLS: false,
      SAFE_FOR_TEMPLATES: true,
      RETURN_DOM: false,
      RETURN_DOM_FRAGMENT: false,
      RETURN_TRUSTED_TYPE: false
    };
  }

  /**
   * Sanitize HTML content
   * @param {string} html - HTML content to sanitize
   * @param {Object} options - Sanitization options
   * @returns {string} Sanitized HTML
   */
  sanitize(html, options = {}) {
    if (!html || typeof html !== 'string') {
      return '';
    }

    // Use DOMPurify if available
    if (this.useDOMPurify) {
      return this.sanitizeWithDOMPurify(html, options);
    }

    // Fall back to basic sanitization
    return this.basicSanitize(html, options);
  }

  /**
   * Sanitize using DOMPurify
   * @param {string} html - HTML content
   * @param {Object} options - Options
   * @returns {string} Sanitized HTML
   */
  sanitizeWithDOMPurify(html, options = {}) {
    const config = { ...this.domPurifyConfig, ...options };
    return DOMPurify.sanitize(html, config);
  }

  /**
   * Basic sanitization without DOMPurify
   * @param {string} html - HTML content
   * @param {Object} options - Options
   * @returns {string} Sanitized HTML
   */
  basicSanitize(html, options = {}) {
    // Create a temporary div to parse HTML
    const temp = document.createElement('div');
    temp.innerHTML = html;

    // Recursively sanitize nodes
    this.sanitizeNode(temp, options);

    return temp.innerHTML;
  }

  /**
   * Recursively sanitize a DOM node
   * @param {Node} node - DOM node to sanitize
   * @param {Object} options - Options
   */
  sanitizeNode(node, options = {}) {
    const allowedTags = options.allowedTags || this.allowedTags;
    const allowedAttributes = options.allowedAttributes || this.allowedAttributes;

    // Process child nodes
    const children = Array.from(node.childNodes);
    for (let child of children) {
      if (child.nodeType === Node.ELEMENT_NODE) {
        const tagName = child.tagName.toLowerCase();

        // Remove disallowed tags
        if (!allowedTags.includes(tagName)) {
          child.remove();
          continue;
        }

        // Remove disallowed attributes
        const allowedAttrs = allowedAttributes[tagName] || [];
        const attributes = Array.from(child.attributes);
        for (let attr of attributes) {
          if (!allowedAttrs.includes(attr.name)) {
            child.removeAttribute(attr.name);
          }
        }

        // Sanitize href attributes
        if (child.hasAttribute('href')) {
          const href = child.getAttribute('href');
          if (!this.isSafeURL(href)) {
            child.removeAttribute('href');
          }
        }

        // Recursively sanitize children
        this.sanitizeNode(child, options);
      } else if (child.nodeType === Node.TEXT_NODE) {
        // Text nodes are safe, no action needed
      } else {
        // Remove other node types (comments, etc.)
        child.remove();
      }
    }
  }

  /**
   * Check if URL is safe
   * @param {string} url - URL to check
   * @returns {boolean} True if safe
   */
  isSafeURL(url) {
    if (!url) return false;

    // Remove whitespace
    url = url.trim().toLowerCase();

    // Block dangerous protocols
    const dangerousProtocols = ['javascript:', 'data:', 'vbscript:', 'file:'];
    for (let protocol of dangerousProtocols) {
      if (url.startsWith(protocol)) {
        return false;
      }
    }

    // Allow http, https, mailto, and relative URLs
    const safeProtocols = ['http://', 'https://', 'mailto:', '//', '/'];
    const isSafe = safeProtocols.some(protocol => url.startsWith(protocol));
    
    // Also allow relative URLs without protocol
    return isSafe || !url.includes(':');
  }

  /**
   * Sanitize text content (strip all HTML)
   * @param {string} text - Text content
   * @returns {string} Plain text
   */
  sanitizeText(text) {
    if (!text || typeof text !== 'string') {
      return '';
    }

    // Create temporary element
    const temp = document.createElement('div');
    temp.textContent = text;
    return temp.textContent;
  }

  /**
   * Escape HTML entities
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  escapeHTML(text) {
    if (!text || typeof text !== 'string') {
      return '';
    }

    const escapeMap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#x27;',
      '/': '&#x2F;'
    };

    return text.replace(/[&<>"'/]/g, char => escapeMap[char]);
  }

  /**
   * Unescape HTML entities
   * @param {string} text - Text to unescape
   * @returns {string} Unescaped text
   */
  unescapeHTML(text) {
    if (!text || typeof text !== 'string') {
      return '';
    }

    const temp = document.createElement('div');
    temp.innerHTML = text;
    return temp.textContent;
  }

  /**
   * Sanitize for use in attributes
   * @param {string} value - Attribute value
   * @returns {string} Sanitized value
   */
  sanitizeAttribute(value) {
    if (!value || typeof value !== 'string') {
      return '';
    }

    // Remove quotes and dangerous characters
    return value
      .replace(/[<>"'`]/g, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+=/gi, '');
  }

  /**
   * Check if DOMPurify is available
   * @returns {boolean} True if DOMPurify is available
   */
  isDOMPurifyAvailable() {
    return this.useDOMPurify;
  }

  /**
   * Get sanitization method being used
   * @returns {string} 'dompurify' or 'basic'
   */
  getMethod() {
    return this.useDOMPurify ? 'dompurify' : 'basic';
  }
}

// Export singleton instance
const htmlSanitizer = new HTMLSanitizer();
export default htmlSanitizer;

// Also export the class for testing
export { HTMLSanitizer };
