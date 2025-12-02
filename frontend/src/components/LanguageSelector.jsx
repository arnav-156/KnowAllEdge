/**
 * ✅ I18N: Language Selector Component
 * 
 * Dropdown component for changing application language
 * Supports 6 languages with flags and native names
 * 
 * Features:
 * - Accessible dropdown with keyboard navigation
 * - Shows current language
 * - Displays flags and native names
 * - Auto-saves selection to localStorage
 * - Triggers page-wide language update
 * 
 * @version 1.0
 * @date November 19, 2025
 */

import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES, getCurrentLanguage, changeLanguage } from '../i18n/config';
import './LanguageSelector.css';

const LanguageSelector = ({ variant = 'dropdown' }) => {
  const { t, i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [currentLang, setCurrentLang] = useState(getCurrentLanguage());
  const dropdownRef = useRef(null);

  // Update current language when i18n language changes
  useEffect(() => {
    const handleLanguageChange = () => {
      setCurrentLang(getCurrentLanguage());
    };

    i18n.on('languageChanged', handleLanguageChange);
    return () => {
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, [i18n]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Handle language change
  const handleLanguageChange = async (languageCode) => {
    const success = await changeLanguage(languageCode);
    if (success) {
      setCurrentLang(SUPPORTED_LANGUAGES.find(lang => lang.code === languageCode));
      setIsOpen(false);
      
      // Show success notification
      const event = new CustomEvent('notification', {
        detail: {
          type: 'success',
          message: t('settings.language.changed', { 
            language: SUPPORTED_LANGUAGES.find(l => l.code === languageCode)?.name 
          })
        }
      });
      window.dispatchEvent(event);
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (event, languageCode) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleLanguageChange(languageCode);
    } else if (event.key === 'Escape') {
      setIsOpen(false);
    }
  };

  // Compact button variant (for navbar)
  if (variant === 'button') {
    return (
      <div className="language-selector-compact" ref={dropdownRef}>
        <button
          className="language-selector-button"
          onClick={() => setIsOpen(!isOpen)}
          aria-label={t('settings.language.select')}
          aria-expanded={isOpen}
          aria-haspopup="true"
        >
          <span className="language-flag" aria-hidden="true">{currentLang.flag}</span>
          <span className="language-code">{currentLang.code.toUpperCase()}</span>
          <span className="dropdown-arrow" aria-hidden="true">
            {isOpen ? '▲' : '▼'}
          </span>
        </button>

        {isOpen && (
          <div className="language-dropdown-menu" role="menu">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                className={`language-option ${lang.code === currentLang.code ? 'active' : ''}`}
                onClick={() => handleLanguageChange(lang.code)}
                onKeyDown={(e) => handleKeyDown(e, lang.code)}
                role="menuitem"
                aria-current={lang.code === currentLang.code ? 'true' : undefined}
              >
                <span className="language-flag" aria-hidden="true">{lang.flag}</span>
                <span className="language-name">{lang.nativeName}</span>
                {lang.code === currentLang.code && (
                  <span className="checkmark" aria-label="Selected">✓</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Full dropdown variant (for settings page)
  return (
    <div className="language-selector" ref={dropdownRef}>
      <label htmlFor="language-select" className="language-label">
        {t('settings.language.title')}
      </label>
      
      <div className="language-select-wrapper">
        <button
          id="language-select"
          className="language-select-button"
          onClick={() => setIsOpen(!isOpen)}
          aria-label={t('settings.language.select')}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
        >
          <span className="current-language">
            <span className="language-flag-large" aria-hidden="true">{currentLang.flag}</span>
            <span className="language-info">
              <span className="language-name-primary">{currentLang.name}</span>
              <span className="language-name-native">{currentLang.nativeName}</span>
            </span>
          </span>
          <span className="dropdown-arrow-large" aria-hidden="true">
            {isOpen ? '▲' : '▼'}
          </span>
        </button>

        {isOpen && (
          <div className="language-dropdown-full" role="listbox" aria-label={t('settings.language.select')}>
            {SUPPORTED_LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                className={`language-option-full ${lang.code === currentLang.code ? 'active' : ''}`}
                onClick={() => handleLanguageChange(lang.code)}
                onKeyDown={(e) => handleKeyDown(e, lang.code)}
                role="option"
                aria-selected={lang.code === currentLang.code}
              >
                <span className="language-flag-large" aria-hidden="true">{lang.flag}</span>
                <span className="language-info-full">
                  <span className="language-name-primary">{lang.name}</span>
                  <span className="language-name-native">{lang.nativeName}</span>
                </span>
                {lang.code === currentLang.code && (
                  <span className="checkmark-large" aria-label="Currently selected">✓</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      <p className="language-help-text">
        {t('settings.language.current')}: {currentLang.name} ({currentLang.nativeName})
      </p>
    </div>
  );
};

export default LanguageSelector;
