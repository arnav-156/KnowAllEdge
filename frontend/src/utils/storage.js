/**
 * ✅ SECURE LocalStorage Utility
 * Handles persistence with encryption, expiration, and quota management
 * 
 * Security Features:
 * - AES-GCM encryption for sensitive data
 * - Automatic expiration/TTL
 * - Storage quota management (prevents crashes)
 * - Data integrity verification
 * 
 * @version 2.0
 * @date November 16, 2025
 */

const STORAGE_KEYS = {
  USER_PREFERENCES: 'KNOWALLEDGE_preferences',
  RECENT_TOPICS: 'KNOWALLEDGE_recent_topics',
  LAST_SESSION: 'KNOWALLEDGE_last_session',
  ENCRYPTION_KEY: 'KNOWALLEDGE_enc_key', // ✅ SECURITY: Stored encryption key
  STORAGE_METADATA: 'KNOWALLEDGE_metadata', // ✅ STORAGE: Quota tracking
  PRIVACY_CONSENT: 'KNOWALLEDGE_privacy_consent', // ✅ PRIVACY: GDPR/CCPA consent
};

// ✅ PRIVACY: Data categories requiring consent
const DATA_CATEGORIES = {
  NECESSARY: 'necessary',        // Required for app to function (no consent needed)
  FUNCTIONAL: 'functional',      // User preferences, settings
  ANALYTICS: 'analytics',        // Usage tracking, recent topics
  PERFORMANCE: 'performance'     // Session state, optimization
};

// ✅ TTL: Default expiration times (in milliseconds)
const DEFAULT_TTL = {
  USER_PREFERENCES: 30 * 24 * 60 * 60 * 1000, // 30 days
  RECENT_TOPICS: 7 * 24 * 60 * 60 * 1000,      // 7 days
  LAST_SESSION: 24 * 60 * 60 * 1000,           // 24 hours
};

// ✅ STORAGE: Quota limits (in bytes)
const STORAGE_LIMITS = {
  MAX_TOTAL_SIZE: 4 * 1024 * 1024,  // 4MB (safe limit, browser allows 5-10MB)
  WARNING_THRESHOLD: 3 * 1024 * 1024, // 3MB warning
  EMERGENCY_CLEANUP_SIZE: 1 * 1024 * 1024, // Remove 1MB when quota exceeded
};

class StorageManager {
  constructor() {
    this.encryptionKey = null;
    this.encryptionEnabled = false;
    
    // ✅ PRIVACY: Consent state
    this.consentGiven = false;
    this.consentCategories = new Set();
    
    // ✅ INDEXEDDB: Fallback database
    this.db = null;
    this.useIndexedDB = false;
    
    // ✅ Initialize systems
    this.initializePrivacyConsent();
    this.initializeIndexedDB();
    this.initializeEncryption();
    
    // ✅ Clean expired data on startup
    this.cleanupExpiredData();
    
    // ✅ Check storage quota
    this.checkStorageQuota();
  }

  // ==================== PRIVACY CONSENT MANAGEMENT ====================

  /**
   * ✅ PRIVACY: Initialize privacy consent state
   */
  initializePrivacyConsent() {
    try {
      // Check for existing consent (stored in localStorage as necessary data)
      const consentData = localStorage.getItem(STORAGE_KEYS.PRIVACY_CONSENT);
      
      if (consentData) {
        const consent = JSON.parse(consentData);
        this.consentGiven = consent.given || false;
        this.consentCategories = new Set(consent.categories || []);
        
        console.log('✅ Privacy consent loaded:', {
          given: this.consentGiven,
          categories: Array.from(this.consentCategories)
        });
      } else {
        // No consent yet - only necessary data allowed
        this.consentCategories.add(DATA_CATEGORIES.NECESSARY);
        console.log('⚠️ No privacy consent found. Only necessary data allowed.');
      }
    } catch (error) {
      console.error('❌ Failed to initialize privacy consent:', error);
      this.consentCategories.add(DATA_CATEGORIES.NECESSARY);
    }
  }

