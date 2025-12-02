#!/usr/bin/env python3
"""
Translation script using Google Gemini AI (Free API)
Translates en.json to multiple languages using Gemini 1.5 Flash (free tier)
"""

import json
import os
import time
import google.generativeai as genai
from typing import Dict, Any

# Configure Gemini API
# Get your free API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')  # Set this environment variable or paste your key here

if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY environment variable not set!")
    print("Get your free API key from: https://makersuite.google.com/app/apikey")
    print("\nOptions to set it:")
    print("  1. PowerShell: $env:GEMINI_API_KEY='your-api-key-here'")
    print("  2. CMD:        set GEMINI_API_KEY=your-api-key-here")
    print("  3. Or paste your key directly in this script (line 17)")
    print("\nThen run this script again.")
    
    # Try to prompt for key if running interactively
    try:
        api_key = input("\nOr enter your API key now: ").strip()
        if api_key:
            GEMINI_API_KEY = api_key
            print("✅ API key received! Starting translation...")
        else:
            exit(1)
    except (KeyboardInterrupt, EOFError):
        print("\n❌ No API key provided. Exiting.")
        exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Languages to translate to
LANGUAGES = {
    'es': {
        'name': 'Spanish',
        'native': 'Español',
        'code': 'es',
        'instructions': 'Translate to natural, Latin American Spanish. Use formal "usted" form for educational context.'
    },
    'fr': {
        'name': 'French',
        'native': 'Français',
        'code': 'fr',
        'instructions': 'Translate to standard French. Use formal "vous" form for educational context.'
    },
    'de': {
        'name': 'German',
        'native': 'Deutsch',
        'code': 'de',
        'instructions': 'Translate to standard German. Use formal "Sie" form for educational context.'
    },
    'zh': {
        'name': 'Chinese',
        'native': '中文',
        'code': 'zh',
        'instructions': 'Translate to Simplified Chinese (简体中文). Use formal language suitable for education.'
    },
    'ja': {
        'name': 'Japanese',
        'native': '日本語',
        'code': 'ja',
        'instructions': 'Translate to standard Japanese. Use polite form (です・ます) for educational context.'
    }
}

# Glossary of terms that should NOT be translated
GLOSSARY = {
    'KNOWALLEDGE': 'DO NOT TRANSLATE - This is the brand name, always lowercase',
    '{{count}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{topic}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{max}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{current}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{percent}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{date}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{message}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{query}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{node}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{type}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{level}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{min}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{tier}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{language}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{field}}': 'DO NOT TRANSLATE - This is a variable placeholder',
    '{{total}}': 'DO NOT TRANSLATE - This is a variable placeholder',
}

def create_translation_prompt(json_data: Dict[str, Any], target_lang: Dict[str, str], section_name: str = "") -> str:
    """Create a detailed prompt for Gemini to translate JSON"""
    
    section_text = f" (Section: {section_name})" if section_name else ""
    
    prompt = f"""You are a professional translator specializing in software localization for educational platforms.

TARGET LANGUAGE: {target_lang['native']} ({target_lang['name']})
INSTRUCTIONS: {target_lang['instructions']}

CRITICAL RULES:
1. **Preserve ALL variable placeholders** like {{{{count}}}}, {{{{topic}}}}, {{{{max}}}}, etc. - DO NOT TRANSLATE THESE
2. **DO NOT translate "KNOWALLEDGE"** - it's the brand name (always lowercase)
3. **Preserve ALL HTML tags** if present (e.g., <strong>, <em>, <br>)
4. **Keep the same JSON structure** - only translate the string values
5. **Use natural, native-sounding language** - not literal/word-for-word translation
6. **Maintain consistency** - use the same translation for repeated terms
7. **Educational context** - This is for students and educators learning topics
8. **Preserve emojis** - Keep all emoji characters as-is (🎯, 📚, ✅, etc.)
9. **Pluralization keys** - Keep "_plural" suffix in key names unchanged

GLOSSARY (DO NOT TRANSLATE):
{chr(10).join(f"- {term}: {desc}" for term, desc in GLOSSARY.items())}

JSON TO TRANSLATE{section_text}:
```json
{json.dumps(json_data, indent=2, ensure_ascii=False)}
```

Return ONLY the translated JSON (no explanations, no markdown code blocks, no extra text).
Ensure valid JSON syntax with proper escaping."""
    
    return prompt

