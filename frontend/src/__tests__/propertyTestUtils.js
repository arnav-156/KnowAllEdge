/**
 * Property-Based Testing Utilities for Frontend
 * Provides common generators and helpers for fast-check tests
 * Requirements: 6.3 - Set up property-based testing
 */

import fc from 'fast-check';

// ==================== Custom Arbitraries ====================

/**
 * Generate valid email addresses
 */
export const emailArbitrary = () => {
  return fc.tuple(
    fc.stringOf(fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz0123456789._-'), { minLength: 1, maxLength: 64 }),
    fc.stringOf(fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz0123456789-'), { minLength: 1, maxLength: 63 }),
    fc.constantFrom('com', 'org', 'net', 'edu', 'gov')
  ).map(([user, domain, tld]) => `${user}@${domain}.${tld}`);
};

/**
 * Generate valid passwords
 */
export const passwordArbitrary = (minLength = 8, maxLength = 100) => {
  return fc.string({ minLength, maxLength });
};

/**
 * Generate valid topic strings
 */
export const topicArbitrary = (minLength = 1, maxLength = 200) => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,()!?&';
  return fc.stringOf(fc.constantFrom(...chars), { minLength, maxLength })
    .filter(s => s.trim().length > 0);
};

/**
 * Generate valid subtopics arrays
 */
export const subtopicsArbitrary = (minItems = 1, maxItems = 20) => {
  return fc.array(
    topicArbitrary(1, 100),
    { minLength: minItems, maxLength: maxItems }
  ).map(arr => [...new Set(arr)]); // Ensure unique
};

/**
 * Generate JWT-like tokens
 */
export const jwtTokenArbitrary = () => {
  return fc.tuple(
    fc.hexaString({ minLength: 20, maxLength: 50 }),
    fc.hexaString({ minLength: 50, maxLength: 200 }),
    fc.hexaString({ minLength: 20, maxLength: 50 })
  ).map(([header, payload, signature]) => `${header}.${payload}.${signature}`);
};

/**
 * Generate API keys
 */
export const apiKeyArbitrary = (prefix = 'sk_') => {
  return fc.hexaString({ minLength: 32, maxLength: 64 })
    .map(key => `${prefix}${key}`);
};

/**
 * Generate timestamps
 */
export const timestampArbitrary = () => {
  return fc.date({
    min: new Date('2020-01-01'),
    max: new Date('2030-12-31')
  });
};

/**
 * Generate file sizes in bytes
 */
export const fileSizeArbitrary = (minSize = 0, maxSize = 10 * 1024 * 1024) => {
  return fc.integer({ min: minSize, max: maxSize });
};

/**
 * Generate file extensions
 */
export const fileExtensionArbitrary = (allowedOnly = true) => {
  if (allowedOnly) {
    return fc.constantFrom('jpg', 'jpeg', 'png', 'gif', 'webp');
  }
  return fc.stringOf(fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz'), { minLength: 2, maxLength: 5 });
};

/**
 * Generate HTTP status codes
 */
export const httpStatusArbitrary = () => {
  return fc.constantFrom(
    200, 201, 204,  // Success
    400, 401, 403, 404, 422, 429,  // Client errors
    500, 502, 503, 504  // Server errors
  );
};

/**
 * Generate user roles
 */
export const roleArbitrary = () => {
  return fc.constantFrom('user', 'admin', 'moderator');
};

/**
 * Generate quota tiers
 */
export const quotaTierArbitrary = () => {
  return fc.constantFrom('free', 'basic', 'premium', 'enterprise');
};

/**
 * Generate IP addresses
 */
export const ipAddressArbitrary = () => {
  return fc.tuple(
    fc.integer({ min: 0, max: 255 }),
    fc.integer({ min: 0, max: 255 }),
    fc.integer({ min: 0, max: 255 }),
    fc.integer({ min: 0, max: 255 })
  ).map(([a, b, c, d]) => `${a}.${b}.${c}.${d}`);
};

/**
 * Generate user agent strings
 */
export const userAgentArbitrary = () => {
  return fc.tuple(
    fc.constantFrom('Chrome', 'Firefox', 'Safari', 'Edge'),
    fc.integer({ min: 80, max: 120 })
  ).map(([browser, version]) => `Mozilla/5.0 (${browser}/${version})`);
};

// ==================== Composite Arbitraries ====================

/**
 * Generate complete user data
 */
export const userDataArbitrary = () => {
  return fc.record({
    email: emailArbitrary(),
    password: passwordArbitrary(),
    role: roleArbitrary(),
    quota_tier: quotaTierArbitrary(),
    created_at: timestampArbitrary()
  });
};

/**
 * Generate complete session data
 */
export const sessionDataArbitrary = () => {
  return fc.record({
    token: jwtTokenArbitrary(),
    user_id: fc.integer({ min: 1, max: 1000000 }),
    expires_at: timestampArbitrary(),
    ip_address: ipAddressArbitrary(),
    user_agent: userAgentArbitrary()
  });
};

/**
 * Generate complete API key data
 */
export const apiKeyDataArbitrary = () => {
  return fc.record({
    key: apiKeyArbitrary(),
    user_id: fc.integer({ min: 1, max: 1000000 }),
    name: fc.string({ minLength: 1, maxLength: 100 }),
    created_at: timestampArbitrary()
  });
};

/**
 * Generate error objects
 */
export const errorArbitrary = () => {
  return fc.record({
    error_code: fc.constantFrom(
      'VALIDATION_ERROR',
      'AUTH_REQUIRED',
      'RATE_LIMIT_EXCEEDED',
      'SERVER_ERROR'
    ),
    message: fc.string({ minLength: 10, maxLength: 200 }),
    details: fc.object()
  });
};

// ==================== Helper Functions ====================

/**
 * Check if email is valid
 */
export const isValidEmail = (email) => {
  const pattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$/;
  return pattern.test(email);
};

/**
 * Check if password meets requirements
 */
export const isValidPassword = (password, minLength = 8) => {
  return password.length >= minLength;
};

/**
 * Check if topic is valid
 */
export const isValidTopic = (topic, maxLength = 200) => {
  return topic.trim().length > 0 && topic.length <= maxLength;
};

/**
 * Check if JWT format is valid
 */
export const isValidJWT = (token) => {
  const parts = token.split('.');
  return parts.length === 3 && parts.every(p => p.length > 0);
};

/**
 * Check if API key format is valid
 */
export const isValidAPIKey = (key, prefix = 'sk_') => {
  return key.startsWith(prefix) && key.length > prefix.length + 20;
};

// ==================== Test Configuration ====================

/**
 * Default configuration for property tests
 */
export const defaultConfig = {
  numRuns: 100,
  verbose: true,
  seed: Date.now(),
};

/**
 * Fast configuration for quick tests
 */
export const fastConfig = {
  numRuns: 20,
  verbose: false,
};

/**
 * Thorough configuration for critical tests
 */
export const thoroughConfig = {
  numRuns: 1000,
  verbose: true,
};

// ==================== Example Property Tests ====================

/**
 * Example property test template
 */
export const examplePropertyTest = () => {
  // This is a template - actual tests are in test files
  
  test('password encryption is reversible', () => {
    fc.assert(
      fc.property(passwordArbitrary(), (password) => {
        // const encrypted = encrypt(password);
        // const decrypted = decrypt(encrypted);
        // return decrypted === password;
        return true;
      }),
      defaultConfig
    );
  });
};

/**
 * Example stateful test template
 */
export const exampleStatefulTest = () => {
  // This is a template for stateful testing
  
  class AuthModel {
    constructor() {
      this.users = new Map();
      this.sessions = new Map();
    }
    
    register(email, password) {
      if (!this.users.has(email)) {
        this.users.set(email, { password, role: 'user' });
        return true;
      }
      return false;
    }
    
    login(email, password) {
      const user = this.users.get(email);
      if (user && user.password === password) {
        const token = `token_${this.sessions.size}`;
        this.sessions.set(token, { email });
        return token;
      }
      return null;
    }
  }
  
  // Use fc.commands() for stateful testing
};

export default {
  // Arbitraries
  emailArbitrary,
  passwordArbitrary,
  topicArbitrary,
  subtopicsArbitrary,
  jwtTokenArbitrary,
  apiKeyArbitrary,
  timestampArbitrary,
  fileSizeArbitrary,
  fileExtensionArbitrary,
  httpStatusArbitrary,
  roleArbitrary,
  quotaTierArbitrary,
  ipAddressArbitrary,
  userAgentArbitrary,
  
  // Composite
  userDataArbitrary,
  sessionDataArbitrary,
  apiKeyDataArbitrary,
  errorArbitrary,
  
  // Helpers
  isValidEmail,
  isValidPassword,
  isValidTopic,
  isValidJWT,
  isValidAPIKey,
  
  // Config
  defaultConfig,
  fastConfig,
  thoroughConfig,
};