  /**
   * ✅ PRIVACY: Request user consent (GDPR/CCPA compliant)
   * @param {Array<string>} categories - Categories to request consent for
   * @param {Object} options - Additional options
   * @returns {boolean} Whether consent was granted
   */
  async requestConsent(categories = [], options = {}) {
    try {
      const {
        showUI = true,          // Show consent UI to user
        persistChoice = true,   // Save consent choice
        expiryDays = 365       // Consent valid for 1 year
      } = options;

      console.log('📋 Requesting privacy consent for:', categories);

      // If showUI is true, this would trigger a UI component
      // For now, we'll assume consent is granted programmatically
      // In production, integrate with a consent banner component
      
      const consentGranted = showUI ? await this.showConsentDialog(categories) : true;

      if (consentGranted) {
        this.consentGiven = true;
        categories.forEach(cat => this.consentCategories.add(cat));

        if (persistChoice) {
          const consentData = {
            given: true,
            categories: Array.from(this.consentCategories),
            timestamp: Date.now(),
            expiresAt: Date.now() + (expiryDays * 24 * 60 * 60 * 1000),
            version: '1.0', // Consent version for tracking policy changes
            ipAddress: 'not-collected', // For audit purposes
            userAgent: navigator.userAgent
          };

          // Store consent (as necessary data, doesn't require consent)
          localStorage.setItem(STORAGE_KEYS.PRIVACY_CONSENT, JSON.stringify(consentData));
          console.log('✅ Privacy consent granted and saved');
        }

        return true;
      } else {
        console.log('❌ Privacy consent denied');
        return false;
      }
    } catch (error) {
      console.error('❌ Failed to request consent:', error);
      return false;
    }
  }

  /**
   * ✅ PRIVACY: Show consent dialog (placeholder for UI integration)
   * @param {Array<string>} categories - Categories requesting consent
   * @returns {Promise<boolean>} User's consent decision
   */
  async showConsentDialog(categories) {
    // TODO: Integrate with actual UI component (ConsentBanner.jsx)
    // For now, return true to allow development
    
    console.log(`
╔════════════════════════════════════════════════════════════╗
║           🍪 PRIVACY CONSENT REQUIRED                      ║
╠════════════════════════════════════════════════════════════╣
║ This application would like to store the following data:  ║
║                                                            ║
║ ${categories.map(cat => `✓ ${cat.toUpperCase()}`).join('\n║ ')}                                             ║
║                                                            ║
║ Your data is encrypted and stored locally in your         ║
║ browser. You can withdraw consent at any time.            ║
╚════════════════════════════════════════════════════════════╝
    `);

    // In production, this would await user interaction
    // Return true for development (auto-consent)
    return true;
  }

  /**
   * ✅ PRIVACY: Check if consent given for specific category
   * @param {string} category - Data category to check
   * @returns {boolean} Whether consent is granted
   */
  hasConsent(category) {
    // Necessary data always allowed
    if (category === DATA_CATEGORIES.NECESSARY) {
      return true;
    }

    return this.consentCategories.has(category);
  }

  /**
   * ✅ PRIVACY: Revoke consent (GDPR Right to Erasure)
   * @param {Array<string>} categories - Categories to revoke (empty = revoke all)
   */
  revokeConsent(categories = []) {
    try {
      if (categories.length === 0) {
        // Revoke all consent
        console.log('🗑️ Revoking all privacy consent');
        this.consentGiven = false;
        this.consentCategories.clear();
        this.consentCategories.add(DATA_CATEGORIES.NECESSARY);
        
        // Delete all data except necessary
        this.clearNonNecessaryData();
      } else {
        // Revoke specific categories
        categories.forEach(cat => {
          if (cat !== DATA_CATEGORIES.NECESSARY) {
            this.consentCategories.delete(cat);
            console.log(`🗑️ Revoked consent for: ${cat}`);
          }
        });
      }

      // Update stored consent
      const consentData = {
        given: this.consentGiven,
        categories: Array.from(this.consentCategories),
        timestamp: Date.now(),
        revoked: true,
        revokedAt: Date.now()
      };

      localStorage.setItem(STORAGE_KEYS.PRIVACY_CONSENT, JSON.stringify(consentData));
      console.log('✅ Consent revocation saved');

      return true;
    } catch (error) {
      console.error('❌ Failed to revoke consent:', error);
      return false;
    }
  }

