import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import './Settings.css';

const Settings = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isExporting, setIsExporting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleExportData = async () => {
    setIsExporting(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await fetch('/api/user/data', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to export data');
      }

      // Get the JSON blob
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KNOWALLEDGE_data_export_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setMessage({
        type: 'success',
        text: '✅ Your data has been exported successfully!',
      });
    } catch (error) {
      console.error('Export failed:', error);
      setMessage({
        type: 'error',
        text: '❌ Failed to export data. Please try again.',
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!deleteReason.trim()) {
      setMessage({
        type: 'error',
        text: '❌ Please provide a reason for deletion.',
      });
      return;
    }

    setIsDeleting(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await fetch('/api/user/delete', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ reason: deleteReason }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete account');
      }

      setMessage({
        type: 'success',
        text: '✅ Your account has been deleted. Logging out...',
      });

      // Wait 2 seconds then logout and redirect
      setTimeout(() => {
        logout();
        navigate('/');
      }, 2000);
    } catch (error) {
      console.error('Delete failed:', error);
      setMessage({
        type: 'error',
        text: `❌ ${error.message}`,
      });
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  return (
    <div className="settings-container">
      <div className="settings-content">
        <h1 className="settings-title">⚙️ Account Settings</h1>

        {/* Account Information */}
        <section className="settings-section">
          <h2>👤 Account Information</h2>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">User ID:</span>
              <span className="info-value">{user?.userId || 'N/A'}</span>
            </div>
            {user?.email && (
              <div className="info-item">
                <span className="info-label">Email:</span>
                <span className="info-value">{user.email}</span>
              </div>
            )}
            <div className="info-item">
              <span className="info-label">Quota Tier:</span>
              <span className="info-value tier-badge">{user?.quotaTier || 'free'}</span>
            </div>
            {user?.role === 'admin' && (
              <div className="info-item">
                <span className="info-label">Role:</span>
                <span className="info-value admin-badge">🛡️ ADMIN</span>
              </div>
            )}
          </div>
        </section>

        {/* Message Display */}
        {message.text && (
          <div className={`settings-message ${message.type}`}>
            {message.text}
          </div>
        )}

        {/* Data Export Section */}
        <section className="settings-section" id="data-export">
          <h2>📥 Export Your Data</h2>
          <p className="section-description">
            Download all your personal data in machine-readable format (JSON). This includes your
            account information, queries, topics, and activity history.
          </p>
          <button
            className="settings-btn export-btn"
            onClick={handleExportData}
            disabled={isExporting}
          >
            {isExporting ? '⏳ Exporting...' : '📥 Export My Data (JSON)'}
          </button>
          <p className="gdpr-note">
            <strong>GDPR Article 15:</strong> Right to Access - You have the right to obtain a copy
            of your personal data.
          </p>
        </section>

        {/* Privacy Settings */}
        <section className="settings-section">
          <h2>🔒 Privacy Settings</h2>
          <p className="section-description">
            Manage your privacy preferences and cookie consent.
          </p>
          <button
            className="settings-btn privacy-btn"
            onClick={() => navigate('/privacy')}
          >
            🔒 View Privacy Policy
          </button>
          <button
            className="settings-btn privacy-btn"
            onClick={() => {
              // Trigger cookie consent banner to reappear
              localStorage.removeItem('cookieConsent');
              window.location.reload();
            }}
          >
            🍪 Manage Cookie Preferences
          </button>
        </section>

        {/* Account Deletion Section */}
        <section className="settings-section danger-section" id="delete-account">
          <h2>🗑️ Delete Account</h2>
          <p className="section-description">
            <strong>⚠️ Warning:</strong> This action is permanent and cannot be undone. All your
            data will be deleted within 30 days.
          </p>

          {!showDeleteConfirm ? (
            <button
              className="settings-btn delete-btn"
              onClick={() => setShowDeleteConfirm(true)}
            >
              🗑️ Delete My Account
            </button>
          ) : (
            <div className="delete-confirm-box">
              <h3>⚠️ Confirm Account Deletion</h3>
              <p>
                Please tell us why you're deleting your account (required):
              </p>
              <textarea
                className="delete-reason-input"
                value={deleteReason}
                onChange={(e) => setDeleteReason(e.target.value)}
                placeholder="e.g., No longer using the service, privacy concerns, etc."
                rows={4}
                disabled={isDeleting}
              />
              <div className="confirm-actions">
                <button
                  className="settings-btn cancel-btn"
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeleteReason('');
                  }}
                  disabled={isDeleting}
                >
                  Cancel
                </button>
                <button
                  className="settings-btn confirm-delete-btn"
                  onClick={handleDeleteAccount}
                  disabled={isDeleting || !deleteReason.trim()}
                >
                  {isDeleting ? '⏳ Deleting...' : '✓ Yes, Delete My Account'}
                </button>
              </div>
            </div>
          )}

          <p className="gdpr-note">
            <strong>GDPR Article 17:</strong> Right to Erasure ("Right to be Forgotten") - You have
            the right to request deletion of your personal data.
          </p>
        </section>

        {/* Additional Information */}
        <section className="settings-section info-section">
          <h2>ℹ️ Your Rights</h2>
          <ul className="rights-list">
            <li>
              <strong>Right to Access:</strong> You can download all your data at any time.
            </li>
            <li>
              <strong>Right to Erasure:</strong> You can delete your account and all associated
              data.
            </li>
            <li>
              <strong>Right to Rectification:</strong> You can update your account information.
            </li>
            <li>
              <strong>Right to Data Portability:</strong> Your exported data is in JSON format for
              easy transfer.
            </li>
          </ul>
          <p className="rights-footer">
            For more information, see our{' '}
            <button className="link-btn" onClick={() => navigate('/privacy')}>
              Privacy Policy
            </button>
            .
          </p>
        </section>
      </div>
    </div>
  );
};

export default Settings;
