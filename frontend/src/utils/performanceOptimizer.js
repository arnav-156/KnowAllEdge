/**
 * Frontend Performance Optimizer
 * Provides client-side performance monitoring and optimization utilities
 * Requirements: 7.3 - Set up performance monitoring
 */

class PerformanceOptimizer {
  constructor() {
    this.metrics = new Map();
    this.observers = new Map();
    this.isMonitoring = false;
    this.config = {
      enableResourceTiming: true,
      enableUserTiming: true,
      enableLongTasks: true,
      enableLayoutShift: true,
      reportInterval: 30000, // 30 seconds
    };
  }

  /**
   * Initialize performance monitoring
   */
  initialize(config = {}) {
    this.config = { ...this.config, ...config };
    
    if (this.isMonitoring) {
      return;
    }

    this.isMonitoring = true;
    
    // Setup performance observers
    this.setupPerformanceObservers();
    
    // Monitor Core Web Vitals
    this.monitorCoreWebVitals();
    
    // Setup automatic reporting
    this.setupReporting();
    
    // Monitor memory usage
    this.monitorMemoryUsage();
    
    console.log('✅ Performance monitoring initialized');
  }

  /**
   * Setup performance observers
   */
  setupPerformanceObservers() {
    // Resource timing
    if (this.config.enableResourceTiming && 'PerformanceObserver' in window) {
      try {
        const resourceObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordResourceTiming(entry);
          }
        });
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.set('resource', resourceObserver);
      } catch (e) {
        console.warn('Resource timing observer not supported:', e);
      }
    }

    // Navigation timing
    if ('PerformanceObserver' in window) {
      try {
        const navigationObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordNavigationTiming(entry);
          }
        });
        navigationObserver.observe({ entryTypes: ['navigation'] });
        this.observers.set('navigation', navigationObserver);
      } catch (e) {
        console.warn('Navigation timing observer not supported:', e);
      }
    }

    // Long tasks
    if (this.config.enableLongTasks && 'PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordLongTask(entry);
          }
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.set('longtask', longTaskObserver);
      } catch (e) {
        console.warn('Long task observer not supported:', e);
      }
    }
  }

  /**
   * Monitor Core Web Vitals
   */
  monitorCoreWebVitals() {
    // Largest Contentful Paint (LCP)
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          this.recordMetric('lcp', lastEntry.startTime);
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.set('lcp', lcpObserver);
      } catch (e) {
        console.warn('LCP observer not supported:', e);
      }
    }

    // First Input Delay (FID)
    if ('PerformanceObserver' in window) {
      try {
        const fidObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric('fid', entry.processingStart - entry.startTime);
          }
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.set('fid', fidObserver);
      } catch (e) {
        console.warn('FID observer not supported:', e);
      }
    }

    // Cumulative Layout Shift (CLS)
    let clsValue = 0;
    
    if ('PerformanceObserver' in window) {
      try {
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          }
          this.recordMetric('cls', clsValue);
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.set('cls', clsObserver);
      } catch (e) {
        console.warn('CLS observer not supported:', e);
      }
    }
  }

  /**
   * Record resource timing
   */
  recordResourceTiming(entry) {
    const timing = {
      name: entry.name,
      type: this.getResourceType(entry.name),
      duration: entry.duration,
      size: entry.transferSize || 0,
      cached: entry.transferSize === 0 && entry.decodedBodySize > 0,
      timestamp: Date.now()
    };

    if (!this.metrics.has('resources')) {
      this.metrics.set('resources', []);
    }
    this.metrics.get('resources').push(timing);

    // Keep only recent entries
    const resources = this.metrics.get('resources');
    if (resources.length > 1000) {
      resources.splice(0, resources.length - 1000);
    }
  }

  /**
   * Record navigation timing
   */
  recordNavigationTiming(entry) {
    const timing = {
      domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
      loadComplete: entry.loadEventEnd - entry.loadEventStart,
      domInteractive: entry.domInteractive - entry.fetchStart,
      firstPaint: this.getFirstPaint(),
      firstContentfulPaint: this.getFirstContentfulPaint(),
      timestamp: Date.now()
    };

    this.metrics.set('navigation', timing);
  }

  /**
   * Record long task
   */
  recordLongTask(entry) {
    const task = {
      duration: entry.duration,
      startTime: entry.startTime,
      attribution: entry.attribution || [],
      timestamp: Date.now()
    };

    if (!this.metrics.has('longTasks')) {
      this.metrics.set('longTasks', []);
    }
    this.metrics.get('longTasks').push(task);

    // Log warning for very long tasks
    if (entry.duration > 100) {
      console.warn(`Long task detected: ${entry.duration.toFixed(2)}ms`);
    }
  }

  /**
   * Record custom metric
   */
  recordMetric(name, value, tags = {}) {
    const metric = {
      name,
      value,
      tags,
      timestamp: Date.now()
    };

    if (!this.metrics.has('custom')) {
      this.metrics.set('custom', []);
    }
    this.metrics.get('custom').push(metric);
  }

  /**
   * Time a function execution
   */
  timeFunction(name, fn) {
    const start = performance.now();
    const result = fn();
    const duration = performance.now() - start;
    
    this.recordMetric('function_timing', duration, { function: name });
    
    if (duration > 16.67) { // > 1 frame at 60fps
      console.warn(`Slow function ${name}: ${duration.toFixed(2)}ms`);
    }
    
    return result;
  }

  /**
   * Time an async function execution
   */
  async timeAsyncFunction(name, fn) {
    const start = performance.now();
    const result = await fn();
    const duration = performance.now() - start;
    
    this.recordMetric('async_function_timing', duration, { function: name });
    
    return result;
  }

  /**
   * Monitor memory usage
   */
  monitorMemoryUsage() {
    if ('memory' in performance) {
      setInterval(() => {
        const memory = performance.memory;
        this.recordMetric('memory_used', memory.usedJSHeapSize);
        this.recordMetric('memory_total', memory.totalJSHeapSize);
        this.recordMetric('memory_limit', memory.jsHeapSizeLimit);
      }, 10000); // Every 10 seconds
    }
  }

  /**
   * Get resource type from URL
   */
  getResourceType(url) {
    if (url.includes('.js')) return 'script';
    if (url.includes('.css')) return 'stylesheet';
    if (url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) return 'image';
    if (url.match(/\.(woff|woff2|ttf|otf)$/i)) return 'font';
    if (url.includes('/api/')) return 'api';
    return 'other';
  }

  /**
   * Get First Paint timing
   */
  getFirstPaint() {
    const paintEntries = performance.getEntriesByType('paint');
    const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
    return firstPaint ? firstPaint.startTime : null;
  }

  /**
   * Get First Contentful Paint timing
   */
  getFirstContentfulPaint() {
    const paintEntries = performance.getEntriesByType('paint');
    const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint');
    return fcp ? fcp.startTime : null;
  }

  /**
   * Setup automatic reporting
   */
  setupReporting() {
    setInterval(() => {
      this.sendMetricsToServer();
    }, this.config.reportInterval);

    // Send metrics on page unload
    window.addEventListener('beforeunload', () => {
      this.sendMetricsToServer(true);
    });
  }

  /**
   * Send metrics to server
   */
  async sendMetricsToServer(isBeacon = false) {
    const metricsData = this.getMetricsSummary();
    
    if (Object.keys(metricsData).length === 0) {
      return;
    }

    const payload = JSON.stringify({
      metrics: metricsData,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: Date.now()
    });

    try {
      if (isBeacon && 'sendBeacon' in navigator) {
        navigator.sendBeacon('/api/metrics/performance', payload);
      } else {
        await fetch('/api/metrics/performance', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: payload
        });
      }
    } catch (error) {
      console.warn('Failed to send performance metrics:', error);
    }
  }

  /**
   * Get metrics summary
   */
  getMetricsSummary() {
    const summary = {};

    // Navigation timing
    if (this.metrics.has('navigation')) {
      summary.navigation = this.metrics.get('navigation');
    }

    // Core Web Vitals
    const customMetrics = this.metrics.get('custom') || [];
    const lcp = customMetrics.filter(m => m.name === 'lcp').pop();
    const fid = customMetrics.filter(m => m.name === 'fid').pop();
    const cls = customMetrics.filter(m => m.name === 'cls').pop();

    if (lcp || fid || cls) {
      summary.coreWebVitals = {
        lcp: lcp?.value,
        fid: fid?.value,
        cls: cls?.value
      };
    }

    // Resource summary
    const resources = this.metrics.get('resources') || [];
    if (resources.length > 0) {
      summary.resources = {
        total: resources.length,
        cached: resources.filter(r => r.cached).length,
        totalSize: resources.reduce((sum, r) => sum + r.size, 0),
        avgDuration: resources.reduce((sum, r) => sum + r.duration, 0) / resources.length
      };
    }

    // Long tasks
    const longTasks = this.metrics.get('longTasks') || [];
    if (longTasks.length > 0) {
      summary.longTasks = {
        count: longTasks.length,
        totalDuration: longTasks.reduce((sum, t) => sum + t.duration, 0)
      };
    }

    return summary;
  }

  /**
   * Get performance report
   */
  getPerformanceReport() {
    return {
      metrics: this.getMetricsSummary(),
      timestamp: Date.now(),
      url: window.location.href
    };
  }

  /**
   * Clear all metrics
   */
  clearMetrics() {
    this.metrics.clear();
  }

  /**
   * Stop monitoring
   */
  stop() {
    this.isMonitoring = false;
    
    // Disconnect all observers
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
    
    console.log('Performance monitoring stopped');
  }
}

// Create singleton instance
const performanceOptimizer = new PerformanceOptimizer();

// Export utilities
export default performanceOptimizer;

export const initializePerformanceMonitoring = (config) => {
  performanceOptimizer.initialize(config);
};

export const recordMetric = (name, value, tags) => {
  performanceOptimizer.recordMetric(name, value, tags);
};

export const timeFunction = (name, fn) => {
  return performanceOptimizer.timeFunction(name, fn);
};

export const timeAsyncFunction = (name, fn) => {
  return performanceOptimizer.timeAsyncFunction(name, fn);
};

export const getPerformanceReport = () => {
  return performanceOptimizer.getPerformanceReport();
};