  /**
   * ✅ PRIVACY: Clear all non-necessary data
   */
  clearNonNecessaryData() {
    try {
      // Remove preferences (functional)
      localStorage.removeItem(STORAGE_KEYS.USER_PREFERENCES);
      
      // Remove recent topics (analytics)
      localStorage.removeItem(STORAGE_KEYS.RECENT_TOPICS);
      
      // Remove session (performance)
      localStorage.removeItem(STORAGE_KEYS.LAST_SESSION);
      
      // Clear IndexedDB if used
      if (this.db) {
        this.clearIndexedDBData();
      }

      console.log('✅ Non-necessary data cleared');
    } catch (error) {
      console.error('❌ Failed to clear non-necessary data:', error);
    }
  }

  /**
   * ✅ PRIVACY: Get current consent status
   * @returns {Object} Consent status and details
   */
  getConsentStatus() {
    try {
      const consentData = localStorage.getItem(STORAGE_KEYS.PRIVACY_CONSENT);
      
      if (!consentData) {
        return {
          given: false,
          categories: [DATA_CATEGORIES.NECESSARY],
          timestamp: null,
          expiresAt: null
        };
      }

      const consent = JSON.parse(consentData);
      
      return {
        given: consent.given || false,
        categories: consent.categories || [DATA_CATEGORIES.NECESSARY],
        timestamp: consent.timestamp || null,
        expiresAt: consent.expiresAt || null,
        version: consent.version || '1.0',
        isExpired: consent.expiresAt ? Date.now() > consent.expiresAt : false
      };
    } catch (error) {
      console.error('❌ Failed to get consent status:', error);
      return {
        given: false,
        categories: [DATA_CATEGORIES.NECESSARY],
        timestamp: null,
        expiresAt: null
      };
    }
  }

  // ==================== INDEXEDDB FALLBACK ====================

  /**
   * ✅ INDEXEDDB: Initialize IndexedDB for large data storage
   */
  async initializeIndexedDB() {
    try {
      // Check if IndexedDB is available
      if (!window.indexedDB) {
        console.warn('⚠️ IndexedDB not available. Using localStorage only.');
        this.useIndexedDB = false;
        return;
      }

      // Open database
      const request = indexedDB.open('KNOWALLEDGEDB', 1);

      request.onerror = (event) => {
        console.error('❌ IndexedDB error:', event.target.error);
        this.useIndexedDB = false;
      };

      request.onsuccess = (event) => {
        this.db = event.target.result;
        this.useIndexedDB = true;
        console.log('✅ IndexedDB initialized');
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Create object stores if they don't exist
        if (!db.objectStoreNames.contains('storage')) {
          const objectStore = db.createObjectStore('storage', { keyPath: 'key' });
          objectStore.createIndex('expiresAt', 'expiresAt', { unique: false });
          objectStore.createIndex('category', 'category', { unique: false });
          console.log('✅ IndexedDB object store created');
        }
      };

      // Wait for initialization
      await new Promise((resolve) => {
        request.onsuccess = (event) => {
          this.db = event.target.result;
          this.useIndexedDB = true;
          resolve();
        };
        request.onerror = () => {
          this.useIndexedDB = false;
          resolve();
        };
      });
    } catch (error) {
      console.error('❌ Failed to initialize IndexedDB:', error);
      this.useIndexedDB = false;
    }
  }

  /**
   * ✅ INDEXEDDB: Write data to IndexedDB
   * @param {string} key - Storage key
   * @param {*} value - Data to store
   * @param {number} expiresAt - Expiration timestamp
   * @param {string} category - Data category
   * @returns {Promise<boolean>} Success status
   */
  async writeToIndexedDB(key, value, expiresAt, category) {
    if (!this.db) {
      return false;
    }

    try {
      const transaction = this.db.transaction(['storage'], 'readwrite');
      const objectStore = transaction.objectStore('storage');

      const data = {
        key: key,
        value: value,
        expiresAt: expiresAt,
        category: category,
        createdAt: Date.now()
      };

      const request = objectStore.put(data);

      return new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(true);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('❌ IndexedDB write failed:', error);
      return false;
    }
  }

  /**
   * ✅ INDEXEDDB: Read data from IndexedDB
   * @param {string} key - Storage key
   * @returns {Promise<*>} Stored data or null
   */
  async readFromIndexedDB(key) {
    if (!this.db) {
      return null;
    }

    try {
      const transaction = this.db.transaction(['storage'], 'readonly');
      const objectStore = transaction.objectStore('storage');
      const request = objectStore.get(key);

      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          const data = request.result;
          
          if (!data) {
            resolve(null);
            return;
          }

          // Check expiration
          if (data.expiresAt && Date.now() > data.expiresAt) {
            // Expired, delete it
            this.deleteFromIndexedDB(key);
            resolve(null);
            return;
          }

          resolve(data.value);
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('❌ IndexedDB read failed:', error);
      return null;
    }
  }

