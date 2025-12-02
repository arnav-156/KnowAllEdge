/**
 * ✅ I18N Helper Functions for API Integration
 * 
 * Use these helpers to add language instructions to API requests
 * that use Google Gemini or other LLMs.
 */

import apiClient from './apiClient';

/**
 * Get localized prompt instruction for current language
 * 
 * @returns {string} Language instruction to append to prompts, or empty string for English
 * 
 * @example
 * const prompt = `Generate 5 subtopics about ${topic}${getLanguageInstruction()}`;
 */
export const getLanguageInstruction = () => {
  return apiClient.getLocalizedPromptInstruction();
};

/**
 * Get localized prompt instruction for specific language
 * 
 * @param {string} languageCode - Language code (en, es, fr, de, zh, ja, ar, he)
 * @returns {string} Language instruction for the specified language
 * 
 * @example
 * const spanishPrompt = `Generate 5 subtopics${getLanguageInstructionFor('es')}`;
 */
export const getLanguageInstructionFor = (languageCode) => {
  return apiClient.getLocalizedPromptInstruction(languageCode);
};

/**
 * Get current language code
 * 
 * @returns {string} Current language code (en, es, fr, de, zh, ja, etc.)
 * 
 * @example
 * const lang = getCurrentLanguage(); // 'es'
 */
export const getCurrentLanguage = () => {
  return apiClient.getCurrentLanguageCode();
};

/**
 * Check if current language is RTL (Right-to-Left)
 * 
 * @returns {boolean} True if current language is RTL (Arabic, Hebrew, Farsi, Urdu)
 * 
 * @example
 * if (isRTL()) {
 *   // Apply RTL-specific styling
 * }
 */
export const isRTL = () => {
  const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
  return rtlLanguages.includes(getCurrentLanguage());
};

/**
 * Get language display name
 * 
 * @param {string} languageCode - Language code (en, es, fr, etc.)
 * @returns {string} Display name in English
 * 
 * @example
 * getLanguageName('es') // 'Spanish'
 * getLanguageName('zh') // 'Chinese (Simplified)'
 */
export const getLanguageName = (languageCode) => {
  const languageNames = {
    en: 'English',
    es: 'Spanish',
    fr: 'French',
    de: 'German',
    zh: 'Chinese (Simplified)',
    ja: 'Japanese',
    ar: 'Arabic',
    he: 'Hebrew',
    fa: 'Persian',
    ur: 'Urdu',
  };
  
  return languageNames[languageCode] || languageCode;
};

/**
 * Get native language name (in the language itself)
 * 
 * @param {string} languageCode - Language code (en, es, fr, etc.)
 * @returns {string} Display name in native language
 * 
 * @example
 * getNativeLanguageName('es') // 'Español'
 * getNativeLanguageName('zh') // '简体中文'
 */
export const getNativeLanguageName = (languageCode) => {
  const nativeNames = {
    en: 'English',
    es: 'Español',
    fr: 'Français',
    de: 'Deutsch',
    zh: '简体中文',
    ja: '日本語',
    ar: 'العربية',
    he: 'עברית',
    fa: 'فارسی',
    ur: 'اردو',
  };
  
  return nativeNames[languageCode] || languageCode;
};

/**
 * Format API request with language parameter
 * 
 * @param {object} data - Original request data
 * @param {string} [languageCode] - Optional language override
 * @returns {object} Request data with language parameter
 * 
 * @example
 * // Automatically adds current language
 * const request = withLanguage({ topic: 'Machine Learning' });
 * // { topic: 'Machine Learning', language: 'es' }
 * 
 * // Or specify language
 * const request = withLanguage({ topic: 'AI' }, 'fr');
 * // { topic: 'AI', language: 'fr' }
 */
export const withLanguage = (data, languageCode = null) => {
  return {
    ...data,
    language: languageCode || getCurrentLanguage(),
  };
};

/**
 * Create localized API error message
 * 
 * @param {Error} error - API error object
 * @returns {string} Localized error message
 * 
 * @example
 * try {
 *   await apiClient.createSubtopics(topic);
 * } catch (error) {
 *   const message = getLocalizedErrorMessage(error);
 *   console.error(message);
 * }
 */
export const getLocalizedErrorMessage = (error) => {
  // This would ideally use i18n translation keys
  // For now, return the error message as-is
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
};

/**
 * ✅ USAGE EXAMPLES:
 * 
 * // Example 1: Add language instruction to Gemini prompt
 * const prompt = `Generate 5 subtopics about ${topic}${getLanguageInstruction()}`;
 * 
 * // Example 2: Create API request with language parameter
 * const response = await apiClient.createSubtopics(
 *   withLanguage({ topic: 'Machine Learning' })
 * );
 * 
 * // Example 3: Check if UI should use RTL layout
 * const containerClass = isRTL() ? 'container-rtl' : 'container-ltr';
 * 
 * // Example 4: Display language selector
 * const languages = ['en', 'es', 'fr', 'de', 'zh', 'ja'];
 * {languages.map(lang => (
 *   <option value={lang}>
 *     {getNativeLanguageName(lang)} ({getLanguageName(lang)})
 *   </option>
 * ))}
 * 
 * // Example 5: Force specific language for a request
 * const spanishPrompt = `Generate graph${getLanguageInstructionFor('es')}`;
 * 
 * // Example 6: Current language detection
 * const currentLang = getCurrentLanguage(); // 'es', 'fr', etc.
 * console.log(`User is viewing site in: ${getLanguageName(currentLang)}`);
 */
