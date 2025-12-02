/**
 * Authentication E2E Tests
 * Tests user authentication flows
 */

describe('Authentication', () => {
  beforeEach(() => {
    cy.visit('/auth');
  });

  describe('Login', () => {
    it('should login successfully with valid credentials', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      
      cy.url().should('not.include', '/auth');
      cy.get('[data-testid="user-menu"]').should('be.visible');
    });

    it('should show error with invalid credentials', () => {
      cy.get('[data-testid="email-input"]').type('invalid@example.com');
      cy.get('[data-testid="password-input"]').type('wrongpassword');
      cy.get('[data-testid="login-button"]').click();
      
      cy.shouldShowError('Invalid credentials');
    });

    it('should validate email format', () => {
      cy.get('[data-testid="email-input"]').type('invalid-email');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      
      cy.shouldShowError('Invalid email format');
    });
  });

  describe('Registration', () => {
    it('should register a new user', () => {
      cy.get('[data-testid="register-tab"]').click();
      cy.get('[data-testid="email-input"]').type('newuser@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="confirm-password-input"]').type('password123');
      cy.get('[data-testid="register-button"]').click();
      
      cy.url().should('not.include', '/auth');
    });

    it('should validate password match', () => {
      cy.get('[data-testid="register-tab"]').click();
      cy.get('[data-testid="email-input"]').type('newuser@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="confirm-password-input"]').type('different');
      cy.get('[data-testid="register-button"]').click();
      
      cy.shouldShowError('Passwords do not match');
    });
  });

  describe('Logout', () => {
    it('should logout successfully', () => {
      cy.login();
      cy.logout();
      
      cy.url().should('include', '/');
      cy.get('[data-testid="user-menu"]').should('not.exist');
    });
  });
});