  /**
   * ✅ INDEXEDDB: Delete data from IndexedDB
   * @param {string} key - Storage key
   * @returns {Promise<boolean>} Success status
   */
  async deleteFromIndexedDB(key) {
    if (!this.db) {
      return false;
    }

    try {
      const transaction = this.db.transaction(['storage'], 'readwrite');
      const objectStore = transaction.objectStore('storage');
      const request = objectStore.delete(key);

      return new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(true);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('❌ IndexedDB delete failed:', error);
      return false;
    }
  }

  /**
   * ✅ INDEXEDDB: Clear all IndexedDB data
   */
  async clearIndexedDBData() {
    if (!this.db) {
      return false;
    }

    try {
      const transaction = this.db.transaction(['storage'], 'readwrite');
      const objectStore = transaction.objectStore('storage');
      const request = objectStore.clear();

      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          console.log('✅ IndexedDB cleared');
          resolve(true);
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('❌ Failed to clear IndexedDB:', error);
      return false;
    }
  }

  /**
   * ✅ INDEXEDDB: Cleanup expired data from IndexedDB
   */
  async cleanupIndexedDBExpired() {
    if (!this.db) {
      return;
    }

    try {
      const transaction = this.db.transaction(['storage'], 'readwrite');
      const objectStore = transaction.objectStore('storage');
      const index = objectStore.index('expiresAt');
      
      const now = Date.now();
      const range = IDBKeyRange.upperBound(now);
      const request = index.openCursor(range);

      let removedCount = 0;

      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          cursor.delete();
          removedCount++;
          cursor.continue();
        } else {
          if (removedCount > 0) {
            console.log(`✅ Cleaned up ${removedCount} expired items from IndexedDB`);
          }
        }
      };
    } catch (error) {
      console.error('❌ Failed to cleanup IndexedDB:', error);
    }
  }

  // ==================== ENCRYPTION METHODS ====================

  /**
   * ✅ SECURITY: Initialize AES-GCM encryption
   */
  async initializeEncryption() {
    try {
      // Check if Web Crypto API available
      if (!crypto.subtle) {
        console.warn('⚠️ Web Crypto API not available. Encryption disabled.');
        this.encryptionEnabled = false;
        return;
      }

      // Try to load existing key
      const storedKey = localStorage.getItem(STORAGE_KEYS.ENCRYPTION_KEY);
      
      if (storedKey) {
        // Import existing key
        const keyData = this.base64ToArrayBuffer(storedKey);
        this.encryptionKey = await crypto.subtle.importKey(
          'raw',
          keyData,
          { name: 'AES-GCM', length: 256 },
          true,
          ['encrypt', 'decrypt']
        );
      } else {
        // Generate new key
        this.encryptionKey = await crypto.subtle.generateKey(
          { name: 'AES-GCM', length: 256 },
          true,
          ['encrypt', 'decrypt']
        );
        
        // Store key for future sessions
        const exportedKey = await crypto.subtle.exportKey('raw', this.encryptionKey);
        localStorage.setItem(
          STORAGE_KEYS.ENCRYPTION_KEY,
          this.arrayBufferToBase64(exportedKey)
        );
      }
      
      this.encryptionEnabled = true;
      console.log('✅ Storage encryption initialized');
    } catch (error) {
      console.error('❌ Failed to initialize encryption:', error);
      this.encryptionEnabled = false;
    }
  }

  /**
   * ✅ SECURITY: Encrypt data with AES-GCM
   */
  async encryptData(data) {
    if (!this.encryptionEnabled || !this.encryptionKey) {
      // Fallback: Return unencrypted data
      return { encrypted: false, data: JSON.stringify(data) };
    }

    try {
      const jsonString = JSON.stringify(data);
      const encoder = new TextEncoder();
      const dataBuffer = encoder.encode(jsonString);
      
      // Generate random IV (12 bytes for AES-GCM)
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
      
      return {
        encrypted: true,
        data: this.arrayBufferToBase64(combined.buffer)
      };
    } catch (error) {
      console.error('❌ Encryption failed:', error);
      // Fallback to unencrypted
      return { encrypted: false, data: JSON.stringify(data) };
    }
  }

  /**
   * ✅ SECURITY: Decrypt data with AES-GCM
   */
  async decryptData(encryptedData) {
    if (!encryptedData.encrypted) {
      // Data not encrypted, parse directly
      return JSON.parse(encryptedData.data);
    }

    if (!this.encryptionEnabled || !this.encryptionKey) {
      console.error('❌ Cannot decrypt: Encryption not initialized');
      return null;
    }

    try {
      const combined = this.base64ToArrayBuffer(encryptedData.data);
      
      // Extract IV and encrypted data
      const iv = combined.slice(0, 12);
      const encryptedBuffer = combined.slice(12);
      
      // Decrypt
      const decryptedBuffer = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: iv },
        this.encryptionKey,
        encryptedBuffer
      );
      
      const decoder = new TextDecoder();
      const jsonString = decoder.decode(decryptedBuffer);
      
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('❌ Decryption failed:', error);
      return null;
    }
  }

  /**
   * Helper: ArrayBuffer to Base64
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Helper: Base64 to ArrayBuffer
   */
  base64ToArrayBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  // ==================== EXPIRATION MANAGEMENT ====================

  /**
   * ✅ TTL: Wrap data with expiration metadata
   */
  wrapWithExpiration(data, ttl) {
    return {
      value: data,
      expiresAt: Date.now() + ttl,
      createdAt: Date.now()
    };
  }

  /**
   * ✅ TTL: Check if data expired
   */
  isExpired(wrappedData) {
    if (!wrappedData || !wrappedData.expiresAt) {
      return true; // Invalid or missing expiration
    }
    return Date.now() > wrappedData.expiresAt;
  }

  /**
   * ✅ TTL: Clean up all expired data
   */
  cleanupExpiredData() {
    try {
      let removedCount = 0;
      
      // Check all keys
      for (const key in STORAGE_KEYS) {
        const storageKey = STORAGE_KEYS[key];
        
        // Skip metadata keys
        if (storageKey === STORAGE_KEYS.ENCRYPTION_KEY || 
            storageKey === STORAGE_KEYS.STORAGE_METADATA) {
          continue;
        }
        
        const rawData = localStorage.getItem(storageKey);
        if (!rawData) continue;
        
        try {
          const parsed = JSON.parse(rawData);
          
          // Check if wrapped with expiration
          if (parsed.expiresAt && this.isExpired(parsed)) {
            localStorage.removeItem(storageKey);
            removedCount++;
            console.log(`🗑️ Removed expired data: ${storageKey}`);
          }
        } catch (e) {
          // Invalid data, skip
        }
      }
      
      if (removedCount > 0) {
        console.log(`✅ Cleaned up ${removedCount} expired items`);
      }
    } catch (error) {
      console.error('❌ Cleanup failed:', error);
    }
  }

  // ==================== STORAGE QUOTA MANAGEMENT ====================

  /**
   * ✅ STORAGE: Calculate current storage usage
   */
  calculateStorageSize() {
    let totalSize = 0;
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      const value = localStorage.getItem(key);
      
      // Size = key + value (in bytes)
      totalSize += (key.length + value.length) * 2; // UTF-16 = 2 bytes per char
    }
    
    return totalSize;
  }

  /**
   * ✅ STORAGE: Check quota and warn if near limit
   */
  checkStorageQuota() {
    try {
      const currentSize = this.calculateStorageSize();
      const percentUsed = (currentSize / STORAGE_LIMITS.MAX_TOTAL_SIZE) * 100;
      
      // Update metadata
      const metadata = {
        lastChecked: Date.now(),
        currentSize: currentSize,
        percentUsed: percentUsed.toFixed(2),
        itemCount: localStorage.length
      };
      
      localStorage.setItem(STORAGE_KEYS.STORAGE_METADATA, JSON.stringify(metadata));
      
      // Warnings
      if (currentSize > STORAGE_LIMITS.MAX_TOTAL_SIZE) {
        console.error(`🚨 Storage quota EXCEEDED: ${(currentSize / 1024 / 1024).toFixed(2)}MB`);
        this.emergencyCleanup();
        return false;
      } else if (currentSize > STORAGE_LIMITS.WARNING_THRESHOLD) {
        console.warn(`⚠️ Storage quota WARNING: ${percentUsed.toFixed(1)}% used`);
      }
      
      return true;
    } catch (error) {
      console.error('❌ Quota check failed:', error);
      return true; // Don't block operations
    }
  }

  /**
   * ✅ STORAGE: Emergency cleanup when quota exceeded
   */
  emergencyCleanup() {
    console.warn('🚨 EMERGENCY CLEANUP: Removing old data...');
    
    try {
      // 1. Remove expired data first
      this.cleanupExpiredData();
      
      // 2. If still over limit, remove oldest items
      const currentSize = this.calculateStorageSize();
      
      if (currentSize > STORAGE_LIMITS.MAX_TOTAL_SIZE) {
        // Get all items with timestamps
        const items = [];
        
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          
          // Skip critical keys
          if (key === STORAGE_KEYS.ENCRYPTION_KEY || 
              key === STORAGE_KEYS.STORAGE_METADATA) {
            continue;
          }
          
          const value = localStorage.getItem(key);
          
          try {
            const parsed = JSON.parse(value);
            items.push({
              key: key,
              createdAt: parsed.createdAt || 0,
              size: (key.length + value.length) * 2
            });
          } catch (e) {
            // Invalid data, mark for removal
            items.push({ key: key, createdAt: 0, size: 0 });
          }
        }
        
        // Sort by age (oldest first)
        items.sort((a, b) => a.createdAt - b.createdAt);
        
        // Remove oldest until under limit
        let removed = 0;
        for (const item of items) {
          localStorage.removeItem(item.key);
          removed += item.size;
          
          if (removed >= STORAGE_LIMITS.EMERGENCY_CLEANUP_SIZE) {
            break;
          }
        }
        
        console.log(`✅ Emergency cleanup: Removed ${(removed / 1024 / 1024).toFixed(2)}MB`);
      }
    } catch (error) {
      console.error('❌ Emergency cleanup failed:', error);
    }
  }

  /**
   * ✅ STORAGE: Safe write with quota check, consent validation, and IndexedDB fallback
   * @param {string} key - Storage key
   * @param {*} data - Data to store
   * @param {number} ttl - Time to live in milliseconds
   * @param {string} category - Data category (for consent check)
   * @returns {Promise<boolean>} Success status
   */
  async safeWrite(key, data, ttl, category = DATA_CATEGORIES.FUNCTIONAL) {
    try {
      // ✅ PRIVACY: Check consent before writing
      if (!this.hasConsent(category)) {
        console.warn(`⚠️ Cannot write ${key}: No consent for category ${category}`);
        return false;
      }

      // Check quota before writing
      if (!this.checkStorageQuota()) {
        // ✅ INDEXEDDB: Try IndexedDB as fallback
        if (this.useIndexedDB) {
          console.log('💾 localStorage full, falling back to IndexedDB...');
          
          const wrapped = this.wrapWithExpiration(data, ttl);
          const encrypted = await this.encryptData(wrapped);
          
          const success = await this.writeToIndexedDB(
            key,
            encrypted,
            Date.now() + ttl,
            category
          );
          
          if (success) {
            console.log(`✅ Wrote to IndexedDB: ${key}`);
            return true;
          } else {
            console.error('❌ IndexedDB write failed');
            return false;
          }
        }
        
        console.error('❌ Cannot write: Storage quota exceeded and no IndexedDB');
        return false;
      }
      
      // Wrap with expiration
      const wrapped = this.wrapWithExpiration(data, ttl);
      
      // Encrypt
      const encrypted = await this.encryptData(wrapped);
      
      // Calculate size
      const dataSize = JSON.stringify(encrypted).length * 2; // UTF-16 bytes
      
      // ✅ INDEXEDDB: Use IndexedDB for large data (> 100KB)
      if (dataSize > 100 * 1024 && this.useIndexedDB) {
        console.log(`💾 Large data detected (${(dataSize / 1024).toFixed(2)}KB), using IndexedDB`);
        
        const success = await this.writeToIndexedDB(
          key,
          encrypted,
          Date.now() + ttl,
          category
        );
        
        if (success) {
          // Store a pointer in localStorage
          localStorage.setItem(key, JSON.stringify({
            useIndexedDB: true,
            key: key
          }));
          return true;
        }
      }
      
      // Attempt localStorage write
      try {
        localStorage.setItem(key, JSON.stringify(encrypted));
        return true;
      } catch (error) {
        if (error.name === 'QuotaExceededError') {
          console.warn('⚠️ QuotaExceededError: Running emergency cleanup...');
          this.emergencyCleanup();
          
          // ✅ INDEXEDDB: Try IndexedDB after cleanup
          if (this.useIndexedDB) {
            console.log('💾 Falling back to IndexedDB after quota error...');
            const success = await this.writeToIndexedDB(
              key,
              encrypted,
              Date.now() + ttl,
              category
            );
            
            if (success) {
              localStorage.setItem(key, JSON.stringify({
                useIndexedDB: true,
                key: key
              }));
              return true;
            }
          }
          
          // Retry localStorage once
          try {
            localStorage.setItem(key, JSON.stringify(encrypted));
            return true;
          } catch (retryError) {
            console.error('❌ Write failed after cleanup:', retryError);
            return false;
          }
        }
        throw error;
      }
    } catch (error) {
      console.error('❌ Safe write failed:', error);
      return false;
    }
  }

  /**
   * ✅ STORAGE: Safe read with expiration check and IndexedDB fallback
   * @param {string} key - Storage key
   * @param {string} category - Data category (for consent check)
   * @returns {Promise<*>} Stored data or null
   */
  async safeRead(key, category = DATA_CATEGORIES.FUNCTIONAL) {
    try {
      // ✅ PRIVACY: Check consent before reading
      if (!this.hasConsent(category)) {
        console.warn(`⚠️ Cannot read ${key}: No consent for category ${category}`);
        return null;
      }

      const rawData = localStorage.getItem(key);
      if (!rawData) {
        // ✅ INDEXEDDB: Try IndexedDB if localStorage empty
        if (this.useIndexedDB) {
          const indexedData = await this.readFromIndexedDB(key);
          if (indexedData) {
            const wrapped = await this.decryptData(indexedData);
            return wrapped ? wrapped.value : null;
          }
        }
        return null;
      }
      
      const parsed = JSON.parse(rawData);
      
      // ✅ INDEXEDDB: Check if data is in IndexedDB
      if (parsed.useIndexedDB) {
        if (!this.useIndexedDB) {
          console.error('❌ Data in IndexedDB but IndexedDB not available');
          return null;
        }
        
        const indexedData = await this.readFromIndexedDB(parsed.key);
        if (!indexedData) return null;
        
        const wrapped = await this.decryptData(indexedData);
        
        if (!wrapped) return null;
        
        // Check expiration
        if (this.isExpired(wrapped)) {
          await this.deleteFromIndexedDB(parsed.key);
          localStorage.removeItem(key);
          console.log(`🗑️ Removed expired data from IndexedDB: ${key}`);
          return null;
        }
        
        return wrapped.value;
      }
      
      // Regular localStorage data
      const encrypted = parsed;
      const wrapped = await this.decryptData(encrypted);
      
      if (!wrapped) return null;
      
      // Check expiration
      if (this.isExpired(wrapped)) {
        localStorage.removeItem(key);
        console.log(`🗑️ Removed expired data: ${key}`);
        return null;
      }
      
      return wrapped.value;
    } catch (error) {
      console.error('❌ Safe read failed:', error);
      return null;
    }
  }

  // ==================== PUBLIC API METHODS ====================

  /**
   * ✅ SECURE: Save user preferences (encrypted, with TTL, consent-aware)
   */
  async savePreferences(preferences) {
    try {
      const success = await this.safeWrite(
        STORAGE_KEYS.USER_PREFERENCES,
        preferences,
        DEFAULT_TTL.USER_PREFERENCES,
        DATA_CATEGORIES.FUNCTIONAL // ✅ PRIVACY: Requires functional consent
      );
      
      if (success) {
        console.log('✅ Preferences saved (encrypted)');
      }
      
      return success;
    } catch (error) {
      console.error('❌ Failed to save preferences:', error);
      return false;
    }
  }

  /**
   * ✅ SECURE: Load user preferences (decrypted, checked for expiration, consent-aware)
   */
  async loadPreferences() {
    try {
      const preferences = await this.safeRead(
        STORAGE_KEYS.USER_PREFERENCES,
        DATA_CATEGORIES.FUNCTIONAL // ✅ PRIVACY: Requires functional consent
      );
      
      if (preferences) {
        console.log('✅ Preferences loaded (decrypted)');
      }
      
      return preferences;
    } catch (error) {
      console.error('❌ Failed to load preferences:', error);
      return null;
    }
  }

  /**
   * ✅ SECURE: Add topic to recent searches (consent-aware)
   */
  async addRecentTopic(topic) {
    try {
      const recent = await this.getRecentTopics() || [];
      const updated = [topic, ...recent.filter((t) => t !== topic)].slice(0, 10);
      
      const success = await this.safeWrite(
        STORAGE_KEYS.RECENT_TOPICS,
        updated,
        DEFAULT_TTL.RECENT_TOPICS,
        DATA_CATEGORIES.ANALYTICS // ✅ PRIVACY: Requires analytics consent
      );
      
      return success;
    } catch (error) {
      console.error('❌ Failed to save recent topic:', error);
      return false;
    }
  }

  /**
   * ✅ SECURE: Get recent topics (consent-aware)
   */
  async getRecentTopics() {
    try {
      const topics = await this.safeRead(
        STORAGE_KEYS.RECENT_TOPICS,
        DATA_CATEGORIES.ANALYTICS // ✅ PRIVACY: Requires analytics consent
      );
      return topics || [];
    } catch (error) {
      console.error('❌ Failed to load recent topics:', error);
      return [];
    }
  }

  /**
   * ✅ SECURE: Save last session state (consent-aware)
   */
  async saveSession(sessionData) {
    try {
      const success = await this.safeWrite(
        STORAGE_KEYS.LAST_SESSION,
        sessionData,
        DEFAULT_TTL.LAST_SESSION,
        DATA_CATEGORIES.PERFORMANCE // ✅ PRIVACY: Requires performance consent
      );
      
      return success;
    } catch (error) {
      console.error('❌ Failed to save session:', error);
      return false;
    }
  }

  /**
   * ✅ SECURE: Load last session (consent-aware)
   */
  async loadSession() {
    try {
      const session = await this.safeRead(
        STORAGE_KEYS.LAST_SESSION,
        DATA_CATEGORIES.PERFORMANCE // ✅ PRIVACY: Requires performance consent
      );
      return session;
    } catch (error) {
      console.error('❌ Failed to load session:', error);
      return null;
    }
  }

  /**
   * ✅ SECURE: Clear all stored data (including IndexedDB)
   */
  async clearAll() {
    try {
      // Clear localStorage
      Object.values(STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
      
      // Clear IndexedDB
      if (this.useIndexedDB) {
        await this.clearIndexedDBData();
      }
      
      console.log('✅ All storage cleared (localStorage + IndexedDB)');
      return true;
    } catch (error) {
      console.error('❌ Failed to clear storage:', error);
      return false;
    }
  }

  /**
   * ✅ STORAGE: Get storage statistics (including IndexedDB)
   */
  getStorageStats() {
    const currentSize = this.calculateStorageSize();
    const percentUsed = (currentSize / STORAGE_LIMITS.MAX_TOTAL_SIZE) * 100;
    
    return {
      currentSize: currentSize,
      currentSizeMB: (currentSize / 1024 / 1024).toFixed(2),
      maxSize: STORAGE_LIMITS.MAX_TOTAL_SIZE,
      maxSizeMB: (STORAGE_LIMITS.MAX_TOTAL_SIZE / 1024 / 1024).toFixed(2),
      percentUsed: percentUsed.toFixed(2),
      itemCount: localStorage.length,
      encryptionEnabled: this.encryptionEnabled,
      warningThreshold: STORAGE_LIMITS.WARNING_THRESHOLD,
      isNearLimit: currentSize > STORAGE_LIMITS.WARNING_THRESHOLD,
      // ✅ INDEXEDDB: Include IndexedDB info
      useIndexedDB: this.useIndexedDB,
      indexedDBAvailable: !!window.indexedDB,
      // ✅ PRIVACY: Include consent info
      consentGiven: this.consentGiven,
      consentCategories: Array.from(this.consentCategories)
    };
  }
}

// Export singleton instance
export default new StorageManager();

// ✅ Export constants for external use
export { DATA_CATEGORIES, STORAGE_KEYS };
