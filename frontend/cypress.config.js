/**
 * Cypress Configuration for E2E Testing
 * Requirements: 6.6 - Configure Cypress for E2E testing
 */

import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    // Base URL for the application
    baseUrl: 'http://localhost:3000',
    
    // Spec pattern
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    
    // Support file
    supportFile: 'cypress/support/e2e.js',
    
    // Fixtures folder
    fixturesFolder: 'cypress/fixtures',
    
    // Screenshots and videos
    screenshotsFolder: 'cypress/screenshots',
    videosFolder: 'cypress/videos',
    video: true,
    videoCompression: 32,
    screenshotOnRunFailure: true,
    
    // Viewport
    viewportWidth: 1280,
    viewportHeight: 720,
    
    // Timeouts
    defaultCommandTimeout: 10000,
    pageLoadTimeout: 60000,
    requestTimeout: 10000,
    responseTimeout: 30000,
    
    // Retry configuration
    retries: {
      runMode: 2,
      openMode: 0
    },
    
    // Browser configuration
    chromeWebSecurity: false,
    
    // Test isolation
    testIsolation: true,
    
    // Environment variables
    env: {
      apiUrl: 'http://localhost:5000/api',
      coverage: false
    },
    
    setupNodeEvents(on, config) {
      // implement node event listeners here
      
      // Code coverage plugin
      // require('@cypress/code-coverage/task')(on, config);
      
      // Custom tasks
      on('task', {
        log(message) {
          console.log(message);
          return null;
        },
        
        table(message) {
          console.table(message);
          return null;
        }
      });
      
      return config;
    },
  },
  
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite',
    },
    specPattern: 'src/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/component.js',
  },
});
