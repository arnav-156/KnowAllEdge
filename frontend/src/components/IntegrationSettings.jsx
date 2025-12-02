import React, { useState, useEffect } from 'react';
import './IntegrationSettings.css';

const IntegrationSettings = ({ userId }) => {
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [formData, setFormData] = useState({
    api_key: '',
    webhook_url: '',
    sync_enabled: true,
    settings: {}
  });

  const platforms = [
    {
      id: 'notion',
      name: 'Notion',
      icon: '📓',
      description: 'Sync notes to Notion workspace',
      fields: ['api_key', 'database_id']
    },
    {
      id: 'obsidian',
      name: 'Obsidian',
      icon: '💎',
      description: 'Export to Obsidian vault',
      fields: ['vault_path']
    },
    {
      id: 'onenote',
      name: 'OneNote',
      icon: '📔',
      description: 'Sync to Microsoft OneNote',
      fields: ['api_key', 'notebook_id']
    }
  ];

  useEffect(() => {
    fetchIntegrations();
  }, [userId]);

  const fetchIntegrations = async () => {
    try {
      const response = await fetch(`/api/study-tools/integrations?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setIntegrations(Array.isArray(data.integrations) ? data.integrations : []);
      }
    } catch (error) {
      console.error('Error fetching integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigurePlatform = (platform) => {
    setSelectedPlatform(platform);
    
    const existing = integrations.find(i => i.platform === platform.id);
    if (existing) {
      setFormData({
        api_key: existing.api_key || '',
        webhook_url: existing.webhook_url || '',
        sync_enabled: existing.sync_enabled,
        settings: existing.settings || {}
      });
    } else {
      setFormData({
        api_key: '',
        webhook_url: '',
        sync_enabled: true,
        settings: {}
      });
    }
  };

  const handleSaveIntegration = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`/api/study-tools/integrations/${selectedPlatform.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (data.success) {
        fetchIntegrations();
        setSelectedPlatform(null);
        alert(`${selectedPlatform.name} integration configured!`);
      }
    } catch (error) {
      console.error('Error saving integration:', error);
      alert('Failed to save integration');
    }
  };

  const handleTestConnection = async (platformId) => {
    try {
      const response = await fetch(`/api/study-tools/integrations/${platformId}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert(`✓ ${platformId} connection successful!`);
      } else {
        alert(`✗ Connection failed: ${data.error}`);
      }
    } catch (error) {
      console.error('Error testing connection:', error);
      alert('Connection test failed');
    }
  };

  const handleSync = async (platformId) => {
    try {
      const response = await fetch(`/api/study-tools/integrations/${platformId}/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          content: {} // Would include actual content to sync
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert(`✓ Synced to ${platformId}!`);
        fetchIntegrations();
      }
    } catch (error) {
      console.error('Error syncing:', error);
      alert('Sync failed');
    }
  };

  const getIntegrationStatus = (platformId) => {
    const integration = integrations.find(i => i.platform === platformId);
    return integration ? 'connected' : 'not_connected';
  };

  const getLastSync = (platformId) => {
    const integration = integrations.find(i => i.platform === platformId);
    return integration?.last_sync 
      ? new Date(integration.last_sync).toLocaleString()
      : 'Never';
  };

  if (loading) {
    return <div className="integration-settings-loading">Loading integrations...</div>;
  }

  return (
    <div className="integration-settings">
      <div className="integration-header">
        <h2>Integration Settings</h2>
        <p>Connect KnowAllEdge with your favorite tools</p>
      </div>

      <div className="platforms-grid">
        {platforms.map(platform => {
          const status = getIntegrationStatus(platform.id);
          const isConnected = status === 'connected';
          
          return (
            <div key={platform.id} className={`platform-card ${isConnected ? 'connected' : ''}`}>
              <div className="platform-icon">{platform.icon}</div>
              <h3>{platform.name}</h3>
              <p>{platform.description}</p>
              
              <div className="platform-status">
                <span className={`status-badge ${status}`}>
                  {isConnected ? '✓ Connected' : '○ Not Connected'}
                </span>
              </div>

              {isConnected && (
                <div className="platform-info">
                  <div className="info-item">
                    <span className="info-label">Last Sync:</span>
                    <span className="info-value">{getLastSync(platform.id)}</span>
                  </div>
                </div>
              )}

              <div className="platform-actions">
                <button 
                  className="configure-btn"
                  onClick={() => handleConfigurePlatform(platform)}
                >
                  {isConnected ? 'Reconfigure' : 'Configure'}
                </button>
                
                {isConnected && (
                  <>
                    <button 
                      className="test-btn"
                      onClick={() => handleTestConnection(platform.id)}
                    >
                      Test
                    </button>
                    <button 
                      className="sync-btn"
                      onClick={() => handleSync(platform.id)}
                    >
                      Sync
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {selectedPlatform && (
        <div className="config-modal" onClick={() => setSelectedPlatform(null)}>
          <div className="config-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Configure {selectedPlatform.name}</h3>
              <button className="close-btn" onClick={() => setSelectedPlatform(null)}>×</button>
            </div>

            <form onSubmit={handleSaveIntegration}>
              {selectedPlatform.fields.includes('api_key') && (
                <div className="form-group">
                  <label>API Key *</label>
                  <input
                    type="password"
                    value={formData.api_key}
                    onChange={(e) => setFormData({...formData, api_key: e.target.value})}
                    required
                    placeholder="Enter your API key"
                  />
                  <small>Get your API key from {selectedPlatform.name} settings</small>
                </div>
              )}

              {selectedPlatform.fields.includes('database_id') && (
                <div className="form-group">
                  <label>Database ID</label>
                  <input
                    type="text"
                    value={formData.settings.database_id || ''}
                    onChange={(e) => setFormData({
                      ...formData, 
                      settings: {...formData.settings, database_id: e.target.value}
                    })}
                    placeholder="Notion database ID"
                  />
                </div>
              )}

              {selectedPlatform.fields.includes('notebook_id') && (
                <div className="form-group">
                  <label>Notebook ID</label>
                  <input
                    type="text"
                    value={formData.settings.notebook_id || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      settings: {...formData.settings, notebook_id: e.target.value}
                    })}
                    placeholder="OneNote notebook ID"
                  />
                </div>
              )}

              {selectedPlatform.fields.includes('vault_path') && (
                <div className="form-group">
                  <label>Vault Path</label>
                  <input
                    type="text"
                    value={formData.settings.vault_path || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      settings: {...formData.settings, vault_path: e.target.value}
                    })}
                    placeholder="/path/to/obsidian/vault"
                  />
                </div>
              )}

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.sync_enabled}
                    onChange={(e) => setFormData({...formData, sync_enabled: e.target.checked})}
                  />
                  <span>Enable automatic sync</span>
                </label>
              </div>

              <div className="form-actions">
                <button type="submit" className="save-btn">Save Configuration</button>
                <button type="button" className="cancel-btn" onClick={() => setSelectedPlatform(null)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationSettings;
