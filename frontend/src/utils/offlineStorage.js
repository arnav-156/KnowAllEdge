/**
 * Offline Storage Utility
 * Manages IndexedDB for offline data storage and sync queue
 */

const DB_NAME = 'KNOWALLEDGE-offline';
const DB_VERSION = 1;

// Object stores
const STORES = {
  MAPS: 'concept-maps',
  NOTES: 'study-notes',
  ANALYTICS: 'analytics-data',
  SYNC_QUEUE: 'sync-queue',
  CACHE_META: 'cache-metadata'
};

class OfflineStorage {
  constructor() {
    this.db = null;
  }

  /**
   * Initialize IndexedDB
   */
  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Create object stores
        if (!db.objectStoreNames.contains(STORES.MAPS)) {
          const mapsStore = db.createObjectStore(STORES.MAPS, { keyPath: 'id' });
          mapsStore.createIndex('userId', 'userId', { unique: false });
          mapsStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORES.NOTES)) {
          const notesStore = db.createObjectStore(STORES.NOTES, { keyPath: 'id' });
          notesStore.createIndex('userId', 'userId', { unique: false });
          notesStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORES.ANALYTICS)) {
          const analyticsStore = db.createObjectStore(STORES.ANALYTICS, { keyPath: 'id' });
          analyticsStore.createIndex('userId', 'userId', { unique: false });
          analyticsStore.createIndex('type', 'type', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORES.SYNC_QUEUE)) {
          const syncStore = db.createObjectStore(STORES.SYNC_QUEUE, { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          syncStore.createIndex('timestamp', 'timestamp', { unique: false });
          syncStore.createIndex('status', 'status', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORES.CACHE_META)) {
          db.createObjectStore(STORES.CACHE_META, { keyPath: 'key' });
        }
      };
    });
  }

  /**
   * Save data to store
   */
  async save(storeName, data) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.put(data);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  /**
   * Get data from store
   */
  async get(storeName, id) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.get(id);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  /**
   * Get all data from store
   */
  async getAll(storeName, indexName = null, indexValue = null) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      
      let request;
      if (indexName && indexValue) {
        const index = store.index(indexName);
        request = index.getAll(indexValue);
      } else {
        request = store.getAll();
      }

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  /**
   * Delete data from store
   */
  async delete(storeName, id) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.delete(id);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  /**
   * Clear all data from store
   */
  async clear(storeName) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.clear();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  /**
   * Add action to sync queue
   */
  async addToSyncQueue(action) {
    const queueItem = {
      ...action,
      timestamp: Date.now(),
      status: 'pending',
      retries: 0
    };

    return this.save(STORES.SYNC_QUEUE, queueItem);
  }

  /**
   * Get pending sync actions
   */
  async getPendingSyncActions() {
    return this.getAll(STORES.SYNC_QUEUE, 'status', 'pending');
  }

  /**
   * Mark sync action as complete
   */
  async completeSyncAction(id) {
    return this.delete(STORES.SYNC_QUEUE, id);
  }

  /**
   * Save concept map offline
   */
  async saveConceptMap(map, userId) {
    const data = {
      ...map,
      userId,
      timestamp: Date.now(),
      offline: true
    };

    return this.save(STORES.MAPS, data);
  }

  /**
   * Get offline concept maps
   */
  async getOfflineConceptMaps(userId) {
    return this.getAll(STORES.MAPS, 'userId', userId);
  }

  /**
   * Save study note offline
   */
  async saveStudyNote(note, userId) {
    const data = {
      ...note,
      userId,
      timestamp: Date.now(),
      offline: true
    };

    return this.save(STORES.NOTES, data);
  }

  /**
   * Get offline study notes
   */
  async getOfflineStudyNotes(userId) {
    return this.getAll(STORES.NOTES, 'userId', userId);
  }

  /**
   * Cache analytics data
   */
  async cacheAnalytics(type, data, userId) {
    const cacheData = {
      id: `${userId}-${type}`,
      userId,
      type,
      data,
      timestamp: Date.now()
    };

    return this.save(STORES.ANALYTICS, cacheData);
  }

  /**
   * Get cached analytics
   */
  async getCachedAnalytics(type, userId) {
    const id = `${userId}-${type}`;
    return this.get(STORES.ANALYTICS, id);
  }

  /**
   * Set cache metadata
   */
  async setCacheMetadata(key, value) {
    return this.save(STORES.CACHE_META, { key, value, timestamp: Date.now() });
  }

  /**
   * Get cache metadata
   */
  async getCacheMetadata(key) {
    const result = await this.get(STORES.CACHE_META, key);
    return result ? result.value : null;
  }

  /**
   * Get storage usage
   */
  async getStorageUsage() {
    if (!navigator.storage || !navigator.storage.estimate) {
      return { usage: 0, quota: 0, percentage: 0 };
    }

    const estimate = await navigator.storage.estimate();
    return {
      usage: estimate.usage,
      quota: estimate.quota,
      percentage: Math.round((estimate.usage / estimate.quota) * 100)
    };
  }

  /**
   * Request persistent storage
   */
  async requestPersistentStorage() {
    if (navigator.storage && navigator.storage.persist) {
      const isPersisted = await navigator.storage.persist();
      console.log(`Persistent storage: ${isPersisted ? 'granted' : 'denied'}`);
      return isPersisted;
    }
    return false;
  }
}

// Export singleton instance
const offlineStorage = new OfflineStorage();
export default offlineStorage;

// Export store names for convenience
export { STORES };