def translate_with_gemini(json_data: Dict[str, Any], target_lang: Dict[str, str], section_name: str = "") -> Dict[str, Any]:
    """Translate JSON data using Gemini API"""
    
    try:
        # Use Gemini 2.5 Flash (stable, fast model)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        prompt = create_translation_prompt(json_data, target_lang, section_name)
        
        print(f"   Translating section: {section_name or 'root'}...")
        
        # Generate translation
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Low temperature for consistent translations
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,  # Increased for large sections
            )
        )
        
        # Extract JSON from response
        result_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            lines = result_text.split('\n')
            result_text = '\n'.join(lines[1:-1])  # Remove first and last lines
        
        # Clean up any remaining markdown
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON
        translated_data = json.loads(result_text)
        
        print(f"   ✅ Section '{section_name or 'root'}' translated successfully")
        
        return translated_data
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parsing error in section '{section_name}': {e}")
        print(f"   Response was: {result_text[:200]}...")
        return json_data  # Return original on error
        
    except Exception as e:
        print(f"   ❌ Translation error in section '{section_name}': {e}")
        return json_data  # Return original on error

def translate_json_file(input_file: str, output_file: str, target_lang: Dict[str, str]):
    """Translate entire JSON file section by section"""
    
    print(f"\n{'='*60}")
    print(f"🌍 Translating to {target_lang['name']} ({target_lang['native']})")
    print(f"{'='*60}")
    
    # Load English translations
    with open(input_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    
    translated_data = {}
    
    # Translate each top-level section separately (to avoid token limits)
    for section_key, section_value in en_data.items():
        print(f"\n📦 Section: {section_key}")
        
        if isinstance(section_value, dict):
            # Translate this section
            translated_section = translate_with_gemini(
                {section_key: section_value}, 
                target_lang,
                section_key
            )
            
            # Extract the translated section
            if section_key in translated_section:
                translated_data[section_key] = translated_section[section_key]
            else:
                # Fallback: use original
                translated_data[section_key] = section_value
                print(f"   ⚠️ Using original text for {section_key}")
        else:
            # Simple string value, translate directly
            translated_data[section_key] = section_value
        
        # Rate limiting: Gemini free tier has 60 requests per minute
        # Wait 1.5 seconds between sections to stay under limit
        time.sleep(1.5)
    
    # Save translated file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Translation complete: {output_file}")
    print(f"   Translated {len(translated_data)} sections")

def main():
    """Main translation workflow"""
    
    print("=" * 60)
    print("🌐 KNOWALLEDGE i18n Translation with Google Gemini")
    print("=" * 60)
    
    # Paths
    locales_dir = os.path.join('frontend', 'src', 'i18n', 'locales')
    en_file = os.path.join(locales_dir, 'en.json')
    
    # Check if English file exists
    if not os.path.exists(en_file):
        print(f"❌ ERROR: English translation file not found: {en_file}")
        return
    
    # Create backup of existing translations
    backup_dir = os.path.join(locales_dir, 'backup')
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"\n📂 Source file: {en_file}")
    print(f"📂 Output directory: {locales_dir}")
    print(f"📂 Backup directory: {backup_dir}")
    
    # Translate to each language
    for lang_code, lang_info in LANGUAGES.items():
        output_file = os.path.join(locales_dir, f'{lang_code}.json')
        backup_file = os.path.join(backup_dir, f'{lang_code}.json.backup')
        
        # Backup existing translation if it exists
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                with open(backup_file, 'w', encoding='utf-8') as fb:
                    fb.write(f.read())
            print(f"\n💾 Backed up existing {lang_code}.json")
        
        # Translate
        try:
            translate_json_file(en_file, output_file, lang_info)
        except Exception as e:
            print(f"\n❌ Failed to translate {lang_code}: {e}")
            continue
        
        print(f"\n⏳ Cooling down (rate limit protection)...")
        time.sleep(3)  # Extra delay between languages
    
    print("\n" + "=" * 60)
    print("✅ ALL TRANSLATIONS COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the translated files in frontend/src/i18n/locales/")
    print("2. Test the translations in your app")
    print("3. Make manual corrections if needed")
    print("4. Backups are in frontend/src/i18n/locales/backup/")
    print("\n🎉 Happy translating!")

if __name__ == '__main__':
    main()
