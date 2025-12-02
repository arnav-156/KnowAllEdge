/**
 * Lazy Loading Utilities
 * Provides utilities for code splitting and lazy loading components
 * Requirements: 12.7 - Implement code splitting and lazy loading
 */

import React, { lazy, Suspense } from 'react';

/**
 * Loading fallback component
 */
const LoadingFallback = ({ message = 'Loading...' }) => (
  <div className="loading-container" style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '200px',
    padding: '20px'
  }}>
    <div className="loading-spinner">
      <div className="spinner" style={{
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #3498db',
        borderRadius: '50%',
        width: '40px',
        height: '40px',
        animation: 'spin 1s linear infinite'
      }}></div>
      <p style={{ marginTop: '10px', color: '#666' }}>{message}</p>
    </div>
  </div>
);

/**
 * Error fallback component
 */
const ErrorFallback = ({ error, retry }) => (
  <div className="error-container" style={{
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '200px',
    padding: '20px',
    textAlign: 'center'
  }}>
    <div className="error-content">
      <h3 style={{ color: '#e74c3c', marginBottom: '10px' }}>
        Failed to load component
      </h3>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        {error?.message || 'An error occurred while loading this component'}
      </p>
      {retry && (
        <button
          onClick={retry}
          style={{
            padding: '10px 20px',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      )}
    </div>
  </div>
);

/**
 * Lazy load a component with error boundary and retry logic
 */
export const lazyLoad = (importFunc, options = {}) => {
  const {
    fallback = <LoadingFallback />,
    retryDelay = 1000,
    maxRetries = 3
  } = options;

  let retryCount = 0;

  const loadComponent = () => {
    return importFunc().catch(error => {
      if (retryCount < maxRetries) {
        retryCount++;
        console.warn(`Retry ${retryCount}/${maxRetries} loading component...`);
        return new Promise(resolve => {
          setTimeout(() => resolve(loadComponent()), retryDelay);
        });
      }
      throw error;
    });
  };

  const LazyComponent = lazy(loadComponent);

  return (props) => (
    <Suspense fallback={fallback}>
      <LazyComponent {...props} />
    </Suspense>
  );
};

/**
 * Lazy load with error boundary
 */
export class LazyLoadErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Lazy load error:', error, errorInfo);
  }

  retry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} retry={this.retry} />;
    }

    return this.props.children;
  }
}

/**
 * Preload a lazy component
 */
export const preloadComponent = (lazyComponent) => {
  if (lazyComponent && lazyComponent._payload && lazyComponent._payload._result === null) {
    lazyComponent._payload._result();
  }
};

/**
 * Lazy load with preload on hover
 */
export const lazyLoadWithPreload = (importFunc, options = {}) => {
  const Component = lazyLoad(importFunc, options);
  Component.preload = () => importFunc();
  return Component;
};

/**
 * Route-based code splitting helper
 */
export const createLazyRoute = (importFunc, options = {}) => {
  const {
    loadingMessage = 'Loading page...',
    ...otherOptions
  } = options;

  return lazyLoad(importFunc, {
    fallback: <LoadingFallback message={loadingMessage} />,
    ...otherOptions
  });
};

/**
 * Intersection Observer based lazy loading for components
 */
export class LazyLoadOnVisible extends React.Component {
  constructor(props) {
    super(props);
    this.state = { isVisible: false };
    this.containerRef = React.createRef();
  }

  componentDidMount() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting && !this.state.isVisible) {
              this.setState({ isVisible: true });
              this.observer.disconnect();
            }
          });
        },
        {
          rootMargin: this.props.rootMargin || '50px',
          threshold: this.props.threshold || 0.01
        }
      );

      if (this.containerRef.current) {
        this.observer.observe(this.containerRef.current);
      }
    } else {
      // Fallback for browsers without IntersectionObserver
      this.setState({ isVisible: true });
    }
  }

  componentWillUnmount() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }

  render() {
    const { children, placeholder, height = '200px' } = this.props;

    if (!this.state.isVisible) {
      return (
        <div
          ref={this.containerRef}
          style={{ minHeight: height }}
        >
          {placeholder || <LoadingFallback message="Loading..." />}
        </div>
      );
    }

    return children;
  }
}

/**
 * Prefetch resources for better performance
 */
export const prefetchResource = (url, type = 'script') => {
  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.as = type;
  link.href = url;
  document.head.appendChild(link);
};

/**
 * Preconnect to external domains
 */
export const preconnect = (url) => {
  const link = document.createElement('link');
  link.rel = 'preconnect';
  link.href = url;
  document.head.appendChild(link);
};

/**
 * Bundle size analyzer helper
 */
export const logBundleSize = (componentName, importFunc) => {
  if (process.env.NODE_ENV === 'development') {
    const startTime = performance.now();
    return importFunc().then(module => {
      const endTime = performance.now();
      console.log(`[Bundle] ${componentName} loaded in ${(endTime - startTime).toFixed(2)}ms`);
      return module;
    });
  }
  return importFunc();
};

/**
 * Dynamic import with retry and timeout
 */
export const dynamicImport = (importFunc, options = {}) => {
  const {
    timeout = 10000,
    maxRetries = 3,
    retryDelay = 1000
  } = options;

  let retryCount = 0;

  const attemptImport = () => {
    return Promise.race([
      importFunc(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Import timeout')), timeout)
      )
    ]).catch(error => {
      if (retryCount < maxRetries) {
        retryCount++;
        console.warn(`Retry ${retryCount}/${maxRetries} importing module...`);
        return new Promise(resolve =>
          setTimeout(() => resolve(attemptImport()), retryDelay)
        );
      }
      throw error;
    });
  };

  return attemptImport();
};

// Add CSS for spinner animation
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
}

export default {
  lazyLoad,
  LazyLoadErrorBoundary,
  preloadComponent,
  lazyLoadWithPreload,
  createLazyRoute,
  LazyLoadOnVisible,
  prefetchResource,
  preconnect,
  logBundleSize,
  dynamicImport
};
