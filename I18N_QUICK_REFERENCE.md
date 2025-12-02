# 🌍 i18n Quick Reference Card

**One-page cheat sheet for internationalization**

---

## 🎯 Core Imports

```jsx
// Components
import { useTranslation } from 'react-i18next';

// Helpers
import { 
  getLanguageInstruction,    // For API prompts
  getCurrentLanguage,        // Get current language code
  isRTL,                    // Check if RTL
  getNativeLanguageName     // Display name
} from './utils/i18nHelpers';

// API Client
import apiClient from './utils/apiClient';
```

---

## 📝 Basic Translation

```jsx
function MyComponent() {
  const { t } = useTranslation();
  
  return (
    <div>
      {/* Simple */}
      <h1>{t('homepage.welcome')}</h1>
      
      {/* With variables */}
      <p>{t('recentTopics.count', { count: 5 })}</p>
      
      {/* Pluralization (auto-detects _plural key) */}
      <p>{t('items', { count: 1 })}</p> {/* "1 item" */}
      <p>{t('items', { count: 5 })}</p> {/* "5 items" */}
    </div>
  );
}
```

---

## 🌐 API Integration

```javascript
// ✅ Automatic (API client adds language automatically)
const response = await apiClient.createSubtopics(topic);
// Sends: Accept-Language: es
// Sends: { topic: "AI", language: "es" }

// ✅ Manual (add language instruction to prompt)
const prompt = `Generate 5 subtopics${getLanguageInstruction()}`;
// English: "Generate 5 subtopics"
// Spanish: "Generate 5 subtopics\n\nIMPORTANT: Please respond in Spanish..."
```

---

## 🔄 Language Switching

```jsx
function LanguageSelector() {
  const { i18n } = useTranslation();
  
  return (
    <select 
      value={i18n.language} 
      onChange={(e) => i18n.changeLanguage(e.target.value)}
    >
      <option value="en">English</option>
      <option value="es">Español</option>
      <option value="fr">Français</option>
      <option value="de">Deutsch</option>
      <option value="zh">简体中文</option>
      <option value="ja">日本語</option>
    </select>
  );
}
```

---

## ↔️ RTL Support

```jsx
import { isRTL } from './utils/i18nHelpers';

// Conditional CSS class
const className = isRTL() ? 'rtl-layout' : 'ltr-layout';

// Conditional rendering
{isRTL() && <div>RTL-specific content</div>}

// Automatic (already in i18n config)
// document.documentElement.dir = 'rtl' (for ar, he, fa, ur)
```

---

## 📅 Date/Number Formatting

```javascript
import { formatDate, formatNumber } from './i18n/config';

// Date formatting
formatDate(new Date(), 'short');    // 1/15/2025
formatDate(new Date(), 'long');     // January 15, 2025
formatDate(new Date(), 'relative'); // 2 hours ago

// Number formatting
formatNumber(1234567);              // 1,234,567 (en)
formatNumber(1234567);              // 1.234.567 (es)
formatNumber(1234567, 'compact');   // 1.2M
formatNumber(0.75, 'percent');      // 75%
```

---

## 🗂️ Translation File Structure

```json
{
  "common": {
    "appName": "KNOWALLEDGE",
    "loading": "Loading..."
  },
  "navigation": {
    "home": "Home",
    "metrics": "Metrics"
  },
  "homepage": {
    "welcome": "Welcome to",
    "generate": {
      "button": "Generate subtopics",
      "generating": "Generating..."
    },
    "recentTopics": {
      "description": "{{count}} recent topic",
      "description_plural": "{{count}} recent topics"
    }
  }
}
```

---

## 🐛 Debugging

```javascript
// Check i18n status
console.log('Initialized:', i18n.isInitialized);
console.log('Language:', i18n.language);
console.log('Loaded:', Object.keys(i18n.store.data));

// Test translation
console.log('Translation:', i18n.t('homepage.welcome'));

// Check localStorage
console.log('Stored:', localStorage.getItem('i18nextLng'));

// Force language
i18n.changeLanguage('es');
```

---

## ⚡ Common Patterns

