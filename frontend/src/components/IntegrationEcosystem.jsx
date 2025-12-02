import React, { useState, useEffect } from 'react';
import './IntegrationEcosystem.css';

const IntegrationEcosystem = ({ userId }) => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [apiKeys, setApiKeys] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [logs, setLogs] = useState([]);
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [newApiKey, setNewApiKey] = useState(null);

  const integrationTypes = {
    lms: [
      { id: 'canvas', name: 'Canvas LMS', icon: '🎨', description: 'Sync courses and assignments from Canvas' },
      { id: 'blackboard', name: 'Blackboard', icon: '📚', description: 'Connect to Blackboard Learn' },
      { id: 'moodle', name: 'Moodle', icon: '🎓', description: 'Integrate with Moodle platform' }
    ],
    calendar: [
      { id: 'google_calendar', name: 'Google Calendar', icon: '📅', description: 'Sync study sessions with Google Calendar' },
      { id: 'outlook', name: 'Outlook Calendar', icon: '📆', description: 'Connect to Microsoft Outlook' },
      { id: 'apple_calendar', name: 'Apple Calendar', icon: '🍎', description: 'Sync with iCloud Calendar' }
    ],
    classroom: [
      { id: 'google_classroom', name: 'Google Classroom', icon: '🏫', description: 'Import assignments from Google Classroom' }
    ]
  };

  useEffect(() => {
    fetchOverview();
    if (activeTab === 'api-keys') fetchApiKeys();
    if (activeTab === 'webhooks') fetchWebhooks();
    if (activeTab === 'logs') fetchLogs();
  }, [userId, activeTab]);

  const fetchOverview = async () => {
    try {
      const response = await fetch(`/api/integrations/overview?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setOverview(data.overview);
      }
    } catch (error) {
      console.error('Error fetching overview:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchApiKeys = async () => {
    try {
      const response = await fetch(`/api/integrations/api-keys?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setApiKeys(data.api_keys);
      }
    } catch (error) {
      console.error('Error fetching API keys:', error);
    }
  };

  const fetchWebhooks = async () => {
    try {
      const response = await fetch(`/api/integrations/webhooks?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setWebhooks(data.webhooks);
      }
    } catch (error) {
      console.error('Error fetching webhooks:', error);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await fetch(`/api/integrations/logs?user_id=${userId}&limit=50`);
      const data = await response.json();
      
      if (data.success) {
        setLogs(data.logs);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const handleConnect = (type, integration) => {
    setSelectedIntegration({ type, ...integration });
    setShowConnectionModal(true);
  };

  const handleSync = async (type, integrationId) => {
    try {
      let endpoint = '';
      let body = {};

      if (type === 'lms') {
        endpoint = '/api/integrations/lms/sync';
        body = { lms_type: integrationId };
      } else if (type === 'calendar') {
        endpoint = '/api/integrations/calendar/sync';
        body = { calendar_type: integrationId };
      } else if (type === 'classroom') {
        endpoint = '/api/integrations/google-classroom/sync';
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(body)
      });

      const data = await response.json();
      
      if (data.success) {
        alert('Sync completed successfully!');
        fetchOverview();
      } else {
        alert(data.error || 'Sync failed');
      }
    } catch (error) {
      console.error('Error syncing:', error);
      alert('Sync failed');
    }
  };

  const handleGenerateApiKey = async (keyData) => {
    try {
      const response = await fetch('/api/integrations/api-keys/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(keyData)
      });

      const data = await response.json();
      
      if (data.success) {
        setNewApiKey(data);
        fetchApiKeys();
      } else {
        alert(data.error || 'Failed to generate API key');
      }
    } catch (error) {
      console.error('Error generating API key:', error);
      alert('Failed to generate API key');
    }
  };

  const handleRevokeApiKey = async (keyId) => {
    if (!confirm('Are you sure you want to revoke this API key?')) return;

    try {
      const response = await fetch(`/api/integrations/api-keys/${keyId}/revoke`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
        alert('API key revoked');
        fetchApiKeys();
      }
    } catch (error) {
      console.error('Error revoking API key:', error);
      alert('Failed to revoke API key');
    }
  };

  const getConnectionStatus = (type, integrationId) => {
    if (!overview) return 'disconnected';

    if (type === 'lms' && overview.lms && overview.lms.lms_type === integrationId) {
      return 'connected';
    }
    if (type === 'calendar' && overview.calendar && overview.calendar.calendar_type === integrationId) {
      return 'connected';
    }
    if (type === 'classroom' && overview.google_classroom) {
      return 'connected';
    }

    return 'disconnected';
  };

  const renderOverview = () => {
    if (!overview) return null;

    return (
      <div className="overview-content">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">🔗</div>
            <div className="stat-content">
              <div className="stat-value">
                {(overview.lms ? 1 : 0) + (overview.google_classroom ? 1 : 0) + (overview.calendar ? 1 : 0)}
              </div>
              <div className="stat-label">Active Integrations</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🔑</div>
            <div className="stat-content">
              <div className="stat-value">{overview.api_keys_count}</div>
              <div className="stat-label">API Keys</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🪝</div>
            <div className="stat-content">
              <div className="stat-value">{overview.webhooks_count}</div>
              <div className="stat-label">Webhooks</div>
            </div>
          </div>
        </div>

        <div className="integrations-sections">
          {/* LMS Section */}
          <div className="integration-section">
            <h3>🎓 Learning Management Systems</h3>
            <div className="integration-grid">
              {integrationTypes.lms.map(lms => {
                const status = getConnectionStatus('lms', lms.id);
                return (
                  <div key={lms.id} className={`integration-card ${status}`}>
                    <div className="card-icon">{lms.icon}</div>
                    <div className="card-content">
                      <h4>{lms.name}</h4>
                      <p>{lms.description}</p>
                    </div>
                    <div className="card-actions">
                      {status === 'connected' ? (
                        <>
                          <button onClick={() => handleSync('lms', lms.id)}>Sync Now</button>
                          <span className="status-badge connected">Connected</span>
                        </>
                      ) : (
                        <button onClick={() => handleConnect('lms', lms)}>Connect</button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Google Classroom Section */}
          <div className="integration-section">
            <h3>🏫 Google Classroom</h3>
            <div className="integration-grid">
              {integrationTypes.classroom.map(classroom => {
                const status = getConnectionStatus('classroom', classroom.id);
                return (
                  <div key={classroom.id} className={`integration-card ${status}`}>
                    <div className="card-icon">{classroom.icon}</div>
                    <div className="card-content">
                      <h4>{classroom.name}</h4>
                      <p>{classroom.description}</p>
                    </div>
                    <div className="card-actions">
                      {status === 'connected' ? (
                        <>
                          <button onClick={() => handleSync('classroom', classroom.id)}>Sync Now</button>
                          <span className="status-badge connected">Connected</span>
                        </>
                      ) : (
                        <button onClick={() => handleConnect('classroom', classroom)}>Connect</button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Calendar Section */}
          <div className="integration-section">
            <h3>📅 Calendar Apps</h3>
            <div className="integration-grid">
              {integrationTypes.calendar.map(calendar => {
                const status = getConnectionStatus('calendar', calendar.id);
                return (
                  <div key={calendar.id} className={`integration-card ${status}`}>
                    <div className="card-icon">{calendar.icon}</div>
                    <div className="card-content">
                      <h4>{calendar.name}</h4>
                      <p>{calendar.description}</p>
                    </div>
                    <div className="card-actions">
                      {status === 'connected' ? (
                        <>
                          <button onClick={() => handleSync('calendar', calendar.id)}>Sync Now</button>
                          <span className="status-badge connected">Connected</span>
                        </>
                      ) : (
                        <button onClick={() => handleConnect('calendar', calendar)}>Connect</button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderApiKeys = () => {
    return (
      <div className="api-keys-content">
        <div className="section-header">
          <h3>API Keys for Developers</h3>
          <button className="primary-btn" onClick={() => setShowApiKeyModal(true)}>
            + Generate New Key
          </button>
        </div>

        {apiKeys.length === 0 ? (
          <div className="empty-state">
            <p>No API keys generated yet</p>
            <button onClick={() => setShowApiKeyModal(true)}>Generate Your First API Key</button>
          </div>
        ) : (
          <div className="api-keys-list">
            {apiKeys.map(key => (
              <div key={key.id} className={`api-key-card ${key.is_active ? 'active' : 'inactive'}`}>
                <div className="key-header">
                  <h4>{key.name}</h4>
                  <span className={`status-badge ${key.is_active ? 'active' : 'inactive'}`}>
                    {key.is_active ? 'Active' : 'Revoked'}
                  </span>
                </div>
                <p className="key-description">{key.description}</p>
                <div className="key-details">
                  <div className="detail-item">
                    <strong>Permissions:</strong> {key.permissions.join(', ')}
                  </div>
                  <div className="detail-item">
                    <strong>Rate Limit:</strong> {key.rate_limit} requests/hour
                  </div>
                  <div className="detail-item">
                    <strong>Created:</strong> {new Date(key.created_at).toLocaleDateString()}
                  </div>
                  {key.last_used && (
                    <div className="detail-item">
                      <strong>Last Used:</strong> {new Date(key.last_used).toLocaleDateString()}
                    </div>
                  )}
                </div>
                {key.is_active && (
                  <button className="revoke-btn" onClick={() => handleRevokeApiKey(key.id)}>
                    Revoke Key
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderWebhooks = () => {
    return (
      <div className="webhooks-content">
        <div className="section-header">
          <h3>Webhook Subscriptions</h3>
          <button className="primary-btn">+ Create Webhook</button>
        </div>

        {webhooks.length === 0 ? (
          <div className="empty-state">
            <p>No webhooks configured</p>
          </div>
        ) : (
          <div className="webhooks-list">
            {webhooks.map(webhook => (
              <div key={webhook.id} className="webhook-card">
                <div className="webhook-header">
                  <h4>{webhook.webhook_url}</h4>
                  <span className={`status-badge ${webhook.is_active ? 'active' : 'inactive'}`}>
                    {webhook.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="webhook-events">
                  <strong>Events:</strong> {webhook.events.join(', ')}
                </div>
                {webhook.last_triggered && (
                  <div className="webhook-meta">
                    Last triggered: {new Date(webhook.last_triggered).toLocaleString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderLogs = () => {
    return (
      <div className="logs-content">
        <h3>Integration Activity Logs</h3>
        {logs.length === 0 ? (
          <div className="empty-state">
            <p>No activity logs yet</p>
          </div>
        ) : (
          <div className="logs-list">
            {logs.map(log => (
              <div key={log.id} className={`log-item ${log.status}`}>
                <div className="log-icon">
                  {log.status === 'success' ? '✅' : '❌'}
                </div>
                <div className="log-content">
                  <div className="log-header">
                    <strong>{log.integration_type}</strong>
                    <span className="log-action">{log.action}</span>
                  </div>
                  {log.details && <p className="log-details">{log.details}</p>}
                  <div className="log-time">{new Date(log.created_at).toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className="integration-ecosystem loading">Loading integrations...</div>;
  }

  return (
    <div className="integration-ecosystem">
      <div className="ecosystem-header">
        <h1>Integration Ecosystem</h1>
        <p>Connect KnowAllEdge with your favorite learning tools and platforms</p>
      </div>

      <div className="ecosystem-tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={activeTab === 'api-keys' ? 'active' : ''}
          onClick={() => setActiveTab('api-keys')}
        >
          🔑 API Keys
        </button>
        <button 
          className={activeTab === 'webhooks' ? 'active' : ''}
          onClick={() => setActiveTab('webhooks')}
        >
          🪝 Webhooks
        </button>
        <button 
          className={activeTab === 'logs' ? 'active' : ''}
          onClick={() => setActiveTab('logs')}
        >
          📋 Activity Logs
        </button>
      </div>

      <div className="ecosystem-content">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'api-keys' && renderApiKeys()}
        {activeTab === 'webhooks' && renderWebhooks()}
        {activeTab === 'logs' && renderLogs()}
      </div>

      {/* Connection Modal */}
      {showConnectionModal && (
        <div className="modal-overlay" onClick={() => setShowConnectionModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Connect to {selectedIntegration?.name}</h3>
            <p>Connection setup for {selectedIntegration?.name} will be implemented with OAuth flow.</p>
            <button onClick={() => setShowConnectionModal(false)}>Close</button>
          </div>
        </div>
      )}

      {/* API Key Generation Modal */}
      {showApiKeyModal && (
        <div className="modal-overlay" onClick={() => setShowApiKeyModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Generate API Key</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.target);
              handleGenerateApiKey({
                name: formData.get('name'),
                description: formData.get('description'),
                permissions: ['read', 'write'],
                rate_limit: 1000
              });
              setShowApiKeyModal(false);
            }}>
              <div className="form-group">
                <label>Key Name</label>
                <input type="text" name="name" required />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea name="description" rows="3"></textarea>
              </div>
              <div className="modal-actions">
                <button type="submit">Generate</button>
                <button type="button" onClick={() => setShowApiKeyModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New API Key Display Modal */}
      {newApiKey && (
        <div className="modal-overlay" onClick={() => setNewApiKey(null)}>
          <div className="modal-content api-key-display" onClick={(e) => e.stopPropagation()}>
            <h3>🎉 API Key Generated!</h3>
            <div className="warning-box">
              <strong>⚠️ Important:</strong> Save these credentials now. The secret will not be shown again!
            </div>
            <div className="key-display">
              <div className="key-item">
                <label>API Key:</label>
                <code>{newApiKey.api_key}</code>
              </div>
              <div className="key-item">
                <label>API Secret:</label>
                <code>{newApiKey.api_secret}</code>
              </div>
            </div>
            <button onClick={() => setNewApiKey(null)}>I've Saved These Credentials</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationEcosystem;
