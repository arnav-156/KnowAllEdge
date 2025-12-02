# 🧪 Quick Accessibility Testing Guide

**Test Duration**: 5-10 minutes  
**Browser**: Chrome, Firefox, or Edge  
**Status**: Ready to test immediately

---

## ⚡ Quick Test (2 minutes)

### **1. Skip Link Test** (30 seconds)
```
1. Open http://localhost:5173
2. Press TAB once
3. ✅ PASS if: Purple "Skip to main content" appears at top-left
4. Press ENTER
5. ✅ PASS if: Focus moves to topic input field
```

### **2. Focus Indicators Test** (1 minute)
```
1. Stay on homepage
2. Press TAB repeatedly (10-15 times)
3. ✅ PASS if EVERY element shows:
   - Blue or purple outline (3px)
   - Glowing shadow effect
   - Clearly visible against background
4. Test elements:
   ✓ Logo
   ✓ Metrics link
   ✓ Privacy link
   ✓ Topic input
   ✓ Generate button
   ✓ Checkbox
   ✓ File upload
```

### **3. Keyboard Navigation Test** (30 seconds)
```
1. Use ONLY keyboard (no mouse)
2. Navigate to topic input
3. Type "Machine Learning"
4. TAB to Generate button
5. Press ENTER
6. ✅ PASS if: Page navigates to subtopics
```

---

## 🔍 Detailed Test (10 minutes)

### **Test 1: Skip Link**

**Steps**:
1. Open homepage
2. Press Tab (first focus)

**Expected Result**:
```
╔═══════════════════════════╗
║ Skip to main content  >>  ║ ← Should appear at top-left
╚═══════════════════════════╝
```

