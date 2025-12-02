/**
 * LoadingSpinner Component
 * Reusable loading indicator with multiple variants
 */

import React from 'react';
import PropTypes from 'prop-types';
import './LoadingSpinner.css';

const LoadingSpinner = ({ 
  size = 'medium', 
  variant = 'default', 
  message = '',
  fullScreen = false 
}) => {
  const sizeClass = `spinner-${size}`;
  const variantClass = `spinner-${variant}`;

  const spinnerElement = (
    <div className={`loading-spinner ${sizeClass} ${variantClass}`}>
      <div className="spinner"></div>
      {message && <p className="spinner-message">{message}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="loading-overlay">
        {spinnerElement}
      </div>
    );
  }

  return spinnerElement;
};

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  variant: PropTypes.oneOf(['default', 'primary', 'secondary']),
  message: PropTypes.string,
  fullScreen: PropTypes.bool
};

LoadingSpinner.defaultProps = {
  size: 'medium',
  variant: 'default',
  message: '',
  fullScreen: false
};

export default LoadingSpinner;
