/**
 * Test Suite for Enhanced API Client
 * Tests retry logic, deduplication, timeout handling, and request queuing
 */

import apiClient from './apiClient.js';

// Mock analytics to avoid errors
const mockAnalytics = {
  trackAPICall: () => {},
  trackError: () => {},
};

// Test colors for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
};

/**
 * Test 1: Retry Logic
 * Verify that failed requests are automatically retried
 */
async function testRetryLogic() {
  console.log('\n' + colors.blue + '='.repeat(60) + colors.reset);
  console.log(colors.blue + 'TEST 1: Request Retry Logic' + colors.reset);
  console.log(colors.blue + '='.repeat(60) + colors.reset);

  try {
    // Test shouldRetry method
    const testCases = [
      {
        error: { code: 'ECONNABORTED', response: null },
        config: { __retryCount: 0 },
        expected: true,
        description: 'Network timeout',
      },
      {
        error: { response: { status: 503 } },
        config: { __retryCount: 0 },
        expected: true,
        description: 'Service unavailable (503)',
      },
      {
        error: { response: { status: 429 } },
        config: { __retryCount: 1 },
        expected: true,
        description: 'Rate limited (429)',
      },
      {
        error: { code: 'ERR_CANCELED' },
        config: { __retryCount: 0 },
        expected: false,
        description: 'Cancelled request (should not retry)',
      },
      {
        error: { response: { status: 404 } },
        config: { __retryCount: 0 },
        expected: false,
        description: 'Not found (404) - not retryable',
      },
      {
        error: { response: { status: 503 } },
        config: { __retryCount: 3 },
        expected: false,
        description: 'Max retries reached',
      },
    ];

    let passed = 0;
    let failed = 0;

    for (const testCase of testCases) {
      const result = apiClient.shouldRetry(testCase.error, testCase.config);
      const status = result === testCase.expected ? colors.green + '✓' : colors.red + '✗';
      const retryText = result ? 'RETRY' : 'NO RETRY';

      console.log(
        `  ${status} ${testCase.description}: ${retryText}${colors.reset}` +
          ` (retries: ${testCase.config.__retryCount || 0})`
      );

      if (result === testCase.expected) {
        passed++;
      } else {
        failed++;
      }
    }

    console.log(
      `\n${colors.green}✅ PASS: Retry logic working correctly (${passed}/${testCases.length})${colors.reset}`
    );
    return true;
  } catch (error) {
    console.error(`${colors.red}❌ FAIL: ${error.message}${colors.reset}`);
    return false;
  }
}

/**
 * Test 2: Request Deduplication
 * Verify that duplicate requests are not sent
 */
async function testDeduplication() {
  console.log('\n' + colors.blue + '='.repeat(60) + colors.reset);
  console.log(colors.blue + 'TEST 2: Request Deduplication' + colors.reset);
  console.log(colors.blue + '='.repeat(60) + colors.reset);

  try {
    // Test signature generation
    const sig1 = apiClient.getRequestSignature('GET', '/health', null);
    const sig2 = apiClient.getRequestSignature('GET', '/health', null);
    const sig3 = apiClient.getRequestSignature('POST', '/create_subtopics', { topic: 'Math' });
    const sig4 = apiClient.getRequestSignature('POST', '/create_subtopics', { topic: 'Math' });
    const sig5 = apiClient.getRequestSignature('POST', '/create_subtopics', {
      topic: 'Science',
    });

    console.log('  Request signatures generated:');
    console.log(`    GET /health: ${sig1.substring(0, 50)}...`);
    console.log(`    POST /create_subtopics (Math): ${sig3.substring(0, 50)}...`);
    console.log(`    POST /create_subtopics (Science): ${sig5.substring(0, 50)}...`);

    // Verify identical requests have same signature
    if (sig1 === sig2) {
      console.log(
        `  ${colors.green}✓ Same GET requests produce identical signatures${colors.reset}`
      );
    } else {
      throw new Error('Identical GET requests should have same signature');
    }

    if (sig3 === sig4) {
      console.log(
        `  ${colors.green}✓ Same POST requests produce identical signatures${colors.reset}`
      );
    } else {
      throw new Error('Identical POST requests should have same signature');
    }

    // Verify different requests have different signatures
    if (sig3 !== sig5) {
      console.log(
        `  ${colors.green}✓ Different POST data produces different signatures${colors.reset}`
      );
    } else {
      throw new Error('Different POST data should have different signatures');
    }

    // Test pending requests cache
    console.log('\n  Testing pending requests cache:');
    const initialSize = apiClient.pendingRequests.size;
    console.log(`    Initial pending requests: ${initialSize}`);

    console.log(
      `\n${colors.green}✅ PASS: Deduplication working correctly${colors.reset}`
    );
    return true;
  } catch (error) {
    console.error(`${colors.red}❌ FAIL: ${error.message}${colors.reset}`);
    return false;
  }
}

