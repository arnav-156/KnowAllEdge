import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import LanguageSelector from './LanguageSelector';
import './Navbar.css';

export default function Navbar() {
  const { user, isAuthenticated, logout, getQuotaLimits } = useAuth();
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleLogout = () => {
    if (window.confirm(t('auth.logout') || 'Are you sure you want to log out?')) {
      logout();
      navigate('/auth');
      setShowProfileMenu(false);
    }
  };

  const getTierBadgeClass = (tier) => {
    const tierMap = {
      limited: 'tier-badge-limited',
      free: 'tier-badge-free',
      basic: 'tier-badge-basic',
      premium: 'tier-badge-premium',
      unlimited: 'tier-badge-unlimited',
    };
    return tierMap[tier] || 'tier-badge-free';
  };

  const getTierIcon = (tier) => {
    const iconMap = {
      limited: '🔒',
      free: '🆓',
      basic: '⭐',
      premium: '💎',
      unlimited: '👑',
    };
    return iconMap[tier] || '🆓';
  };

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo" aria-label="KNOWALLEDGE home">
          <span className="logo-gradient">KNOWALLEDGE</span>
        </Link>

        <div className="navbar-right" role="menubar" aria-label="Main menu">
          <Link to="/metrics" className="navbar-link" role="menuitem">
            <span aria-hidden="true">📊</span> {t('navigation.metrics')}
          </Link>
          
          <Link to="/privacy" className="navbar-link" role="menuitem">
            <span aria-hidden="true">🔒</span> {t('navigation.privacy')}
          </Link>

          {/* ✅ I18N: Language Selector */}
          <LanguageSelector variant="button" />

          {isAuthenticated ? (
            <div className="navbar-profile">
              <button
                className="profile-button"
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                aria-label={t('auth.profile.userMenu')}
                aria-expanded={showProfileMenu}
              >
                <div className="profile-avatar">
                  {user.userId ? user.userId.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="profile-name">{user.userId}</span>
                <span className="profile-dropdown-icon">
                  {showProfileMenu ? '▲' : '▼'}
                </span>
              </button>

              {showProfileMenu && (
                <div className="profile-dropdown">
                  <div className="profile-dropdown-header">
                    <div className="dropdown-avatar">
                      {user.userId ? user.userId.charAt(0).toUpperCase() : 'U'}
                    </div>
                    <div className="dropdown-user-info">
                      <div className="dropdown-username">{user.userId}</div>
                      {user.email && (
                        <div className="dropdown-email">{user.email}</div>
                      )}
                      <div className="dropdown-tier-wrapper">
                        <span
                          className={`tier-badge ${getTierBadgeClass(
                            user.quotaTier
                          )}`}
                        >
                          <span className="tier-icon">
                            {getTierIcon(user.quotaTier)}
                          </span>
                          {t(`auth.profile.tier`, { tier: user.quotaTier })}
                        </span>
                        {user.role === 'admin' && (
                          <span className="admin-badge">{t('auth.profile.admin')}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="profile-dropdown-divider"></div>

                  <div className="profile-dropdown-quota">
                    <div className="quota-title">📊 {t('auth.profile.quotaLimits')}</div>
                    <div className="quota-grid-small">
                      {(() => {
                        const limits = getQuotaLimits();
                        return (
                          <>
                            <div className="quota-item-small">
                              <span className="quota-label-small">
                                {t('auth.profile.requestsPerMinute')}
                              </span>
                              <span className="quota-value-small">
                                {limits.requestsPerMinute === Infinity
                                  ? t('auth.profile.unlimited')
                                  : limits.requestsPerMinute}
                              </span>
                            </div>
                            <div className="quota-item-small">
                              <span className="quota-label-small">
                                {t('auth.profile.requestsPerDay')}
                              </span>
                              <span className="quota-value-small">
                                {limits.requestsPerDay === Infinity
                                  ? t('auth.profile.unlimited')
                                  : limits.requestsPerDay}
                              </span>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  </div>

                  <div className="profile-dropdown-divider"></div>

                  <div className="profile-dropdown-actions">
                    <button
                      className="dropdown-action-btn"
                      onClick={() => {
                        setShowProfileMenu(false);
                        navigate('/');
                      }}
                    >
                      🏠 {t('navigation.home')}
                    </button>
                    <button
                      className="dropdown-action-btn"
                      onClick={() => {
                        setShowProfileMenu(false);
                        navigate('/settings');
                      }}
                    >
                      ⚙️ {t('navigation.settings')}
                    </button>
                    <button
                      className="dropdown-action-btn logout-btn"
                      onClick={handleLogout}
                    >
                      🚪 {t('navigation.logout')}
                    </button>
                  </div>
                </div>
              )}

              {/* Overlay to close menu when clicking outside */}
              {showProfileMenu && (
                <div
                  className="profile-dropdown-overlay"
                  onClick={() => setShowProfileMenu(false)}
                ></div>
              )}
            </div>
          ) : (
            <Link to="/auth" className="navbar-login-btn">
              🔐 {t('navigation.login')}
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
