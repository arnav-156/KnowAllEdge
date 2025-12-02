import React, { useState, useEffect } from 'react';
import './CookieConsent.css';
import storage from '../utils/storage';

/**
 * ✅ GDPR: Cookie Consent Banner
 * Compliant with GDPR Article 7 (consent) and ePrivacy Directive
 * 
 * Features:
 * - Granular consent controls (necessary, functional, analytics)
 * - Clear opt-in/opt-out
 * - Persistent storage of consent choices
 * - Revocable consent
 * - Links to privacy policy
 */
const CookieConsent = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [consents, setConsents] = useState({
    necessary: true, // Always true (required for app function)
    functional: false,
    analytics: false,
    performance: false
  });

  useEffect(() => {
    // Check if user has already given/rejected consent
    const consentData = storage.getConsentStatus();
    
    if (!consentData || !consentData.given || !consentData.timestamp) {
      // No consent recorded - show banner
      setIsVisible(true);
    } else {
      // Consent exists - apply it
      setConsents({
        necessary: true,
        functional: consentData.categories.includes('functional'),
        analytics: consentData.categories.includes('analytics'),
        performance: consentData.categories.includes('performance')
      });
    }
  }, []);

  const handleAcceptAll = () => {
    const allConsents = {
      necessary: true,
      functional: true,
      analytics: true,
      performance: true
    };
    
    setConsents(allConsents);
    saveConsent(allConsents);
    setIsVisible(false);
  };

  const handleRejectAll = () => {
    const minimalConsents = {
      necessary: true, // Can't disable necessary cookies
      functional: false,
      analytics: false,
      performance: false
    };
    
    setConsents(minimalConsents);
    saveConsent(minimalConsents);
    setIsVisible(false);
  };

  const handleSavePreferences = () => {
    saveConsent(consents);
    setIsVisible(false);
  };

  const saveConsent = (consentChoices) => {
    // Save to storage using privacy consent API
    const categories = Object.entries(consentChoices)
      .filter(([_, value]) => value === true)
      .map(([key, _]) => key);
    
    // Use requestConsent with showUI=false since we already have user choices
    storage.requestConsent(categories, { showUI: false, persistChoice: true });
    
    // Trigger consent change event for other components
    window.dispatchEvent(new CustomEvent('consentChanged', { 
      detail: { consents: consentChoices } 
    }));
    
    console.log('✅ Privacy consent saved:', categories);
  };

  const handleToggleConsent = (category) => {
    if (category === 'necessary') return; // Can't disable necessary
    
    setConsents(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  if (!isVisible) return null;

  return (
    <div className="cookie-consent-overlay" role="dialog" aria-labelledby="cookie-consent-title" aria-modal="true">
      <div className="cookie-consent-banner">
        <div className="cookie-consent-content">
          <h2 id="cookie-consent-title" className="cookie-consent-title">
            🍪 We Value Your Privacy
          </h2>
          
          <p className="cookie-consent-description">
            We use cookies and similar technologies to enhance your experience, analyze usage, 
            and provide personalized features. By clicking "Accept All", you consent to our use 
            of cookies.
          </p>

          <p className="cookie-consent-legal">
            We share some data with Google Gemini AI to provide intelligent features. 
            You can manage your preferences at any time. 
            <a href="/privacy" target="_blank" rel="noopener noreferrer">
              Read our Privacy Policy
            </a>
          </p>

          {showDetails && (
            <div className="cookie-consent-details">
              <h3>Cookie Preferences</h3>
              
              <div className="cookie-category">
                <div className="cookie-category-header">
                  <label>
                    <input
                      type="checkbox"
                      checked={consents.necessary}
                      disabled
                      aria-label="Necessary cookies (required)"
                    />
                    <span className="cookie-category-name">
                      Necessary Cookies <span className="required-badge">Required</span>
                    </span>
                  </label>
                </div>
                <p className="cookie-category-description">
                  Essential for the website to function. Includes authentication, security, 
                  and basic functionality. Cannot be disabled.
                </p>
              </div>

              <div className="cookie-category">
                <div className="cookie-category-header">
                  <label>
                    <input
                      type="checkbox"
                      checked={consents.functional}
                      onChange={() => handleToggleConsent('functional')}
                      aria-label="Functional cookies (optional)"
                    />
                    <span className="cookie-category-name">Functional Cookies</span>
                  </label>
                </div>
                <p className="cookie-category-description">
                  Remember your preferences (theme, language, settings) for a better experience.
                </p>
              </div>

              <div className="cookie-category">
                <div className="cookie-category-header">
                  <label>
                    <input
                      type="checkbox"
                      checked={consents.analytics}
                      onChange={() => handleToggleConsent('analytics')}
                      aria-label="Analytics cookies (optional)"
                    />
                    <span className="cookie-category-name">Analytics Cookies</span>
                  </label>
                </div>
                <p className="cookie-category-description">
                  Help us understand how you use our site to improve your experience. 
                  Data is anonymized.
                </p>
              </div>

              <div className="cookie-category">
                <div className="cookie-category-header">
                  <label>
                    <input
                      type="checkbox"
                      checked={consents.performance}
                      onChange={() => handleToggleConsent('performance')}
                      aria-label="Performance cookies (optional)"
                    />
                    <span className="cookie-category-name">Performance Cookies</span>
                  </label>
                </div>
                <p className="cookie-category-description">
                  Monitor site performance and optimize load times for a faster experience.
                </p>
              </div>
            </div>
          )}

          <div className="cookie-consent-actions">
            {!showDetails ? (
              <>
                <button
                  className="btn btn-primary"
                  onClick={handleAcceptAll}
                  aria-label="Accept all cookies"
                >
                  Accept All
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={handleRejectAll}
                  aria-label="Reject optional cookies"
                >
                  Reject All
                </button>
                <button
                  className="btn btn-link"
                  onClick={() => setShowDetails(true)}
                  aria-label="Customize cookie preferences"
                >
                  Customize
                </button>
              </>
            ) : (
              <>
                <button
                  className="btn btn-primary"
                  onClick={handleSavePreferences}
                  aria-label="Save cookie preferences"
                >
                  Save Preferences
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowDetails(false)}
                  aria-label="Go back"
                >
                  Back
                </button>
              </>
            )}
          </div>

          <div className="cookie-consent-footer">
            <small>
              Your privacy matters. You can change your preferences anytime in Settings. 
              This banner complies with GDPR, CCPA, and ePrivacy regulations.
            </small>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CookieConsent;