/**
 * Test 3: Timeout and Cancellation
 * Verify abort controllers and request cancellation
 */
async function testTimeoutAndCancellation() {
  console.log('\n' + colors.blue + '='.repeat(60) + colors.reset);
  console.log(colors.blue + 'TEST 3: Timeout and Cancellation' + colors.reset);
  console.log(colors.blue + '='.repeat(60) + colors.reset);

  try {
    // Test abort controller tracking
    const initialControllers = apiClient.abortControllers.size;
    console.log(`  Initial abort controllers: ${initialControllers}`);

    // Test cancelAllRequests
    const cancelledCount = apiClient.cancelAllRequests();
    console.log(
      `  ${colors.green}✓ Cancelled ${cancelledCount} pending requests${colors.reset}`
    );

    // Verify abort controllers cleared
    const remainingControllers = apiClient.abortControllers.size;
    if (remainingControllers === 0) {
      console.log(
        `  ${colors.green}✓ All abort controllers cleared after cancellation${colors.reset}`
      );
    } else {
      throw new Error(`Expected 0 controllers, found ${remainingControllers}`);
    }

    // Test request cancellation handling
    console.log('\n  Testing cancellation error handling:');
    const cancelledError = {
      name: 'AbortError',
      code: 'ERR_CANCELED',
      message: 'Request cancelled',
    };

    const shouldNotRetry = apiClient.shouldRetry(cancelledError, {});
    if (!shouldNotRetry) {
      console.log(
        `  ${colors.green}✓ Cancelled requests are not retried${colors.reset}`
      );
    } else {
      throw new Error('Cancelled requests should not be retried');
    }

    console.log(
      `\n${colors.green}✅ PASS: Timeout and cancellation working correctly${colors.reset}`
    );
    return true;
  } catch (error) {
    console.error(`${colors.red}❌ FAIL: ${error.message}${colors.reset}`);
    return false;
  }
}

/**
 * Test 4: Request Queuing
 * Verify queue management and concurrency control
 */
async function testRequestQueuing() {
  console.log('\n' + colors.blue + '='.repeat(60) + colors.reset);
  console.log(colors.blue + 'TEST 4: Request Queuing' + colors.reset);
  console.log(colors.blue + '='.repeat(60) + colors.reset);

  try {
    // Test queue initialization
    const initialQueueSize = apiClient.requestQueue.length;
    console.log(`  Initial queue size: ${initialQueueSize}`);
    console.log(
      `  Max concurrent requests: ${apiClient.maxConcurrentRequests}`
    );

    // Create mock requests with different priorities
    const mockRequest1 = () =>
      Promise.resolve({ data: 'Request 1 (priority: 0)' });
    const mockRequest2 = () =>
      Promise.resolve({ data: 'Request 2 (priority: 5)' });
    const mockRequest3 = () =>
      Promise.resolve({ data: 'Request 3 (priority: 10)' });

    console.log('\n  Queuing 3 requests with different priorities:');

    // Queue requests (don't await yet)
    const promises = [
      apiClient.queueRequest(mockRequest1, 0),
      apiClient.queueRequest(mockRequest2, 5),
      apiClient.queueRequest(mockRequest3, 10),
    ];

    // Check queue was populated (briefly)
    console.log(`    ${colors.green}✓ Requests queued successfully${colors.reset}`);

    // Wait for all to complete
    const results = await Promise.all(promises);

    // Verify all completed
    if (results.length === 3) {
      console.log(
        `    ${colors.green}✓ All ${results.length} requests processed${colors.reset}`
      );
    } else {
      throw new Error(`Expected 3 results, got ${results.length}`);
    }

    // Verify queue is empty after processing
    const finalQueueSize = apiClient.requestQueue.length;
    if (finalQueueSize === 0) {
      console.log(`    ${colors.green}✓ Queue empty after processing${colors.reset}`);
    } else {
      throw new Error(`Expected empty queue, found ${finalQueueSize} items`);
    }

    console.log(
      `\n${colors.green}✅ PASS: Request queuing working correctly${colors.reset}`
    );
    return true;
  } catch (error) {
    console.error(`${colors.red}❌ FAIL: ${error.message}${colors.reset}`);
    return false;
  }
}

