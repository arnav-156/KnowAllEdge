/**
 * ErrorDisplay Component
 * Maps API errors to user-friendly messages
 * Logs technical details to console for debugging
 * 
 * Requirements: 5.4 - Create user-friendly error handling
 */

import React from 'react';
import PropTypes from 'prop-types';
import './ErrorDisplay.css';

const ErrorDisplay = ({ error, onRetry, onDismiss }) => {
  if (!error) return null;

  /**
   * Map error codes to user-friendly messages
   */
  const getUserFriendlyMessage = (error) => {
    // Handle string errors
    if (typeof error === 'string') {
      return error;
    }

    // Handle error objects with error_code
    const errorCode = error.error_code || error.code;
    const errorMessage = error.message || error.error;

    // Map common error codes to friendly messages
    const errorMessages = {
      // Authentication errors
      'AUTH_REQUIRED': 'Please log in to continue',
      'AUTH_INVALID': 'Your session has expired. Please log in again',
      'AUTH_EXPIRED': 'Your session has expired. Please log in again',
      'INVALID_API_KEY': 'Invalid authentication credentials',
      'INVALID_TOKEN': 'Your session is invalid. Please log in again',
      
      // Authorization errors
      'INSUFFICIENT_PERMISSIONS': 'You don\'t have permission to perform this action',
      'ADMIN_REQUIRED': 'This action requires administrator privileges',
      
      // Validation errors
      'VALIDATION_ERROR': 'Please check your input and try again',
      'INVALID_INPUT': 'Some of the information you provided is invalid',
      'MISSING_FIELD': 'Please fill in all required fields',
      'INVALID_FORMAT': 'Please check the format of your input',
      
      // Rate limiting
      'RATE_LIMIT_EXCEEDED': 'You\'re making requests too quickly. Please wait a moment and try again',
      'QUOTA_EXCEEDED': 'You\'ve reached your usage limit. Please upgrade your plan or try again later',
      
      // CSRF errors
      'CSRF_TOKEN_MISSING': 'Security token missing. Please refresh the page and try again',
      'CSRF_TOKEN_INVALID': 'Security token invalid. Please refresh the page and try again',
      'CSRF_TOKEN_MISMATCH': 'Security token mismatch. Please refresh the page and try again',
      
      // Network errors
      'NETWORK_ERROR': 'Unable to connect to the server. Please check your internet connection',
      'TIMEOUT': 'The request took too long. Please try again',
      'SERVER_ERROR': 'Something went wrong on our end. Please try again later',
      
      // Resource errors
      'NOT_FOUND': 'The requested resource was not found',
      'ALREADY_EXISTS': 'This resource already exists',
      'CONFLICT': 'This action conflicts with existing data',
      
      // File upload errors
      'FILE_TOO_LARGE': 'The file you\'re trying to upload is too large',
      'INVALID_FILE_TYPE': 'This file type is not supported',
      'UPLOAD_FAILED': 'File upload failed. Please try again',
      
      // Database errors
      'DATABASE_ERROR': 'A database error occurred. Please try again later',
      'CONNECTION_ERROR': 'Unable to connect to the database. Please try again later',
    };

    // Return mapped message or default
    if (errorCode && errorMessages[errorCode]) {
      return errorMessages[errorCode];
    }

    // Return original message if it's user-friendly
    if (errorMessage && !errorMessage.includes('Error:') && !errorMessage.includes('Exception')) {
      return errorMessage;
    }

    // Default fallback
    return 'An unexpected error occurred. Please try again';
  };

  /**
   * Get error severity level
   */
  const getErrorSeverity = (error) => {
    const errorCode = error?.error_code || error?.code;
    
    // Critical errors that require immediate action
    const criticalErrors = ['AUTH_EXPIRED', 'AUTH_INVALID', 'QUOTA_EXCEEDED'];
    if (criticalErrors.includes(errorCode)) {
      return 'critical';
    }

    // Warning errors that user should be aware of
    const warningErrors = ['RATE_LIMIT_EXCEEDED', 'VALIDATION_ERROR'];
    if (warningErrors.includes(errorCode)) {
      return 'warning';
    }

    // Default to error
    return 'error';
  };

  /**
   * Log technical details to console
   */
  const logTechnicalDetails = (error) => {
    if (import.meta.env.DEV) {
      console.group('🔍 Error Details');
      console.error('Error Object:', error);
      if (error.stack) {
        console.error('Stack Trace:', error.stack);
      }
      if (error.details) {
        console.error('Additional Details:', error.details);
      }
      if (error.status) {
        console.error('HTTP Status:', error.status);
      }
      console.groupEnd();
    } else {
      // In production, log minimal info
      console.error('Error:', error.error_code || error.code || 'UNKNOWN', error.message || error.error);
    }
  };

  // Log technical details
  React.useEffect(() => {
    if (error) {
      logTechnicalDetails(error);
    }
  }, [error]);

  const userMessage = getUserFriendlyMessage(error);
  const severity = getErrorSeverity(error);

  return (
    <div className={`error-display error-display-${severity}`} role="alert" aria-live="assertive">
      <div className="error-display-content">
        <div className="error-display-icon">
          {severity === 'critical' && '🚨'}
          {severity === 'warning' && '⚠️'}
          {severity === 'error' && '❌'}
        </div>
        
        <div className="error-display-message">
          <h3 className="error-display-title">
            {severity === 'critical' && 'Action Required'}
            {severity === 'warning' && 'Warning'}
            {severity === 'error' && 'Error'}
          </h3>
          <p className="error-display-text">{userMessage}</p>
          
          {error.details && import.meta.env.DEV && (
            <details className="error-display-details">
              <summary>Technical Details (Development Mode)</summary>
              <pre>{JSON.stringify(error.details, null, 2)}</pre>
            </details>
          )}
        </div>

        <div className="error-display-actions">
          {onRetry && (
            <button 
              onClick={onRetry}
              className="error-display-button error-display-button-primary"
              aria-label="Retry action"
            >
              Try Again
            </button>
          )}
          {onDismiss && (
            <button 
              onClick={onDismiss}
              className="error-display-button error-display-button-secondary"
              aria-label="Dismiss error"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

ErrorDisplay.propTypes = {
  error: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.shape({
      message: PropTypes.string,
      error: PropTypes.string,
      error_code: PropTypes.string,
      code: PropTypes.string,
      status: PropTypes.number,
      details: PropTypes.any,
      stack: PropTypes.string
    })
  ]),
  onRetry: PropTypes.func,
  onDismiss: PropTypes.func
};

export default ErrorDisplay;
