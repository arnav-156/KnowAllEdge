# 🧪 Accessibility Testing Guide - Step by Step

**Date**: November 18, 2025  
**Target**: GraphPage.jsx accessibility features  
**WCAG Level**: AA Compliance

---

## 🎯 Pre-Test Setup

### 1. Start the Application

**Backend**:
```powershell
cd backend
python main.py
# Should run on http://localhost:5000
```

**Frontend**:
```powershell
cd frontend
npm start
# Should run on http://localhost:3000
```

### 2. Navigate to Test Page

Open browser: `http://localhost:3000`
Enter a topic (e.g., "Machine Learning")
Wait for graph to load

---

## ✅ Test 1: Manual Keyboard Navigation

### Setup
- **Close all mouse/trackpad** (or keep hands off)
- **Use keyboard only**
- **Have notepad ready** for notes

### Test Cases

#### 1.1 Initial Tab Navigation
```
Action: Press Tab key repeatedly
Expected: 
  - Focus moves to search input
  - Focus visible (blue outline)
  - Tab through all controls
  - No focus traps
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

#### 1.2 Arrow Key Node Navigation
```
Action: Press ↓ (down arrow)
Expected:
  - First node gets blue outline + glow
  - Screen reader region updates
  
Action: Press ↓ multiple times
Expected:
  - Focus moves to next node
  - Wraps to first node after last
  
Action: Press ↑ (up arrow)
Expected:
  - Focus moves to previous node
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

#### 1.3 Left/Right Navigation
```
Action: Press → (right arrow)
Expected:
  - Focus moves to node on the right
  - If no node to right, stays on current
  
Action: Press ← (left arrow)
Expected:
  - Focus moves to node on the left
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

#### 1.4 Node Interaction
```
Action: Navigate to a node, press Enter
Expected:
  - Modal opens with node details
  - Focus moves into modal
  - Modal content is accessible
  
Action: Press Escape
Expected:
  - Modal closes
  - Focus returns to node
  
Action: Navigate to node, press Space
Expected:
  - Same as Enter - modal opens
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

