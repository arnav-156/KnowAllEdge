/**
 * Enhanced API Client with Performance Tracking, Retry Logic, and Request Deduplication
 * ✅ NOW INCLUDES: Authentication support (API Key + JWT Token)
 * ✅ SECURITY: Environment-based configuration with validation
 * ✅ I18N: Language support with Accept-Language headers
 */

import axios from 'axios';
import analytics from './analytics';
import i18n from '../i18n/config';
import csrfProtection from './csrfProtection';

// ✅ SECURITY FIX: Secure API URL configuration with validation
const getAPIBaseURL = () => {
  // Get URL from environment variable
  const envURL = import.meta.env.VITE_API_URL;

  // Validate environment variable exists in production
  if (import.meta.env.MODE === 'production' && !envURL) {
    console.error('CRITICAL: VITE_API_URL not set in production!');
    throw new Error('API URL not configured. Please contact support.');
  }

  // Development fallback (only for local development)
  const defaultURL = import.meta.env.MODE === 'development'
    ? 'http://localhost:5000/api'
    : null;

  const apiURL = envURL || defaultURL;

  // Validate URL format
  if (apiURL) {
    try {
      const url = new URL(apiURL);
      // Enforce HTTPS in production
      if (import.meta.env.MODE === 'production' && url.protocol !== 'https:') {
        console.error('SECURITY WARNING: API URL must use HTTPS in production');
        throw new Error('Insecure API URL detected');
      }
    } catch (error) {
      console.error('Invalid API URL format:', apiURL);
      throw new Error('Invalid API configuration');
    }
  }

  return apiURL;
};

const API_BASE_URL = getAPIBaseURL();

class APIClient {
  constructor() {
    // ✅ NEW: Load API key from localStorage
    this.apiKey = this.getStoredAPIKey();
    this.jwtToken = this.getStoredJWTToken();

    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000, // 60 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // ✅ NEW: Request deduplication cache
    this.pendingRequests = new Map(); // key: request signature -> Promise
    this.abortControllers = new Map(); // key: request ID -> AbortController

    // ✅ NEW: Request queue for bulk operations
    this.requestQueue = [];
    this.isProcessingQueue = false;
    this.maxConcurrentRequests = 5; // Configurable concurrency limit

    // ✅ SECURITY: More aggressive exponential backoff to avoid hammering backend
    this.retryConfig = {
      maxRetries: 3,
      retryDelay: 1000, // Base delay in ms (exponential backoff: 1s, 4s, 16s)
      retryableStatuses: [408, 429, 500, 502, 503, 504], // Retry on these status codes
      retryableErrors: ['ECONNABORTED', 'ETIMEDOUT', 'ENOTFOUND', 'ENETUNREACH'],
    };

    // ✅ SECURITY: Request encryption configuration (optional, for sensitive data)
    this.encryptionEnabled = false; // Enable with enableEncryption()
    this.encryptionKey = null;

    this.setupInterceptors();
  }

  // ==================== ENCRYPTION METHODS ====================

  /**
   * ✅ SECURITY: Enable end-to-end encryption for sensitive data
   * Uses AES-GCM with Web Crypto API
   * 
   * NOTE: This provides defense-in-depth beyond HTTPS
   * Use for highly sensitive operations (e.g., financial, medical)
   */
  async enableEncryption(password = null) {
    try {
      // Generate or derive encryption key
      if (password) {
        // Derive key from password (PBKDF2)
        const encoder = new TextEncoder();
        const passwordBuffer = encoder.encode(password);
        const salt = crypto.getRandomValues(new Uint8Array(16));

        const keyMaterial = await crypto.subtle.importKey(
          'raw',
          passwordBuffer,
          'PBKDF2',
          false,
          ['deriveBits', 'deriveKey']
        );

        this.encryptionKey = await crypto.subtle.deriveKey(
          {
            name: 'PBKDF2',
            salt: salt,
            iterations: 100000,
            hash: 'SHA-256'
          },
          keyMaterial,
          { name: 'AES-GCM', length: 256 },
          false,
          ['encrypt', 'decrypt']
        );

        // Store salt for later (in production, use secure storage)
        sessionStorage.setItem('encryption_salt', btoa(String.fromCharCode(...salt)));
      } else {
        // Generate random key
        this.encryptionKey = await crypto.subtle.generateKey(
          { name: 'AES-GCM', length: 256 },
          true, // extractable (for session storage if needed)
          ['encrypt', 'decrypt']
        );
      }

      this.encryptionEnabled = true;
      console.log('✅ End-to-end encryption enabled');
      return true;
    } catch (error) {
      console.error('Failed to enable encryption:', error);
      return false;
    }
  }

