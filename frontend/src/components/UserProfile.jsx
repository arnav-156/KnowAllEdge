/**
 * User Profile Component
 * Displays user information and quota limits
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './UserProfile.css';
import './UserProfile.css';

const UserProfile = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, getQuotaLimits } = useAuth();

  if (!isAuthenticated || !user) {
    return (
      <div className="user-profile-card">
        <p className="not-authenticated">Not authenticated</p>
        <button className="btn-primary" onClick={() => navigate('/auth')}>
          Login / Register
        </button>
      </div>
    );
  }

  const quotaLimits = getQuotaLimits();

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
      navigate('/auth');
    }
  };

  const getTierBadgeClass = (tier) => {
    const classes = {
      limited: 'tier-badge-limited',
      free: 'tier-badge-free',
      basic: 'tier-badge-basic',
      premium: 'tier-badge-premium',
      unlimited: 'tier-badge-unlimited',
    };
    return classes[tier] || 'tier-badge-free';
  };

  const getTierIcon = (tier) => {
    const icons = {
      limited: '🔒',
      free: '🆓',
      basic: '⭐',
      premium: '💎',
      unlimited: '👑',
    };
    return icons[tier] || '🆓';
  };

  return (
    <div className="user-profile-card">
      <div className="profile-header">
        <div className="user-avatar">{user.userId.charAt(0).toUpperCase()}</div>
        <div className="user-info">
          <h3>{user.userId}</h3>
          {user.email && <p className="user-email">{user.email}</p>}
        </div>
      </div>

      <div className="profile-tier">
        <span className={`tier-badge ${getTierBadgeClass(user.quotaTier)}`}>
          {getTierIcon(user.quotaTier)} {user.quotaTier.toUpperCase()}
        </span>
        {user.role === 'admin' && <span className="admin-badge">🛡️ ADMIN</span>}
      </div>

      {quotaLimits && (
        <div className="quota-section">
          <h4>Quota Limits</h4>
          <div className="quota-grid">
            <div className="quota-item">
              <span className="quota-label">Requests/Min</span>
              <span className="quota-value">{quotaLimits.rpm}</span>
            </div>
            <div className="quota-item">
              <span className="quota-label">Requests/Day</span>
              <span className="quota-value">{quotaLimits.rpd.toLocaleString()}</span>
            </div>
            <div className="quota-item">
              <span className="quota-label">Tokens/Min</span>
              <span className="quota-value">{quotaLimits.tpm.toLocaleString()}</span>
            </div>
            <div className="quota-item">
              <span className="quota-label">Tokens/Day</span>
              <span className="quota-value">{quotaLimits.tpd.toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}

      {user.createdAt && (
        <div className="profile-meta">
          <p className="created-at">
            Member since {new Date(user.createdAt).toLocaleDateString()}
          </p>
        </div>
      )}

      <div className="profile-actions">
        <button className="btn-logout" onClick={handleLogout}>
          🚪 Logout
        </button>
      </div>
    </div>
  );
};

export default UserProfile;
