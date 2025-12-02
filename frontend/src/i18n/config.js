/**
 * ✅ INTERNATIONALIZATION (i18n) Configuration
 * 
 * React-i18next setup for multi-language support
 * Supports: English (en), Spanish (es), French (fr), German (de), Chinese (zh), Japanese (ja)
 * 
 * Features:
 * - Automatic language detection (browser settings)
 * - Local storage persistence
 * - Lazy loading of translations
 * - Fallback to English
 * 
 * @version 1.0
 * @date November 19, 2025
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import enTranslations from './locales/en.json';
import esTranslations from './locales/es.json';
import frTranslations from './locales/fr.json';
import deTranslations from './locales/de.json';
import zhTranslations from './locales/zh.json';
import jaTranslations from './locales/ja.json';

// ✅ I18N: Supported languages configuration
export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸', nativeName: 'English' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸', nativeName: 'Español' },
  { code: 'fr', name: 'French', flag: '🇫🇷', nativeName: 'Français' },
  { code: 'de', name: 'German', flag: '🇩🇪', nativeName: 'Deutsch' },
  { code: 'zh', name: 'Chinese', flag: '🇨🇳', nativeName: '中文' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵', nativeName: '日本語' }
];

// ✅ I18N: Language detection options
const detectionOptions = {
  // Order of detection methods
  order: [
    'localStorage',        // Check localStorage first
    'navigator',           // Browser language
    'htmlTag',            // HTML lang attribute
    'path',               // URL path
    'subdomain'           // Subdomain
  ],
  
  // Keys for localStorage
  lookupLocalStorage: 'i18nextLng',
  
  // Cache user language
  caches: ['localStorage'],
  
  // Exclude certain routes from path detection
  excludeCacheFor: ['cimode'],
  
  // Check for language in query string
  lookupQuerystring: 'lng'
};

// ✅ I18N: Initialize i18next
i18n
  // Detect user language
  .use(LanguageDetector)
  
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  
  // Initialize i18next
  .init({
    // Translation resources
    resources: {
      en: { translation: enTranslations },
      es: { translation: esTranslations },
      fr: { translation: frTranslations },
      de: { translation: deTranslations },
      zh: { translation: zhTranslations },
      ja: { translation: jaTranslations }
    },
    
    // Fallback language
    fallbackLng: 'en',
    
    // Debug mode (disable in production)
    debug: process.env.NODE_ENV === 'development',
    
    // Language detection
    detection: detectionOptions,
    
    // Interpolation options
    interpolation: {
      // React already escapes values
      escapeValue: false,
      
      // Format function for dates, numbers, etc.
      format: (value, format, lng) => {
        if (format === 'uppercase') return value.toUpperCase();
        if (format === 'lowercase') return value.toLowerCase();
        if (format === 'capitalize') {
          return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
        }
        
        // Date formatting
        if (value instanceof Date) {
          if (format === 'short') {
            return new Intl.DateTimeFormat(lng, {
              year: 'numeric',
              month: 'short',
              day: 'numeric'
            }).format(value);
          }
          if (format === 'long') {
            return new Intl.DateTimeFormat(lng, {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            }).format(value);
          }
        }
        
        // Number formatting
        if (typeof value === 'number') {
          if (format === 'currency') {
            return new Intl.NumberFormat(lng, {
              style: 'currency',
              currency: 'USD'
            }).format(value);
          }
          if (format === 'percent') {
            return new Intl.NumberFormat(lng, {
              style: 'percent'
            }).format(value);
          }
        }
        
        return value;
      }
    },
    
    // React options
    react: {
      // Bind i18n instance to context
      bindI18n: 'languageChanged loaded',
      bindI18nStore: 'added removed',
      
      // Use Suspense for async loading
      useSuspense: false
    },
    
    // Load namespace
    ns: ['translation'],
    defaultNS: 'translation',
    
    // Key separator
    keySeparator: '.',
    
    // Nesting separator
    nsSeparator: ':',
    
    // Return empty string for missing keys in production
    returnEmptyString: process.env.NODE_ENV === 'production',
    
    // Show key if translation is missing (development only)
    saveMissing: process.env.NODE_ENV === 'development',
    
    // Missing key handler
    missingKeyHandler: (lngs, ns, key, fallbackValue) => {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`🌐 Missing translation: [${lngs[0]}] ${key}`);
      }
    }
  });

// ✅ I18N: Language change handler
i18n.on('languageChanged', (lng) => {
  // Update HTML lang attribute
  document.documentElement.lang = lng;
  
  // Update HTML dir attribute for RTL languages
  const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
  document.documentElement.dir = rtlLanguages.includes(lng) ? 'rtl' : 'ltr';
  
  // Log language change (development only)
  if (process.env.NODE_ENV === 'development') {
    const lang = SUPPORTED_LANGUAGES.find(l => l.code === lng);
    console.log(`🌐 Language changed to: ${lang ? lang.name : lng}`);
  }
  
  // Dispatch custom event for analytics
  window.dispatchEvent(new CustomEvent('languageChanged', { 
    detail: { language: lng } 
  }));
});

// ✅ I18N: Helper function to get current language info
export const getCurrentLanguage = () => {
  const currentLng = i18n.language || 'en';
  return SUPPORTED_LANGUAGES.find(lang => lang.code === currentLng) || SUPPORTED_LANGUAGES[0];
};

// ✅ I18N: Helper function to change language
export const changeLanguage = async (languageCode) => {
  try {
    await i18n.changeLanguage(languageCode);
    
    // Store in localStorage
    localStorage.setItem('i18nextLng', languageCode);
    
    // Reload page to apply changes everywhere
    // (Optional: you can remove this if you handle state updates properly)
    // window.location.reload();
    
    return true;
  } catch (error) {
    console.error('Failed to change language:', error);
    return false;
  }
};

// ✅ I18N: Helper function to get available languages
export const getAvailableLanguages = () => {
  return SUPPORTED_LANGUAGES;
};

// ✅ I18N: Helper function to format date
export const formatDate = (date, format = 'short') => {
  const lng = i18n.language || 'en';
  
  if (format === 'relative') {
    const rtf = new Intl.RelativeTimeFormat(lng, { numeric: 'auto' });
    const diff = Math.floor((date - new Date()) / 1000);
    
    if (Math.abs(diff) < 60) return rtf.format(diff, 'second');
    if (Math.abs(diff) < 3600) return rtf.format(Math.floor(diff / 60), 'minute');
    if (Math.abs(diff) < 86400) return rtf.format(Math.floor(diff / 3600), 'hour');
    return rtf.format(Math.floor(diff / 86400), 'day');
  }
  
  return i18n.t('common.date', { value: date, format });
};

// ✅ I18N: Helper function to format number
export const formatNumber = (number, format = 'decimal') => {
  const lng = i18n.language || 'en';
  
  if (format === 'compact') {
    return new Intl.NumberFormat(lng, { notation: 'compact' }).format(number);
  }
  
  return new Intl.NumberFormat(lng).format(number);
};

export default i18n;
