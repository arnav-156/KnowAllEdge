/**
 * Cypress Custom Commands
 * Reusable commands for E2E tests
 */

// ==================== Authentication Commands ====================

/**
 * Login command
 */
Cypress.Commands.add('login', (email = 'test@example.com', password = 'password123') => {
  cy.visit('/auth');
  cy.get('[data-testid="email-input"]').type(email);
  cy.get('[data-testid="password-input"]').type(password);
  cy.get('[data-testid="login-button"]').click();
  cy.url().should('not.include', '/auth');
});

/**
 * Login via API (faster)
 */
Cypress.Commands.add('loginAPI', (email = 'test@example.com', password = 'password123') => {
  cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/auth/login`,
    body: { email, password }
  }).then((response) => {
    window.localStorage.setItem('KNOWALLEDGE_jwt_token', response.body.token);
  });
});

/**
 * Logout command
 */
Cypress.Commands.add('logout', () => {
  cy.get('[data-testid="user-menu"]').click();
  cy.get('[data-testid="logout-button"]').click();
  cy.url().should('include', '/');
});

// ==================== Data Seeding Commands ====================

/**
 * Seed test data
 */
Cypress.Commands.add('seedData', (fixture = 'users') => {
  cy.fixture(fixture).then((data) => {
    cy.request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/test/seed`,
      body: data
    });
  });
});

/**
 * Clear test data
 */
Cypress.Commands.add('clearData', () => {
  cy.request({
    method: 'DELETE',
    url: `${Cypress.env('apiUrl')}/test/clear`
  });
});

// ==================== Navigation Commands ====================

/**
 * Navigate to a page
 */
Cypress.Commands.add('navigateTo', (page) => {
  const routes = {
    home: '/',
    auth: '/auth',
    settings: '/settings',
    graph: '/GraphPage',
    subtopic: '/SubtopicPage'
  };
  cy.visit(routes[page] || page);
});

// ==================== Form Commands ====================

/**
 * Fill form
 */
Cypress.Commands.add('fillForm', (formData) => {
  Object.entries(formData).forEach(([field, value]) => {
    cy.get(`[data-testid="${field}"]`).type(value);
  });
});

/**
 * Submit form
 */
Cypress.Commands.add('submitForm', (formId = 'form') => {
  cy.get(`[data-testid="${formId}"]`).submit();
});

// ==================== API Commands ====================

/**
 * Make authenticated API request
 */
Cypress.Commands.add('apiRequest', (method, endpoint, body = null) => {
  const token = window.localStorage.getItem('KNOWALLEDGE_jwt_token');
  
  return cy.request({
    method,
    url: `${Cypress.env('apiUrl')}${endpoint}`,
    body,
    headers: {
      'Authorization': token ? `Bearer ${token}` : undefined
    }
  });
});

// ==================== Wait Commands ====================

/**
 * Wait for API call
 */
Cypress.Commands.add('waitForAPI', (alias) => {
  cy.wait(`@${alias}`);
});

/**
 * Wait for element to be visible
 */
Cypress.Commands.add('waitForElement', (selector, timeout = 10000) => {
  cy.get(selector, { timeout }).should('be.visible');
});

// ==================== Assertion Commands ====================

/**
 * Check if element contains text
 */
Cypress.Commands.add('shouldContainText', { prevSubject: true }, (subject, text) => {
  cy.wrap(subject).should('contain.text', text);
});

/**
 * Check if URL matches
 */
Cypress.Commands.add('shouldBeAt', (path) => {
  cy.url().should('include', path);
});

// ==================== Storage Commands ====================

/**
 * Set local storage item
 */
Cypress.Commands.add('setLocalStorage', (key, value) => {
  window.localStorage.setItem(key, value);
});

/**
 * Get local storage item
 */
Cypress.Commands.add('getLocalStorage', (key) => {
  return cy.wrap(window.localStorage.getItem(key));
});

// ==================== Screenshot Commands ====================

/**
 * Take full page screenshot
 */
Cypress.Commands.add('screenshotPage', (name) => {
  cy.screenshot(name, { capture: 'fullPage' });
});

// ==================== Accessibility Commands ====================

/**
 * Check accessibility
 * Requires cypress-axe plugin
 */
Cypress.Commands.add('checkA11y', (context = null, options = {}) => {
  // cy.injectAxe();
  // cy.checkA11y(context, options);
});

// ==================== Custom Assertions ====================

/**
 * Assert error message is displayed
 */
Cypress.Commands.add('shouldShowError', (message) => {
  cy.get('[data-testid="error-message"]').should('be.visible').and('contain.text', message);
});

/**
 * Assert success message is displayed
 */
Cypress.Commands.add('shouldShowSuccess', (message) => {
  cy.get('[data-testid="success-message"]').should('be.visible').and('contain.text', message);
});

/**
 * Assert loading indicator is visible
 */
Cypress.Commands.add('shouldBeLoading', () => {
  cy.get('[data-testid="loading-indicator"]').should('be.visible');
});

/**
 * Assert loading indicator is not visible
 */
Cypress.Commands.add('shouldNotBeLoading', () => {
  cy.get('[data-testid="loading-indicator"]').should('not.exist');
});