#### 1.5 Keyboard Shortcuts
```
Action: Press H key
Expected:
  - Alert/dialog shows all shortcuts
  
Action: Press Ctrl+F (or Cmd+F on Mac)
Expected:
  - Search input gets focus
  - Can type immediately
  
Action: Type search term, press Escape
Expected:
  - Search clears or focus returns
  
Action: Press 1, 2, 3 keys
Expected:
  - 1: Toggles topic nodes visibility
  - 2: Toggles subtopic nodes
  - 3: Toggles explanation nodes
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

#### 1.6 Focus Indicators
```
Visual Check: All focused elements have:
  - Blue outline (3px solid #667eea)
  - Visible from 2+ feet away
  - Doesn't overlap content
  - Works in high contrast mode
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

### Test Results Summary
```
Total Tests: 6
Passed: ___
Failed: ___
Issues Found: _______________________
```

---

## 🔊 Test 2: Screen Reader Testing

### Option A: NVDA (Windows - Free)

#### Setup
```powershell
# Install NVDA
choco install nvda

# Or download from:
# https://www.nvaccess.org/download/

# Start NVDA: Ctrl + Alt + N
# Stop NVDA: Insert + Q
```

#### NVDA Test Cases

##### 2.1 Basic Navigation
```
Action: Start NVDA, navigate to graph page
Expected: NVDA announces page title

Action: Press NVDA + Down Arrow
Expected: 
  - Reads next element
  - Announces element type (button, link, etc.)
  
✅ Pass / ❌ Fail: _______
Announcement: "_______________________"
```

##### 2.2 Graph Area
```
Action: Tab to graph area (ReactFlow)
Expected: 
  - NVDA announces "application" role
  - Says "Interactive concept map"
  
Action: Press Insert + Space (toggle focus mode)
Expected:
  - Enters focus/forms mode
  - Can use arrow keys
  
✅ Pass / ❌ Fail: _______
Announcement: "_______________________"
```

##### 2.3 Node Navigation
```
Action: Press ↓ to select first node
Expected:
  - Live region announces: "Selected: [node name], [type] node. Press Enter to view details."
  
Action: Press ↓ multiple times
Expected:
  - Each node is announced clearly
  - Node type is included
  
Action: Press Enter on a node
Expected:
  - "Dialog" or "Modal" announced
  - Modal title is read
  
✅ Pass / ❌ Fail: _______
Announcement: "_______________________"
```

##### 2.4 Form Controls
```
Action: Tab to search input
Expected: 
  - "Search nodes, edit, Ctrl+F"
  - Input type announced
  
Action: Tab to checkboxes (filters)
Expected:
  - "Show topic nodes, checkbox, checked/unchecked"
  - Label is clear
  
Action: Tab to buttons
Expected:
  - Button purpose is clear
  - State is announced (pressed/not pressed)
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

##### 2.5 Alt Text
```
Action: Navigate to logo image
Expected:
  - "KNOWALLEDGE - Interactive Learning Platform Logo, graphic"
  - Full descriptive text
  
Action: Navigate to any icon images
Expected:
  - Decorative images: Not announced (alt="")
  - Functional images: Purpose announced
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

### Option B: VoiceOver (Mac - Built-in)

#### Setup
```bash
# Enable VoiceOver: Cmd + F5
# Or: System Preferences > Accessibility > VoiceOver

# VoiceOver Training: 
# Cmd + F8 (opens VoiceOver Utility > Quick Start)
```

#### VoiceOver Test Cases

##### 2.6 Basic Navigation
```
Action: Enable VoiceOver (Cmd + F5)
Expected: VoiceOver starts, announces page

Action: VO + → (Control + Option + Right Arrow)
Expected:
  - Moves to next element
  - Announces element type and content
  
Action: VO + U (Rotor menu)
Expected:
  - Can navigate by headings, links, form controls
  - Graph elements appear in list
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

##### 2.7 Interactive Elements
```
Action: VO + Space on a button
Expected:
  - Button activates
  - Result is announced
  
Action: Navigate to graph, VO + Shift + Down
Expected:
  - Interacts with application region
  - Can use arrow keys for nodes
  
✅ Pass / ❌ Fail: _______
Notes: _______________________
```

### Screen Reader Test Results
```
Screen Reader Used: NVDA / VoiceOver
Total Tests: 7
Passed: ___
Failed: ___
Major Issues: _______________________
Minor Issues: _______________________
```

---

## 🔧 Test 3: Automated Testing with Axe DevTools

### Setup

#### Install Axe DevTools Extension

**Chrome/Edge**:
1. Go to Chrome Web Store
2. Search "axe DevTools"
3. Install "axe DevTools - Web Accessibility Testing"
4. Pin to toolbar

**Firefox**:
1. Go to Firefox Add-ons
2. Search "axe DevTools"
3. Install extension

### Running Axe Scan

#### 3.1 Full Page Scan
```
Steps:
1. Open DevTools (F12)
2. Click "axe DevTools" tab
3. Click "Scan ALL of my page"
4. Wait for results

Expected Results:
  - 0 Critical issues
  - 0 Serious issues
  - 0-2 Moderate issues (acceptable)
  - 0-5 Minor issues (acceptable)

Actual Results:
  Critical: ___
  Serious: ___
  Moderate: ___
  Minor: ___
  
✅ Pass / ❌ Fail: _______
```

#### 3.2 Specific Component Scan
```
Steps:
1. Right-click on graph area
2. Inspect element
3. In axe tab, click "Scan PART of my page"
4. Select the graph container
5. Run scan

Expected: 0 critical/serious issues in graph

Actual Results: _______________________

✅ Pass / ❌ Fail: _______
```

#### 3.3 Review Issues
```
For each issue found:
  1. Click "Highlight" to see affected element
  2. Read "Why It Matters"
  3. Follow "How to Fix It"
  4. Document below:

Issue 1: _______________________
Severity: _______________________
Fix: _______________________

Issue 2: _______________________
Severity: _______________________
Fix: _______________________
```

### 3.4 Export Report
```
Steps:
1. Click "Save results" in axe DevTools
2. Export as CSV or JSON
3. Save to: accessibility_test_results.csv

✅ Exported: _______
Location: _______________________
```

---

## 🎨 Test 4: Color Contrast Verification

### Tool 1: WebAIM Contrast Checker

#### 4.1 Easy Difficulty Color
```
URL: https://webaim.org/resources/contrastchecker/

Foreground: #059669 (Easy - dark green)
Background: #ffffff (white)

Steps:
1. Enter foreground color: #059669
2. Enter background color: #ffffff
3. Check results

Expected: 
  - AA Pass (4.5:1 minimum)
  - AAA Pass for large text (3:1 minimum)

Actual Ratio: _______
AA Status: Pass / Fail
AAA Status: Pass / Fail

✅ Pass / ❌ Fail: _______
```

#### 4.2 Medium Difficulty Color
```
Foreground: #d97706 (Medium - dark orange)
Background: #ffffff (white)

Actual Ratio: _______
AA Status: Pass / Fail

✅ Pass / ❌ Fail: _______
```

#### 4.3 Hard Difficulty Color
```
Foreground: #dc2626 (Hard - dark red)
Background: #ffffff (white)

Actual Ratio: _______
AA Status: Pass / Fail

✅ Pass / ❌ Fail: _______
```

### Tool 2: Chrome DevTools Contrast

#### 4.4 Live Contrast Check
```
Steps:
1. Open DevTools (F12)
2. Inspect a difficulty-colored node
3. In Styles panel, click color square
4. Check "Contrast ratio" section at bottom

For each difficulty color:
  - Should show ✅ checkmarks for AA and AAA
  - Ratio should be > 4.5:1

Easy (#059669): ✅ / ❌
Medium (#d97706): ✅ / ❌
Hard (#dc2626): ✅ / ❌
```

### Tool 3: Colorblind Simulation

#### 4.5 Deuteranopia Test (Red-Green)
```
Tool: Color Oracle (free) or Chrome "Emulate vision deficiencies"

Steps (Chrome):
1. DevTools > Rendering tab
2. "Emulate vision deficiencies"
3. Select "Deuteranopia"
4. View graph

Expected:
  - All three difficulty colors distinguishable
  - Text readable
  - No loss of information

Result: _______________________
✅ Pass / ❌ Fail: _______
```

#### 4.6 Protanopia Test (Red-Green)
```
Emulate: Protanopia
Result: _______________________
✅ Pass / ❌ Fail: _______
```

#### 4.7 Tritanopia Test (Blue-Yellow)
```
Emulate: Tritanopia
Result: _______________________
✅ Pass / ❌ Fail: _______
```

#### 4.8 Achromatopsia Test (Total Color Blindness)
```
Emulate: Achromatopsia (grayscale)
Expected:
  - Colors still distinguishable by shade
  - Icons/labels provide additional cues

Result: _______________________
✅ Pass / ❌ Fail: _______
```

---

## 🌐 Test 5: Cross-Browser Testing

### 5.1 Chrome (Desktop)

```
Version: _____ (Check: chrome://version)

Tests:
1. Keyboard navigation works: ✅ / ❌
2. Focus indicators visible: ✅ / ❌
3. Colors display correctly: ✅ / ❌
4. Axe scan passes: ✅ / ❌
5. No console errors: ✅ / ❌

Issues: _______________________
Overall: Pass / Fail
```

### 5.2 Firefox (Desktop)

```
Version: _____ (Check: about:support)

Tests:
1. Keyboard navigation works: ✅ / ❌
2. Focus indicators visible: ✅ / ❌
3. Colors display correctly: ✅ / ❌
4. Axe scan passes: ✅ / ❌
5. No console errors: ✅ / ❌

Issues: _______________________
Overall: Pass / Fail
```

### 5.3 Safari (Mac)

```
Version: _____

Tests:
1. Keyboard navigation works: ✅ / ❌
2. Focus indicators visible: ✅ / ❌
3. VoiceOver compatibility: ✅ / ❌
4. Colors display correctly: ✅ / ❌
5. No console errors: ✅ / ❌

Issues: _______________________
Overall: Pass / Fail
```

### 5.4 Edge (Desktop)

```
Version: _____ (Check: edge://version)

Tests:
1. Keyboard navigation works: ✅ / ❌
2. Focus indicators visible: ✅ / ❌
3. Narrator compatibility: ✅ / ❌
4. Colors display correctly: ✅ / ❌
5. No console errors: ✅ / ❌

Issues: _______________________
Overall: Pass / Fail
```

### 5.5 Mobile Safari (iOS)

```
Device: _____ iOS Version: _____

Tests:
1. Touch navigation works: ✅ / ❌
2. VoiceOver mobile works: ✅ / ❌
3. Pinch zoom works: ✅ / ❌
4. Colors visible in sunlight: ✅ / ❌
5. No layout issues: ✅ / ❌

Issues: _______________________
Overall: Pass / Fail
```

### 5.6 Chrome Mobile (Android)

```
Device: _____ Android Version: _____

Tests:
1. Touch navigation works: ✅ / ❌
2. TalkBack compatibility: ✅ / ❌
3. Pinch zoom works: ✅ / ❌
4. Colors visible in sunlight: ✅ / ❌
5. No layout issues: ✅ / ❌

Issues: _______________________
Overall: Pass / Fail
```

---

## 📊 Final Test Report

### Summary Statistics

```
Total Test Categories: 5
  1. Manual Keyboard: Pass / Fail
  2. Screen Reader: Pass / Fail
  3. Axe DevTools: Pass / Fail
  4. Color Contrast: Pass / Fail
  5. Cross-Browser: Pass / Fail

Overall WCAG AA Compliance: Pass / Fail
```

### Critical Issues Found

```
Issue #1: _______________________
Severity: Critical / High / Medium / Low
Status: Open / Fixed

Issue #2: _______________________
Severity: Critical / High / Medium / Low
Status: Open / Fixed

Issue #3: _______________________
Severity: Critical / High / Medium / Low
Status: Open / Fixed
```

### Recommendations

```
Short-term fixes (< 1 week):
1. _______________________
2. _______________________
3. _______________________

Medium-term improvements (1-4 weeks):
1. _______________________
2. _______________________

Long-term enhancements (1-3 months):
1. _______________________
2. _______________________
```

### Sign-off

```
Tester Name: _______________________
Date: November 18, 2025
Time Spent: _____ hours
WCAG Level Achieved: A / AA / AAA
Ready for Production: Yes / No

Notes: _______________________
_______________________
_______________________
```

---

## 🚀 Quick Testing Commands

### Run All Tests (Automated)

```powershell
# Frontend tests
cd frontend
npm test -- --coverage

# Accessibility audit (if configured)
npm run test:a11y

# Lighthouse CI
npx lighthouse http://localhost:3000 --only-categories=accessibility --output=html --output-path=./accessibility-report.html
```

### Generate Reports

```powershell
# Axe-core CLI
npm install -g @axe-core/cli
axe http://localhost:3000 --save accessibility-results.json

# Pa11y
npm install -g pa11y
pa11y http://localhost:3000 --reporter html > pa11y-report.html
```

---

## 📝 Testing Checklist

Use this for quick daily checks:

```
Daily Accessibility Checklist:
□ Can tab through entire interface
□ All interactive elements have visible focus
□ Escape closes all modals
□ Color contrast meets AA standards
□ Alt text on all images
□ No keyboard traps
□ Screen reader announces correctly
□ Works in high contrast mode
□ Zoom to 200% - no loss of function
□ Mobile touch targets ≥ 44px
```

---

**Remember**: 
- Test early, test often
- Real users with disabilities are best testers
- Automated tools catch ~30-40% of issues
- Manual testing is essential
- Document everything!

**Good luck with testing! 🎉**

---

Generated: November 18, 2025  
Last Updated: November 18, 2025  
Version: 1.0
