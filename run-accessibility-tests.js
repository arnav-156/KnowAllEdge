#!/usr/bin/env node

/**
 * Automated Accessibility Testing Script
 * Runs various a11y checks on the KNOWALLEDGE application
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const FRONTEND_URL = 'http://localhost:3000';
const TEST_RESULTS_DIR = 'accessibility-test-results';

console.log('🧪 KNOWALLEDGE Accessibility Test Suite\n');
console.log('=' .repeat(60));

// Create results directory
if (!fs.existsSync(TEST_RESULTS_DIR)) {
  fs.mkdirSync(TEST_RESULTS_DIR, { recursive: true });
  console.log('✅ Created test results directory\n');
}

// Test 1: Check if frontend is running
console.log('📡 Test 1: Checking if frontend is running...');
try {
  const response = require('child_process').execSync(`curl -s -o /dev/null -w "%{http_code}" ${FRONTEND_URL}`, { encoding: 'utf8' });
  if (response.includes('200') || response.includes('304')) {
    console.log('✅ Frontend is running at', FRONTEND_URL);
  } else {
    console.log('⚠️  Frontend returned status:', response);
  }
} catch (e) {
  console.log('❌ Frontend is not running. Please start it first:');
  console.log('   cd frontend && npm start\n');
  process.exit(1);
}

console.log('\n' + '='.repeat(60));
console.log('🚀 Running Automated Tests...\n');

// Test 2: Run Lighthouse accessibility audit
console.log('📊 Test 2: Running Lighthouse accessibility audit...');
console.log('   (This may take 30-60 seconds)\n');

try {
  console.log('Installing lighthouse if needed...');
  execSync('npm list -g lighthouse || npm install -g lighthouse', { stdio: 'pipe' });
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const reportPath = path.join(TEST_RESULTS_DIR, `lighthouse-report-${timestamp}.html`);
  const jsonPath = path.join(TEST_RESULTS_DIR, `lighthouse-report-${timestamp}.json`);
  
  console.log('Running Lighthouse...');
  execSync(
    `lighthouse ${FRONTEND_URL} --only-categories=accessibility --output=html --output=json --output-path=${reportPath.replace('.html', '')} --chrome-flags="--headless"`,
    { stdio: 'inherit' }
  );
  
  console.log(`\n✅ Lighthouse report saved to: ${reportPath}`);
  
  // Parse JSON results
  try {
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    const score = jsonData.categories.accessibility.score * 100;
    console.log(`\n📈 Accessibility Score: ${score}/100`);
    
    if (score >= 90) {
      console.log('   🎉 Excellent! (≥90)');
    } else if (score >= 70) {
      console.log('   ✅ Good (70-89)');
    } else if (score >= 50) {
      console.log('   ⚠️  Needs improvement (50-69)');
    } else {
      console.log('   ❌ Poor (<50)');
    }
  } catch (e) {
    console.log('   Could not parse score from JSON');
  }
  
} catch (error) {
  console.log('⚠️  Lighthouse test failed:', error.message);
  console.log('   You can run manually: npx lighthouse', FRONTEND_URL, '--only-categories=accessibility\n');
}

// Test 3: Run axe-core CLI
console.log('\n' + '='.repeat(60));
console.log('🔧 Test 3: Running axe-core accessibility scan...\n');

try {
  console.log('Installing @axe-core/cli if needed...');
  execSync('npm list -g @axe-core/cli || npm install -g @axe-core/cli', { stdio: 'pipe' });
  
  const axeReportPath = path.join(TEST_RESULTS_DIR, `axe-report-${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
  
  console.log('Running axe-core scan...');
  const axeOutput = execSync(`axe ${FRONTEND_URL} --save ${axeReportPath}`, { encoding: 'utf8' });
  
  console.log(axeOutput);
  console.log(`\n✅ Axe report saved to: ${axeReportPath}`);
  
  // Parse results
  try {
    const axeData = JSON.parse(fs.readFileSync(axeReportPath, 'utf8'));
    const violations = axeData.violations || [];
    
    console.log('\n📊 Axe Results Summary:');
    console.log(`   Violations: ${violations.length}`);
    
    const criticalCount = violations.filter(v => v.impact === 'critical').length;
    const seriousCount = violations.filter(v => v.impact === 'serious').length;
    const moderateCount = violations.filter(v => v.impact === 'moderate').length;
    const minorCount = violations.filter(v => v.impact === 'minor').length;
    
    console.log(`   - Critical: ${criticalCount} ${criticalCount === 0 ? '✅' : '❌'}`);
    console.log(`   - Serious: ${seriousCount} ${seriousCount === 0 ? '✅' : '❌'}`);
    console.log(`   - Moderate: ${moderateCount} ${moderateCount <= 2 ? '✅' : '⚠️'}`);
    console.log(`   - Minor: ${minorCount} ${minorCount <= 5 ? '✅' : '⚠️'}`);
    
    if (violations.length > 0) {
      console.log('\n   Top 3 Issues:');
      violations.slice(0, 3).forEach((v, i) => {
        console.log(`   ${i + 1}. [${v.impact}] ${v.description}`);
        console.log(`      Help: ${v.helpUrl}`);
      });
    }
    
  } catch (e) {
    console.log('   Could not parse axe results');
  }
  
} catch (error) {
  console.log('⚠️  Axe-core test failed:', error.message);
  console.log('   You can run manually: npx @axe-core/cli', FRONTEND_URL, '\n');
}

// Test 4: Run Pa11y
console.log('\n' + '='.repeat(60));
console.log('🎨 Test 4: Running Pa11y accessibility test...\n');

try {
  console.log('Installing pa11y if needed...');
  execSync('npm list -g pa11y || npm install -g pa11y', { stdio: 'pipe' });
  
  const pa11yReportPath = path.join(TEST_RESULTS_DIR, `pa11y-report-${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
  
  console.log('Running Pa11y scan...');
  const pa11yOutput = execSync(`pa11y ${FRONTEND_URL} --reporter json > ${pa11yReportPath}`, { encoding: 'utf8' });
  
  console.log(`✅ Pa11y report saved to: ${pa11yReportPath}`);
  
  // Parse results
  try {
    const pa11yData = JSON.parse(fs.readFileSync(pa11yReportPath, 'utf8'));
    const issues = pa11yData.issues || pa11yData;
    
    console.log('\n📊 Pa11y Results Summary:');
    console.log(`   Total Issues: ${Array.isArray(issues) ? issues.length : 0}`);
    
    if (Array.isArray(issues) && issues.length > 0) {
      const errorCount = issues.filter(i => i.type === 'error').length;
      const warningCount = issues.filter(i => i.type === 'warning').length;
      const noticeCount = issues.filter(i => i.type === 'notice').length;
      
      console.log(`   - Errors: ${errorCount} ${errorCount === 0 ? '✅' : '❌'}`);
      console.log(`   - Warnings: ${warningCount} ${warningCount <= 3 ? '✅' : '⚠️'}`);
      console.log(`   - Notices: ${noticeCount} ℹ️`);
    } else {
      console.log('   🎉 No issues found!');
    }
    
  } catch (e) {
    console.log('   Could not parse Pa11y results');
  }
  
} catch (error) {
  console.log('⚠️  Pa11y test failed:', error.message);
  console.log('   You can run manually: npx pa11y', FRONTEND_URL, '\n');
}

// Test 5: Check for common issues
console.log('\n' + '='.repeat(60));
console.log('🔍 Test 5: Manual Checks Required:\n');

console.log('Please perform these manual tests:');
console.log('');
console.log('✋ KEYBOARD NAVIGATION:');
console.log('   1. Close your mouse/trackpad');
console.log('   2. Press Tab - focus should be visible (blue outline)');
console.log('   3. Press arrow keys - navigate between nodes');
console.log('   4. Press Enter - open node details');
console.log('   5. Press H - show keyboard shortcuts');
console.log('   6. Press Escape - close modals');
console.log('');
console.log('🔊 SCREEN READER:');
console.log('   Windows: Enable NVDA (Ctrl+Alt+N)');
console.log('   Mac: Enable VoiceOver (Cmd+F5)');
console.log('   Navigate with arrow keys and Tab');
console.log('');
console.log('🎨 COLOR CONTRAST:');
console.log('   1. Open DevTools (F12)');
console.log('   2. Inspect colored nodes');
console.log('   3. Check contrast ratio in color picker');
console.log('   4. Should show ✅ for AA compliance');
console.log('');
console.log('🌐 CROSS-BROWSER:');
console.log('   Test in Chrome, Firefox, Safari, Edge');
console.log('   Verify keyboard nav works in each');
console.log('');

// Summary
console.log('\n' + '='.repeat(60));
console.log('📋 ACCESSIBILITY TEST SUMMARY\n');
console.log(`Test Results Directory: ${path.resolve(TEST_RESULTS_DIR)}`);
console.log('');
console.log('Automated Tests:');
console.log('  ✅ Frontend availability check');
console.log('  📊 Lighthouse audit (see HTML report)');
console.log('  🔧 Axe-core scan (see JSON report)');
console.log('  🎨 Pa11y test (see JSON report)');
console.log('');
console.log('Manual Tests Required:');
console.log('  ⏳ Keyboard navigation');
console.log('  ⏳ Screen reader testing');
console.log('  ⏳ Color contrast verification');
console.log('  ⏳ Cross-browser testing');
console.log('');
console.log('📖 Full testing guide: ACCESSIBILITY_TESTING_GUIDE.md');
console.log('');
console.log('Next Steps:');
console.log('  1. Review HTML reports in browser');
console.log('  2. Fix any Critical/Serious issues');
console.log('  3. Complete manual tests');
console.log('  4. Re-run this script to verify fixes');
console.log('');
console.log('🎉 Automated testing complete!');
console.log('=' .repeat(60));
