import React, { useState, useEffect } from 'react';
import './OfflineIndicator.css';
import syncManager from '../utils/syncManager';

const OfflineIndicator = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingActions, setPendingActions] = useState(0);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      syncManager.syncNow();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check pending actions
    updatePendingCount();
    const interval = setInterval(updatePendingCount, 5000);

    // Listen for sync events
    syncManager.onSync(() => {
      updatePendingCount();
      setSyncing(false);
    });

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  const updatePendingCount = async () => {
    const count = await syncManager.getPendingCount();
    setPendingActions(count);
  };

  const handleSync = async () => {
    setSyncing(true);
    await syncManager.syncNow();
    setSyncing(false);
  };

  if (isOnline && pendingActions === 0) {
    return null;
  }

  return (
    <div className={`offline-indicator ${isOnline ? 'online' : 'offline'}`}>
      <div className="indicator-content">
        <span className="indicator-icon">
          {isOnline ? '🔄' : '📡'}
        </span>
        <span className="indicator-text">
          {isOnline 
            ? `${pendingActions} action${pendingActions !== 1 ? 's' : ''} pending sync`
            : 'You are offline'}
        </span>
        {isOnline && pendingActions > 0 && (
          <button 
            className="sync-btn" 
            onClick={handleSync}
            disabled={syncing}
          >
            {syncing ? 'Syncing...' : 'Sync Now'}
          </button>
        )}
      </div>
    </div>
  );
};

export default OfflineIndicator;