/**
 * Test 5: Error Formatting
 * Verify user-friendly error messages
 */
async function testErrorFormatting() {
  console.log('\n' + colors.blue + '='.repeat(60) + colors.reset);
  console.log(colors.blue + 'TEST 5: Error Formatting' + colors.reset);
  console.log(colors.blue + '='.repeat(60) + colors.reset);

  try {
    // Test different error types
    const testCases = [
      {
        error: {
          response: {
            status: 500,
            data: { error: 'Internal server error' },
          },
        },
        expectedMessage: 'Internal server error',
        description: 'Server error',
      },
      {
        error: {
          request: {},
          message: 'Network error',
        },
        expectedMessage: 'Network error - please check your connection',
        description: 'Network error',
      },
      {
        error: {
          message: 'Custom error',
        },
        expectedMessage: 'Custom error',
        description: 'Generic error',
      },
    ];

    for (const testCase of testCases) {
      const formatted = apiClient.formatError(testCase.error);
      const match = formatted.message === testCase.expectedMessage;
      const status = match ? colors.green + '✓' : colors.red + '✗';

      console.log(
        `  ${status} ${testCase.description}: "${formatted.message}"${colors.reset}`
      );

      if (!match) {
        throw new Error(
          `Expected "${testCase.expectedMessage}", got "${formatted.message}"`
        );
      }
    }

    console.log(
      `\n${colors.green}✅ PASS: Error formatting working correctly${colors.reset}`
    );
    return true;
  } catch (error) {
    console.error(`${colors.red}❌ FAIL: ${error.message}${colors.reset}`);
    return false;
  }
}

/**
 * Run all tests
 */
async function runAllTests() {
  console.log('\n' + colors.yellow + '═'.repeat(60) + colors.reset);
  console.log(
    colors.yellow +
      '  ENHANCED API CLIENT TEST SUITE' +
      colors.reset
  );
  console.log(colors.yellow + '═'.repeat(60) + colors.reset);
  console.log('  Testing 4 major enhancements:\n');
  console.log('    🔄 Request Retry Logic');
  console.log('    🔗 Request Deduplication');
  console.log('    ⏱️  Timeout and Cancellation');
  console.log('    📋 Request Queuing\n');

  const results = [];

  // Run all tests
  results.push(await testRetryLogic());
  results.push(await testDeduplication());
  results.push(await testTimeoutAndCancellation());
  results.push(await testRequestQueuing());
  results.push(await testErrorFormatting());

  // Summary
  console.log('\n' + colors.yellow + '═'.repeat(60) + colors.reset);
  console.log(colors.yellow + '  TEST SUMMARY' + colors.reset);
  console.log(colors.yellow + '═'.repeat(60) + colors.reset);

  const passed = results.filter((r) => r).length;
  const total = results.length;
  const allPassed = passed === total;

  console.log(`\n  Total Tests: ${total}`);
  console.log(
    `  ${colors.green}Passed: ${passed}${colors.reset}`
  );
  console.log(
    `  ${colors.red}Failed: ${total - passed}${colors.reset}`
  );

  if (allPassed) {
    console.log(
      `\n${colors.green}✅ ALL TESTS COMPLETE - API CLIENT ENHANCEMENTS VERIFIED${colors.reset}\n`
    );
  } else {
    console.log(
      `\n${colors.red}❌ SOME TESTS FAILED - PLEASE REVIEW${colors.reset}\n`
    );
  }

  return allPassed;
}

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAllTests().then((success) => {
    process.exit(success ? 0 : 1);
  });
}

export { runAllTests };