  /**
   * ✅ SECURITY: Disable encryption
   */
  disableEncryption() {
    this.encryptionEnabled = false;
    this.encryptionKey = null;
    sessionStorage.removeItem('encryption_salt');
    console.log('Encryption disabled');
  }

  /**
   * ✅ SECURITY: Encrypt data using AES-GCM
   */
  async encryptData(data) {
    if (!this.encryptionEnabled || !this.encryptionKey) {
      return data; // No encryption, return as-is
    }

    try {
      const encoder = new TextEncoder();
      const dataString = typeof data === 'string' ? data : JSON.stringify(data);
      const dataBuffer = encoder.encode(dataString);

      // Generate random IV (Initialization Vector)
      const iv = crypto.getRandomValues(new Uint8Array(12));

      // Encrypt
      const encryptedBuffer = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv: iv },
        this.encryptionKey,
        dataBuffer
      );

      // Combine IV + encrypted data
      const combined = new Uint8Array(iv.length + encryptedBuffer.byteLength);
      combined.set(iv, 0);
      combined.set(new Uint8Array(encryptedBuffer), iv.length);

      // Convert to base64
      return btoa(String.fromCharCode(...combined));
    } catch (error) {
      console.error('Encryption failed:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  /**
   * ✅ SECURITY: Decrypt data using AES-GCM
   */
  async decryptData(encryptedData) {
    if (!this.encryptionEnabled || !this.encryptionKey) {
      return encryptedData; // No encryption, return as-is
    }

    try {
      // Decode base64
      const combined = new Uint8Array(
        atob(encryptedData).split('').map(c => c.charCodeAt(0))
      );

      // Extract IV and encrypted data
      const iv = combined.slice(0, 12);
      const data = combined.slice(12);

      // Decrypt
      const decryptedBuffer = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: iv },
        this.encryptionKey,
        data
      );

      // Convert to string
      const decoder = new TextDecoder();
      const decryptedString = decoder.decode(decryptedBuffer);

      // Try to parse as JSON, otherwise return string
      try {
        return JSON.parse(decryptedString);
      } catch {
        return decryptedString;
      }
    } catch (error) {
      console.error('Decryption failed:', error);
      throw new Error('Failed to decrypt data');
    }
  }

  // ==================== END ENCRYPTION METHODS ====================

  // ==================== AUTHENTICATION METHODS ====================

  /**
   * Get stored API key from localStorage
   */
  getStoredAPIKey() {
    return localStorage.getItem('KNOWALLEDGE_api_key') || null;
  }

  /**
   * Get stored JWT token from localStorage
   */
  getStoredJWTToken() {
    return localStorage.getItem('KNOWALLEDGE_jwt_token') || null;
  }

  /**
   * Set API key and store in localStorage
   */
  setAPIKey(apiKey) {
    this.apiKey = apiKey;
    if (apiKey) {
      localStorage.setItem('KNOWALLEDGE_api_key', apiKey);
    } else {
      localStorage.removeItem('KNOWALLEDGE_api_key');
    }
  }

  /**
   * Set JWT token and store in localStorage
   */
  setJWTToken(token) {
    this.jwtToken = token;
    if (token) {
      localStorage.setItem('KNOWALLEDGE_jwt_token', token);
    } else {
      localStorage.removeItem('KNOWALLEDGE_jwt_token');
    }
  }

  /**
   * Clear all authentication data
   */
  clearAuth() {
    this.apiKey = null;
    this.jwtToken = null;
    localStorage.removeItem('KNOWALLEDGE_api_key');
    localStorage.removeItem('KNOWALLEDGE_jwt_token');
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!(this.apiKey || this.jwtToken);
  }

  /**
   * Initialize CSRF protection
   * Should be called on app startup
   */
  async initializeCSRF() {
    try {
      await csrfProtection.initialize('/api/csrf-token');
      console.log('✅ CSRF protection initialized');
      return true;
    } catch (error) {
      console.error('Failed to initialize CSRF protection:', error);
      return false;
    }
  }

  // ==================== DEVTOOLS PROTECTION ====================

  /**
   * ✅ SECURITY: Sanitize data before sending to prevent DevTools exposure
   * Redacts sensitive fields from request/response objects
   * 
   * NOTE: This provides additional protection beyond encryption
   * Cannot fully prevent DevTools inspection, but reduces exposure
   */
  sanitizeForDevTools(data, sensitiveFields = []) {
    if (!data || typeof data !== 'object') {
      return data;
    }

    // Default sensitive fields
    const defaultSensitive = [
      'password', 'secret', 'token', 'api_key', 'apiKey',
      'authorization', 'credit_card', 'creditCard', 'ssn',
      'private_key', 'privateKey', 'encryption_key'
    ];

    const allSensitive = [...defaultSensitive, ...sensitiveFields];
    const sanitized = Array.isArray(data) ? [...data] : { ...data };

    // Recursively sanitize nested objects
    for (const key in sanitized) {
      if (allSensitive.some(field => key.toLowerCase().includes(field.toLowerCase()))) {
        sanitized[key] = '[REDACTED]';
      } else if (typeof sanitized[key] === 'object' && sanitized[key] !== null) {
        sanitized[key] = this.sanitizeForDevTools(sanitized[key], sensitiveFields);
      }
    }

    return sanitized;
  }

  /**
   * ✅ SECURITY: Disable DevTools in production (best effort)
   * Note: This is NOT a security guarantee, only a deterrent
   */
  disableDevTools() {
    if (import.meta.env.MODE === 'production') {
      // Detect if DevTools is open
      const detectDevTools = () => {
        const threshold = 160;
        const widthThreshold = window.outerWidth - window.innerWidth > threshold;
        const heightThreshold = window.outerHeight - window.innerHeight > threshold;

        if (widthThreshold || heightThreshold) {
          console.warn('⚠️ DevTools detected. Clearing sensitive data...');
          this.clearAuth();
          // Optionally reload page or redirect
          // window.location.href = '/';
        }
      };

      // Check periodically
      setInterval(detectDevTools, 1000);

      // Disable right-click context menu
      document.addEventListener('contextmenu', (e) => e.preventDefault());

      // Disable common DevTools shortcuts
      document.addEventListener('keydown', (e) => {
        if (
          e.key === 'F12' ||
          (e.ctrlKey && e.shiftKey && e.key === 'I') ||
          (e.ctrlKey && e.shiftKey && e.key === 'J') ||
          (e.ctrlKey && e.key === 'U')
        ) {
          e.preventDefault();
          console.warn('⚠️ DevTools access blocked');
        }
      });
    }
  }

  // ==================== END DEVTOOLS PROTECTION ====================

  /**
   * ✅ I18N: Get current language code from i18n
   */
  getCurrentLanguageCode() {
    return i18n.language || 'en';
  }

  /**
   * ✅ I18N: Get localized prompt instruction for backend
   * Adds language-specific instruction to Gemini prompts
   */
  getLocalizedPromptInstruction(languageCode = null) {
    const lang = languageCode || this.getCurrentLanguageCode();

    // Only add instruction if not English
    if (lang === 'en') {
      return '';
    }

    const languageInstructions = {
      es: '\n\nIMPORTANT: Please respond in Spanish (Español). Use formal "usted" form.',
      fr: '\n\nIMPORTANT: Veuillez répondre en français. Utilisez la forme formelle "vous".',
      de: '\n\nWICHTIG: Bitte antworten Sie auf Deutsch. Verwenden Sie die formelle "Sie"-Form.',
      zh: '\n\n重要提示：请用简体中文回答。使用正式语气。',
      ja: '\n\n重要：日本語で回答してください。丁寧な「です・ます」形を使用してください。',
      ar: '\n\nمهم: يرجى الرد باللغة العربية. استخدم الصيغة الرسمية.',
      he: '\n\nחשוב: אנא הגב בעברית. השתמש בצורה רשמית.',
    };

    return languageInstructions[lang] || '';
  }

  /**
   * Register new user and get API key
   */
  async register(userId, quotaTier = 'free') {
    try {
      const response = await this.client.post('/auth/register', {
        user_id: userId,
        quota_tier: quotaTier,
      });

      if (response.data.api_key) {
        this.setAPIKey(response.data.api_key);
        console.log('✅ User registered successfully');
      }

      return response.data;
    } catch (error) {
      console.error('❌ Registration failed:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Login with API key to get JWT token
   */
  async login(apiKey) {
    try {
      const response = await this.client.post('/auth/login', {
        api_key: apiKey || this.apiKey,
      });

      if (response.data.token) {
        this.setJWTToken(response.data.token);
        console.log('✅ Login successful');
      }

      return response.data;
    } catch (error) {
      console.error('❌ Login failed:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Validate current authentication
   */
  async validateAuth() {
    if (!this.isAuthenticated()) {
      return { valid: false };
    }

    try {
      const response = await this.client.get('/auth/validate');
      return response.data;
    } catch (error) {
      console.error('❌ Auth validation failed:', error.response?.data || error.message);
      return { valid: false };
    }
  }

  /**
   * Handle authentication errors
   */
  handleAuthError(error) {
    if (error.response?.status === 401) {
      console.warn('⚠️ Authentication failed. Clearing credentials...');
      this.clearAuth();

      // Optionally redirect to login page
      // window.location.href = '/login';

      // Or dispatch event for React components to handle
      window.dispatchEvent(new CustomEvent('auth-error', { detail: error }));
    }
  }

  // ==================== REQUEST SIGNING (HMAC-SHA256) ====================

  /**
   * ✅ NEW: Generate HMAC-SHA256 signature for request integrity
   * Prevents man-in-the-middle tampering
   */
  async generateSignature(method, path, timestamp, body = '') {
    if (!this.apiKey) {
      return null; // No signature without API key
    }

    const signingString = `${method}:${path}:${timestamp}:${body}`;

    try {
      // Convert API key and signing string to Uint8Array
      const encoder = new TextEncoder();
      const keyData = encoder.encode(this.apiKey);
      const messageData = encoder.encode(signingString);

      // Import key for HMAC
      const key = await crypto.subtle.importKey(
        'raw',
        keyData,
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign']
      );

      // Generate signature
      const signature = await crypto.subtle.sign('HMAC', key, messageData);

      // Convert to hex string
      return Array.from(new Uint8Array(signature))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
    } catch (error) {
      console.error('Failed to generate request signature:', error);
      return null;
    }
  }

  /**
   * ✅ NEW: Add request signature headers (optional, for sensitive endpoints)
   */
  async addSignatureHeaders(config) {
    if (!this.apiKey || config.skipSignature) {
      return config;
    }

    const timestamp = Math.floor(Date.now() / 1000).toString();
    const method = (config.method || 'get').toUpperCase();
    const path = config.url;
    const body = config.data ? JSON.stringify(config.data) : '';

    const signature = await this.generateSignature(method, path, timestamp, body);

    if (signature) {
      config.headers['X-Timestamp'] = timestamp;
      config.headers['X-Signature'] = signature;
    }

    return config;
  }

  // ==================== END REQUEST SIGNING ====================

  setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        config.metadata = { startTime: Date.now() };

        // ✅ SECURITY: Add CSRF token for state-changing requests
        if (csrfProtection.requiresToken(config.method)) {
          const csrfHeader = csrfProtection.getHeader();
          config.headers = { ...config.headers, ...csrfHeader };
        }

        // ✅ I18N: Add Accept-Language header
        const currentLanguage = this.getCurrentLanguageCode();
        config.headers['Accept-Language'] = currentLanguage;

        // ✅ I18N: Add language parameter to POST request bodies (if not already present)
        if (config.method === 'post' && config.data && typeof config.data === 'object') {
          // Don't override if language already specified
          if (!config.data.language && !config.data.encrypted) {
            config.data.language = currentLanguage;
          }
        }

        // ✅ SECURITY: Encrypt request body if encryption enabled (optional)
        if (this.encryptionEnabled && config.data && config.encryptRequest !== false) {
          try {
            const encryptedData = await this.encryptData(config.data);
            config.data = { encrypted: encryptedData };
            config.headers['X-Encrypted-Request'] = 'true';
          } catch (error) {
            console.error('Request encryption failed, sending unencrypted:', error);
          }
        }

        // ✅ NEW: Add authentication headers
        if (this.jwtToken) {
          // Prefer JWT token if available
          config.headers['Authorization'] = `Bearer ${this.jwtToken}`;
        } else if (this.apiKey) {
          // Fall back to API key
          config.headers['X-API-Key'] = this.apiKey;
        }

        // ✅ SECURITY: Add request signature for sensitive endpoints (optional)
        if (config.requireSignature) {
          await this.addSignatureHeaders(config);
        }

        // ✅ NEW: Add request ID for tracking
        config.requestId = `${config.method}_${config.url}_${Date.now()}`;

        // ✅ NEW: Setup abort signal if not provided
        if (!config.signal && !config.skipAbort) {
          const controller = new AbortController();
          config.signal = controller.signal;
          this.abortControllers.set(config.requestId, controller);
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor with retry logic
    this.client.interceptors.response.use(
      async (response) => {
        const endTime = Date.now();
        const startTime = response.config.metadata.startTime;

        // ✅ NEW: Clean up abort controller
        if (response.config.requestId) {
          this.abortControllers.delete(response.config.requestId);
        }

        // ✅ SECURITY: Decrypt response if encryption enabled
        if (this.encryptionEnabled && response.data?.encrypted) {
          try {
            response.data = await this.decryptData(response.data.encrypted);
          } catch (error) {
            console.error('Response decryption failed:', error);
            // Keep encrypted data, application will handle error
          }
        }

        // Track API call performance
        analytics.trackAPICall(
          response.config.url,
          response.config.method.toUpperCase(),
          startTime,
          endTime,
          response.status
        );

        return response;
      },
      async (error) => {
        const endTime = Date.now();
        const startTime = error.config?.metadata?.startTime || Date.now();
        const config = error.config;

        // ✅ NEW: Clean up abort controller
        if (config?.requestId) {
          this.abortControllers.delete(config.requestId);
        }

        // ✅ NEW: Retry logic for transient failures
        if (this.shouldRetry(error, config)) {
          const retryCount = config.__retryCount || 0;
          config.__retryCount = retryCount + 1;

          // ✅ PERFORMANCE: More aggressive exponential backoff: 1s, 4s, 16s
          // Uses base^(2*retryCount) instead of base*2^retryCount for faster backoff
          const delay = this.retryConfig.retryDelay * Math.pow(4, retryCount);

          console.log(
            `⏳ Retrying request (${config.__retryCount}/${this.retryConfig.maxRetries}) ` +
            `after ${delay}ms: ${config.method?.toUpperCase()} ${config.url}`
          );

          // Wait before retrying
          await new Promise((resolve) => setTimeout(resolve, delay));

          // Retry the request
          return this.client(config);
        }

        // ✅ NEW: Handle authentication errors
        this.handleAuthError(error);

        // Track failed API call
        analytics.trackAPICall(
          error.config?.url || 'unknown',
          error.config?.method?.toUpperCase() || 'UNKNOWN',
          startTime,
          endTime,
          error.response?.status || 0,
          error
        );

        // Track error
        analytics.trackError(error, {
          type: 'api_error',
          endpoint: error.config?.url,
          status: error.response?.status,
          retries: error.config?.__retryCount || 0,
        });

        return Promise.reject(error);
      }
    );
  }

  /**
   * ✅ NEW: Determine if request should be retried
   */
  shouldRetry(error, config) {
    // Don't retry if retries disabled or max retries reached
    if (config?.skipRetry || (config?.__retryCount || 0) >= this.retryConfig.maxRetries) {
      return false;
    }

    // Don't retry if request was cancelled
    if (error.code === 'ERR_CANCELED' || error.name === 'AbortError') {
      return false;
    }

    // Retry on network errors
    if (!error.response && this.retryConfig.retryableErrors.includes(error.code)) {
      return true;
    }

    // Retry on specific HTTP status codes
    if (error.response && this.retryConfig.retryableStatuses.includes(error.response.status)) {
      return true;
    }

    return false;
  }

  /**
   * ✅ NEW: Generate unique request signature for deduplication
   */
  getRequestSignature(method, url, data = null) {
    const dataStr = data ? JSON.stringify(data) : '';
    return `${method.toUpperCase()}_${url}_${dataStr}`;
  }

  /**
   * ✅ NEW: Execute request with deduplication
   * Prevents duplicate requests for the same data
   */
  async executeWithDedup(method, url, data = null, config = {}) {
    // Skip deduplication for certain requests
    if (config.skipDedup) {
      return this.client[method](url, method === 'get' ? config : data, config);
    }

    const signature = this.getRequestSignature(method, url, data);

    // Check if identical request is already pending
    if (this.pendingRequests.has(signature)) {
      console.log(`Deduplicating request: ${method.toUpperCase()} ${url}`);
      return this.pendingRequests.get(signature);
    }

    // Create new request promise
    const requestPromise = (async () => {
      try {
        const response =
          method === 'get'
            ? await this.client.get(url, config)
            : await this.client[method](url, data, config);
        return response;
      } finally {
        // Remove from pending requests when complete
        this.pendingRequests.delete(signature);
      }
    })();

    // Cache the pending request
    this.pendingRequests.set(signature, requestPromise);

    return requestPromise;
  }

  /**
   * ✅ NEW: Add request to queue for bulk operations
   */
  async queueRequest(requestFn, priority = 0) {
    return new Promise((resolve, reject) => {
      this.requestQueue.push({
        execute: requestFn,
        priority,
        resolve,
        reject,
      });

      // Sort by priority (higher priority first)
      this.requestQueue.sort((a, b) => b.priority - a.priority);

      // Start processing queue if not already processing
      if (!this.isProcessingQueue) {
        this.processQueue();
      }
    });
  }

  /**
   * ✅ NEW: Process queued requests with concurrency limit
   */
  async processQueue() {
    if (this.requestQueue.length === 0) {
      this.isProcessingQueue = false;
      return;
    }

    this.isProcessingQueue = true;

    // Process up to maxConcurrentRequests at a time
    const batch = this.requestQueue.splice(0, this.maxConcurrentRequests);

    await Promise.allSettled(
      batch.map(async (item) => {
        try {
          const result = await item.execute();
          item.resolve(result);
        } catch (error) {
          item.reject(error);
        }
      })
    );

    // Continue processing remaining queue
    this.processQueue();
  }

  /**
   * ✅ NEW: Cancel specific request by ID
   */
  cancelRequest(requestId) {
    const controller = this.abortControllers.get(requestId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestId);
      console.log(`Cancelled request: ${requestId}`);
      return true;
    }
    return false;
  }

  /**
   * ✅ NEW: Cancel all pending requests
   */
  cancelAllRequests() {
    let count = 0;
    this.abortControllers.forEach((controller, requestId) => {
      controller.abort();
      count++;
    });
    this.abortControllers.clear();
    console.log(`Cancelled ${count} pending requests`);
    return count;
  }

  // Create subtopics with retry and deduplication
  async createSubtopics(topic) {
    try {
      const response = await this.executeWithDedup('post', '/create_subtopics', { topic });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: this.formatError(error),
      };
    }
  }

  // Create presentation with cancellation support
  async createPresentation(topic, educationLevel, levelOfDetail, focus, learningStyle = 'General', signal = null) {
    try {
      const config = {
        signal, // User-provided abort signal
        skipDedup: true, // Don't deduplicate presentations (they can be customized)
      };

      const response = await this.client.post(
        '/create_presentation',
        {
          topic,
          educationLevel,
          levelOfDetail,
          focus,
          learningStyle, // ✅ Pass learning style
        },
        config
      );

      return { success: true, data: response.data };
    } catch (error) {
      // Don't track cancellation as error
      if (error.name === 'AbortError' || error.code === 'ERR_CANCELED') {
        return {
          success: false,
          cancelled: true,
          error: 'Request cancelled',
        };
      }

      return {
        success: false,
        error: this.formatError(error),
      };
    }
  }

  // Image to topic with retry and deduplication
  async imageToTopic(imagePath) {
    try {
      const response = await this.executeWithDedup('post', '/image2topic', { imagePath });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: this.formatError(error),
      };
    }
  }

  // Upload image (no deduplication - each upload is unique)
  async uploadImage(file) {
    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await this.client.post('/image2topic', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        skipDedup: true, // Each file upload is unique
      });

      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: this.formatError(error),
      };
    }
  }

  // ==================== ADAPTIVE LEARNING METHODS ====================

  // Generate Quiz
  async generateQuiz(topic, subtopic, education = 'high school', count = 3) {
    try {
      const response = await this.executeWithDedup('post', '/quiz/generate', {
        topic,
        subtopic,
        education,
        count
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: this.formatError(error) };
    }
  }

  // Submit Quiz
  async submitQuiz(topic, subtopic, score, total, difficulty = 'medium') {
    try {
      const response = await this.client.post('/quiz/submit', {
        topic,
        subtopic,
        score,
        total,
        difficulty
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: this.formatError(error) };
    }
  }

  // Get Progress
  async getProgress(topic = null) {
    try {
      const url = topic ? `/progress?topic=${encodeURIComponent(topic)}` : '/progress';
      const response = await this.client.get(url);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: this.formatError(error) };
    }
  }

  // Get Recommendations
  async getRecommendations(topic) {
    try {
      const response = await this.executeWithDedup('post', '/recommendations', { topic });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: this.formatError(error) };
    }
  }

  // Health check with deduplication
  async healthCheck() {
    try {
      const response = await this.executeWithDedup('get', '/health');
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: this.formatError(error),
      };
    }
  }

  // Format error for user-friendly display
  formatError(error) {
    if (error.response) {
      // Server responded with error
      return {
        message: error.response.data?.error || 'Server error occurred',
        status: error.response.status,
        details: error.response.data
      };
    } else if (error.request) {
      // Request made but no response
      return {
        message: 'Network error - please check your connection',
        status: 0,
        details: 'No response from server'
      };
    } else {
      // Error in request setup
      return {
        message: error.message || 'An unexpected error occurred',
        status: 0,
        details: error.toString()
      };
    }
  }
}

export default new APIClient();