**Verify**:
- ✅ Link appears at top-left corner
- ✅ Purple background (#667eea)
- ✅ White text
- ✅ White outline when focused
- ✅ Pressing Enter jumps to main content
- ✅ Next Tab focuses topic input

---

### **Test 2: Focus Indicators**

**Steps**:
1. Press Tab multiple times
2. Watch each focused element

**Expected Focus Styles**:

| Element | Outline Color | Outline Width | Shadow |
|---------|---------------|---------------|--------|
| Logo | Purple | 3px | Yes (6px glow) |
| Nav Links | Purple | 3px | Yes (6px glow) |
| Topic Input | Green | 3px | Yes (4px glow) |
| Buttons | Purple | 3px | Yes (6px glow) |
| Checkbox | Green | 3px | Yes (4px glow) |
| Profile Button | Purple | 3px | Yes (6px glow) |
| Dropdown Items | Purple | 3px | Yes (inset) |
| Logout Button | Red | 3px | Yes (inset) |

**Visual Example**:
```
Normal Button:
┌─────────────────┐
│ Generate        │
└─────────────────┘

Focused Button:
╔═══════════════════╗ ← 3px purple outline
║ Generate          ║
╚═══════════════════╝
   ↑ Glowing shadow
```

**Verify Each Element**:
- ✅ Outline is clearly visible
- ✅ Outline contrasts with background
- ✅ Shadow/glow effect present
- ✅ Consistent styling across all elements
- ✅ Focus never disappears

---

### **Test 3: Form Labels**

**Steps**:
1. Tab to topic input
2. Read screen text

**Verify Topic Input**:
- ✅ Label visible: "✏️ Enter Your Topic"
- ✅ Label appears above input
- ✅ Input has placeholder text
- ✅ Character count shown below

**Test Label Clicking**:
```
1. Click label text "Enter Your Topic"
2. ✅ PASS if: Input field gets focus
```

**Verify Checkbox**:
- ✅ Label visible: "Remember my recent topics"
- ✅ Label next to checkbox
- ✅ Clicking label toggles checkbox

**Verify Image Upload**:
- ✅ Heading visible: "Select an image"
- ✅ Help text visible: "Supported formats: PNG, JPG..."
- ✅ Input clearly labeled

---

### **Test 4: ARIA Landmarks**

**Method 1: Browser DevTools**

Chrome:
```
1. Right-click page → Inspect
2. Elements tab → Accessibility panel
3. Click "Accessibility Tree"
4. Look for landmarks
```

Firefox:
```
1. Right-click page → Inspect
2. Accessibility tab
3. Click "Show Accessibility Tree"
4. Expand tree
```

**Expected Landmarks**:
```
└─ Document
   ├─ navigation "Main navigation"
   │  ├─ link "KNOWALLEDGE home"
   │  ├─ menubar "Main menu"
   │  │  ├─ menuitem "Metrics"
   │  │  └─ menuitem "Privacy"
   │  └─ ...
   │
   ├─ main "Main content"
   │  └─ section (labeled by "main-heading")
   │     ├─ heading "Welcome to KNOWALLEDGE"
   │     └─ form elements
   │
   └─ complementary "About KNOWALLEDGE"
      ├─ heading "What is KNOWALLEDGE?"
      └─ content
```

**Verify**:
- ✅ Navigation landmark present
- ✅ Main landmark present
- ✅ Section landmark present
- ✅ Aside/Complementary landmark present
- ✅ All landmarks have labels

---

## 🎯 Pass/Fail Criteria

### **PASS Requirements**:
- ✅ Skip link appears on first Tab
- ✅ Skip link works (jumps to main content)
- ✅ ALL interactive elements have visible focus
- ✅ Focus indicators are 3px outline + shadow
- ✅ All forms have visible labels
- ✅ Labels are clickable (focus input)
- ✅ 4 landmarks detected in accessibility tree

### **FAIL Indicators**:
- ❌ Skip link doesn't appear
- ❌ Any element without focus indicator
- ❌ Focus outline too thin (<2px)
- ❌ No shadow/glow effect on focus
- ❌ Any form input without label
- ❌ Landmarks missing in tree

---

## 🐛 Common Issues & Fixes

### **Issue: Skip Link Not Appearing**

**Symptoms**: First Tab doesn't show skip link

**Debug**:
```javascript
// In browser console:
const skipLink = document.querySelector('.skip-link');
console.log('Skip link:', skipLink);
console.log('Computed style:', getComputedStyle(skipLink));
```

**Fix**: Check `App.css` has skip-link styles, check `index.html` has link

---

### **Issue: Focus Not Visible**

**Symptoms**: Tab navigation but no outline

**Debug**:
```javascript
// In browser console:
document.activeElement; // Shows currently focused element
getComputedStyle(document.activeElement, ':focus-visible').outline;
```

**Fix**: 
- Clear browser cache (Ctrl+Shift+Del)
- Restart dev server
- Check `App.css` has focus-visible styles

---

### **Issue: Labels Not Working**

**Symptoms**: Clicking label doesn't focus input

**Debug**:
```javascript
// Check label association:
const input = document.querySelector('#topicInput');
const label = document.querySelector('label[for="topicInput"]');
console.log('Input ID:', input?.id);
console.log('Label for:', label?.getAttribute('for'));
```

**Fix**: Ensure `<label htmlFor="inputId">` matches `<input id="inputId">`

---

## 📊 Quick Checklist

Copy this checklist and mark off as you test:

```
[ ] Skip link appears on first Tab
[ ] Skip link has purple background
[ ] Skip link has white outline when focused
[ ] Skip link jumps to main content (Enter)

[ ] Logo link has visible focus (purple outline)
[ ] Nav links have visible focus (purple outline)
[ ] Topic input has visible focus (green outline)
[ ] Generate button has visible focus (purple outline)
[ ] Checkbox has visible focus (green outline)
[ ] Image upload has visible focus (green outline)
[ ] Profile button has visible focus (purple outline)

[ ] All focus indicators have shadow/glow
[ ] Focus indicators are at least 3px wide
[ ] Focus is clearly visible on all backgrounds
[ ] Focus never disappears during Tab navigation

[ ] Topic input has visible label above it
[ ] Checkbox has visible label next to it
[ ] Image upload has heading label above it
[ ] Recent topics dropdown has visible label
[ ] Clicking labels focuses inputs

[ ] Navigation landmark in accessibility tree
[ ] Main landmark in accessibility tree
[ ] Section landmark in accessibility tree
[ ] Aside landmark in accessibility tree

[ ] All interactive elements keyboard accessible
[ ] Tab order is logical (top to bottom)
[ ] Enter activates buttons
[ ] Escape closes modals (if any)
```

---

## 🎬 Video Test Recording

If you want to record your testing:

**Windows (Xbox Game Bar)**:
```
1. Press Win+G
2. Click record button
3. Perform tests
4. Press Win+Alt+R to stop
```

**Chrome DevTools Recording**:
```
1. F12 → Recorder tab
2. Click "Start recording"
3. Perform tests
4. Click "End recording"
5. Export as video
```

---

## 📸 Screenshot Checklist

Take screenshots of:
1. Skip link focused (first Tab press)
2. Topic input focused (green outline)
3. Generate button focused (purple outline)
4. Profile dropdown focused items
5. Browser accessibility tree showing landmarks

**Save as**: `accessibility-test-screenshots.zip`

---

## ✅ Completion

When all tests pass:

1. ✅ Mark all checklist items
2. ✅ Take screenshots (optional)
3. ✅ Document any issues found
4. ✅ Report: "All accessibility tests passed"

**Estimated Time**: 10 minutes  
**Result**: WCAG 2.1 Level AA Compliance Verified ✅

---

**Happy Testing!** 🎉

If you encounter any issues, check:
- `ACCESSIBILITY_MEDIUM_LOW_FIXES_COMPLETE.md` for details
- `COOKIE_CONSENT_FIX.md` if consent banner broken
- `ACCESSIBILITY_FIXES_COMPLETE.md` for high-priority fixes
