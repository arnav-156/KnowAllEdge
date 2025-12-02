/**
 * SecureStorage Utility
 * Provides encrypted storage for sensitive data using Web Crypto API
 * Wraps localStorage with encryption/decryption
 * 
 * Requirements: 5.2 - Encrypt sensitive data in browser storage
 */

class SecureStorage {
  constructor() {
    this.algorithm = 'AES-GCM';
    this.keyLength = 256;
    this.ivLength = 12; // 96 bits for GCM
    this.saltLength = 16;
    this.iterations = 100000;
    this.keyCache = null;
  }

  /**
   * Generate a cryptographic key from a password
   * @param {string} password - Password to derive key from
   * @param {Uint8Array} salt - Salt for key derivation
   * @returns {Promise<CryptoKey>} Derived encryption key
   */
  async deriveKey(password, salt) {
    const encoder = new TextEncoder();
    const passwordBuffer = encoder.encode(password);

    // Import password as key material
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      passwordBuffer,
      'PBKDF2',
      false,
      ['deriveBits', 'deriveKey']
    );

    // Derive AES key using PBKDF2
    return await window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: this.iterations,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: this.algorithm, length: this.keyLength },
      false,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Get or generate encryption key
   * Uses session-based key derived from user session
   * @returns {Promise<CryptoKey>} Encryption key
   */
  async getEncryptionKey() {
    if (this.keyCache) {
      return this.keyCache;
    }

    // Get or generate session-based password
    let sessionPassword = sessionStorage.getItem('_sec_key');
    if (!sessionPassword) {
      // Generate random password for this session
      const randomBytes = new Uint8Array(32);
      window.crypto.getRandomValues(randomBytes);
      sessionPassword = Array.from(randomBytes)
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      sessionStorage.setItem('_sec_key', sessionPassword);
    }

    // Get or generate salt
    let saltHex = localStorage.getItem('_sec_salt');
    let salt;
    if (!saltHex) {
      salt = new Uint8Array(this.saltLength);
      window.crypto.getRandomValues(salt);
      saltHex = Array.from(salt)
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      localStorage.setItem('_sec_salt', saltHex);
    } else {
      salt = new Uint8Array(
        saltHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16))
      );
    }

    this.keyCache = await this.deriveKey(sessionPassword, salt);
    return this.keyCache;
  }

  /**
   * Encrypt data
   * @param {string} data - Data to encrypt
   * @returns {Promise<string>} Encrypted data as base64
   */
  async encrypt(data) {
    try {
      const encoder = new TextEncoder();
      const dataBuffer = encoder.encode(data);

      // Generate random IV
      const iv = new Uint8Array(this.ivLength);
      window.crypto.getRandomValues(iv);

      // Get encryption key
      const key = await this.getEncryptionKey();

      // Encrypt data
      const encryptedBuffer = await window.crypto.subtle.encrypt(
        {
          name: this.algorithm,
          iv: iv
        },
        key,
        dataBuffer
      );

      // Combine IV and encrypted data
      const combined = new Uint8Array(iv.length + encryptedBuffer.byteLength);
      combined.set(iv, 0);
      combined.set(new Uint8Array(encryptedBuffer), iv.length);

      // Convert to base64
      return btoa(String.fromCharCode(...combined));
    } catch (error) {
      console.error('Encryption error:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  /**
   * Decrypt data
   * @param {string} encryptedData - Encrypted data as base64
   * @returns {Promise<string>} Decrypted data
   */
  async decrypt(encryptedData) {
    try {
      // Convert from base64
      const combined = new Uint8Array(
        atob(encryptedData).split('').map(c => c.charCodeAt(0))
      );

      // Extract IV and encrypted data
      const iv = combined.slice(0, this.ivLength);
      const data = combined.slice(this.ivLength);

      // Get encryption key
      const key = await this.getEncryptionKey();

      // Decrypt data
      const decryptedBuffer = await window.crypto.subtle.decrypt(
        {
          name: this.algorithm,
          iv: iv
        },
        key,
        data
      );

      // Convert to string
      const decoder = new TextDecoder();
      return decoder.decode(decryptedBuffer);
    } catch (error) {
      console.error('Decryption error:', error);
      throw new Error('Failed to decrypt data');
    }
  }

  /**
   * Set item in secure storage
   * @param {string} key - Storage key
   * @param {any} value - Value to store (will be JSON stringified)
   * @returns {Promise<void>}
   */
  async setItem(key, value) {
    try {
      const jsonValue = JSON.stringify(value);
      const encrypted = await this.encrypt(jsonValue);
      localStorage.setItem(`_sec_${key}`, encrypted);
    } catch (error) {
      console.error(`Failed to set secure item ${key}:`, error);
      throw error;
    }
  }

  /**
   * Get item from secure storage
   * @param {string} key - Storage key
   * @returns {Promise<any>} Decrypted and parsed value, or null if not found
   */
  async getItem(key) {
    try {
      const encrypted = localStorage.getItem(`_sec_${key}`);
      if (!encrypted) {
        return null;
      }
      const decrypted = await this.decrypt(encrypted);
      return JSON.parse(decrypted);
    } catch (error) {
      console.error(`Failed to get secure item ${key}:`, error);
      return null;
    }
  }

  /**
   * Remove item from secure storage
   * @param {string} key - Storage key
   */
  removeItem(key) {
    localStorage.removeItem(`_sec_${key}`);
  }

  /**
   * Clear all secure storage items
   */
  clear() {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith('_sec_')) {
        localStorage.removeItem(key);
      }
    });
    sessionStorage.removeItem('_sec_key');
    this.keyCache = null;
  }

  /**
   * Check if Web Crypto API is available
   * @returns {boolean} True if available
   */
  static isSupported() {
    return (
      typeof window !== 'undefined' &&
      window.crypto &&
      window.crypto.subtle &&
      typeof window.crypto.subtle.encrypt === 'function'
    );
  }

  /**
   * Get all secure storage keys
   * @returns {string[]} Array of keys (without _sec_ prefix)
   */
  keys() {
    const keys = Object.keys(localStorage);
    return keys
      .filter(key => key.startsWith('_sec_') && key !== '_sec_salt')
      .map(key => key.substring(5));
  }
}

// Export singleton instance
const secureStorage = new SecureStorage();
export default secureStorage;