### **Pattern 1: Conditional Content**
```jsx
{isSubmitting ? t('button.submitting') : t('button.submit')}
```

### **Pattern 2: Interpolation**
```jsx
{t('welcome.message', { name: user.name })}
// "Welcome, John!"
```

### **Pattern 3: List Rendering**
```jsx
{items.map(item => (
  <div key={item.id}>{t(`items.${item.type}`)}</div>
))}
```

### **Pattern 4: Error Messages**
```jsx
{error && <p>{t(`errors.${error.code}`)}</p>}
```

---

## 🔧 Helper Functions

```javascript
// Get current language
getCurrentLanguage() // 'es'

// Check RTL
isRTL() // true for ar, he, fa, ur

// Get language name
getLanguageName('es') // 'Spanish'
getNativeLanguageName('es') // 'Español'

// Add language instruction (for Gemini)
getLanguageInstruction() 
// '\n\nIMPORTANT: Please respond in Spanish...'

// Manual language for request
withLanguage({ topic: 'AI' }) 
// { topic: 'AI', language: 'es' }
```

---

## 📦 Supported Languages

| Code | Language | Native Name | Status |
|------|----------|-------------|--------|
| en | English | English | ✅ Base |
| es | Spanish | Español | ✅ 100% |
| fr | French | Français | ✅ 100% |
| de | German | Deutsch | ✅ 100% |
| zh | Chinese | 简体中文 | ✅ 100% |
| ja | Japanese | 日本語 | ✅ 100% |
| ar | Arabic | العربية | ⏳ RTL Ready |
| he | Hebrew | עברית | ⏳ RTL Ready |

---

## ⚠️ Common Mistakes

### ❌ **DON'T: Hardcode strings**
```jsx
<h1>Welcome to KNOWALLEDGE</h1>
```

### ✅ **DO: Use translation keys**
```jsx
<h1>{t('homepage.welcome')} {t('common.appName')}</h1>
```

---

### ❌ **DON'T: Concatenate translations**
```jsx
<p>{t('welcome')} {userName} {t('to')} {t('app')}</p>
```

### ✅ **DO: Use interpolation**
```jsx
<p>{t('welcome.message', { name: userName })}</p>
```

---

### ❌ **DON'T: Forget pluralization**
```json
{ "items": "{{count}} items" }
```

### ✅ **DO: Add plural forms**
```json
{ 
  "items": "{{count}} item",
  "items_plural": "{{count}} items"
}
```

---

### ❌ **DON'T: Send English-only API prompts**
```javascript
const prompt = `Generate subtopics about ${topic}`;
```

### ✅ **DO: Add language instruction**
```javascript
const prompt = `Generate subtopics about ${topic}${getLanguageInstruction()}`;
```

---

## 🚀 Quick Testing

```javascript
// Test all languages in console
['en', 'es', 'fr', 'de', 'zh', 'ja'].forEach(lang => {
  i18n.changeLanguage(lang);
  console.log(`${lang}: ${i18n.t('homepage.welcome')}`);
});

// Output:
// en: Welcome to
// es: Bienvenido a
// fr: Bienvenue à
// de: Willkommen bei
// zh: 欢迎来到
// ja: ようこそ
```

---

## 📚 Documentation

- **Full Guide**: `I18N_API_INTEGRATION_GUIDE.md`
- **Complete Summary**: `I18N_COMPLETE_SUMMARY.md`
- **Quick Start**: `QUICK_START_TRANSLATION.md`

---

## 🎯 Next Steps

1. **Add translation** to your component:
   ```jsx
   import { useTranslation } from 'react-i18next';
   const { t } = useTranslation();
   <button>{t('button.text')}</button>
   ```

2. **Add key** to translation files:
   ```json
   { "button": { "text": "Click me" } }
   ```

3. **Run Gemini translation** (if new keys):
   ```bash
   cd backend
   python translate_with_gemini.py
   ```

4. **Test** all languages:
   ```javascript
   i18n.changeLanguage('es');
   ```

---

**Status**: ✅ **95% Complete** - Ready to use!
