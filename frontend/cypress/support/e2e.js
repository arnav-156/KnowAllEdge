/**
 * Cypress E2E Support File
 * Runs before every test file
 */

// Import commands
import './commands';

// Hide fetch/XHR requests from command log
const app = window.top;
if (!app.document.head.querySelector('[data-hide-command-log-request]')) {
  const style = app.document.createElement('style');
  style.innerHTML = '.command-name-request, .command-name-xhr { display: none }';
  style.setAttribute('data-hide-command-log-request', '');
  app.document.head.appendChild(style);
}

// Global before hook
beforeEach(() => {
  // Clear cookies and local storage
  cy.clearCookies();
  cy.clearLocalStorage();
  
  // Reset database state (if needed)
  // cy.task('db:seed');
});

// Global after hook
afterEach(() => {
  // Take screenshot on failure
  if (Cypress.currentTest.state === 'failed') {
    cy.screenshot(`${Cypress.currentTest.title} - FAILED`);
  }
});

// Uncaught exception handler
Cypress.on('uncaught:exception', (err, runnable) => {
  // Return false to prevent Cypress from failing the test
  // Customize this based on your needs
  if (err.message.includes('ResizeObserver')) {
    return false;
  }
  return true;
});
