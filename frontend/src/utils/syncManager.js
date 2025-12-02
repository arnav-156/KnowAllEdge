/**
 * Sync Manager
 * Handles background sync and offline action queue
 */

import offlineStorage, { STORES } from './offlineStorage';

class SyncManager {
  constructor() {
    this.syncing = false;
    this.syncCallbacks = [];
  }

  /**
   * Register background sync
   */
  async registerSync(tag = 'sync-offline-actions') {
    if ('serviceWorker' in navigator && 'SyncManager' in window) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register(tag);
        console.log('Background sync registered:', tag);
        return true;
      } catch (error) {
        console.error('Background sync registration failed:', error);
        // Fallback to manual sync
        this.syncNow();
        return false;
      }
    }
    
    // Fallback for browsers without background sync
    this.syncNow();
    return false;
  }

  /**
   * Sync now (manual sync)
   */
  async syncNow() {
    if (this.syncing) {
      console.log('Sync already in progress');
      return;
    }

    if (!navigator.onLine) {
      console.log('Cannot sync: offline');
      return;
    }

    this.syncing = true;
    console.log('Starting manual sync...');

    try {
      const actions = await offlineStorage.getPendingSyncActions();
      console.log(`Syncing ${actions.length} actions`);

      for (const action of actions) {
        try {
          await this.syncAction(action);
          await offlineStorage.completeSyncAction(action.id);
          console.log('Action synced:', action.id);
        } catch (error) {
          console.error('Failed to sync action:', action.id, error);
          
          // Increment retry count
          action.retries = (action.retries || 0) + 1;
          
          // Remove if too many retries
          if (action.retries > 3) {
            await offlineStorage.completeSyncAction(action.id);
            console.log('Action removed after max retries:', action.id);
          } else {
            await offlineStorage.save(STORES.SYNC_QUEUE, action);
          }
        }
      }

      // Notify callbacks
      this.syncCallbacks.forEach(callback => callback());
      
      console.log('Sync complete');
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      this.syncing = false;
    }
  }

  /**
   * Sync individual action
   */
  async syncAction(action) {
    const response = await fetch(action.url, {
      method: action.method || 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...action.headers
      },
      body: action.body ? JSON.stringify(action.body) : undefined
    });

    if (!response.ok) {
      throw new Error(`Sync failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Add sync callback
   */
  onSync(callback) {
    this.syncCallbacks.push(callback);
  }

  /**
   * Queue action for sync
   */
  async queueAction(url, method, body, headers = {}) {
    const action = {
      url,
      method,
      body,
      headers,
      timestamp: Date.now()
    };

    await offlineStorage.addToSyncQueue(action);
    console.log('Action queued for sync:', url);

    // Try to sync immediately if online
    if (navigator.onLine) {
      this.registerSync();
    }
  }

  /**
   * Get pending actions count
   */
  async getPendingCount() {
    const actions = await offlineStorage.getPendingSyncActions();
    return actions.length;
  }
}

// Export singleton
const syncManager = new SyncManager();
export default syncManager;
