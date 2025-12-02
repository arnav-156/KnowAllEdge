/**
 * Analytics and Performance Monitoring Utility
 * Tracks user experience metrics, performance, and errors
 */

class Analytics {
  constructor() {
    this.metrics = {
      pageLoads: [],
      interactions: [],
      errors: [],
      apiCalls: [],
      userSessions: []
    };
    
    this.userId = this.getOrCreateUserId();  // ✅ NEW: Persistent user ID
    this.sessionId = this.generateSessionId();
    this.sessionStart = Date.now();
    this.initialized = false;
    
    // Initialize only in browser environment
    if (typeof window !== 'undefined') {
      this.init();
    }
  }
  
  init() {
    if (this.initialized) return;
    this.initialized = true;
    
    try {
      this.initPerformanceObserver();
      this.initErrorTracking();
    } catch (error) {
      console.error('Analytics initialization error:', error);
    }
  }

  // ✅ NEW: Get or create persistent user ID (tracks across sessions)
  getOrCreateUserId() {
    if (typeof window === 'undefined') return null;
    
    try {
      // Try to get existing user ID from localStorage
      let userId = localStorage.getItem('analytics_user_id');
      
      if (!userId) {
        // Generate browser fingerprint for anonymous users
        userId = this.generateBrowserFingerprint();
        localStorage.setItem('analytics_user_id', userId);
        localStorage.setItem('analytics_user_created', new Date().toISOString());
      }
      
      return userId;
    } catch (error) {
      // Fallback if localStorage not available
      return this.generateBrowserFingerprint();
    }
  }

  // Generate browser fingerprint (stable across sessions)
  generateBrowserFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('fingerprint', 2, 2);
    
    const fingerprint = [
      navigator.userAgent,
      navigator.language,
      screen.colorDepth,
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset(),
      !!window.sessionStorage,
      !!window.localStorage,
      canvas.toDataURL()
    ].join('|');
    
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
      const char = fingerprint.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return `user_${Math.abs(hash).toString(36)}`;
  }

  // Generate unique session ID (new for each session)
  generateSessionId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // ✅ NEW: Extract UTM parameters from URL
  getUTMParameters() {
    if (typeof window === 'undefined') return {};
    
    try {
      const params = new URLSearchParams(window.location.search);
      const utm = {};
      
      ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'].forEach(key => {
        if (params.has(key)) {
          utm[key] = params.get(key);
        }
      });
      
      // Store in localStorage for attribution across session
      if (Object.keys(utm).length > 0) {
        localStorage.setItem('analytics_utm', JSON.stringify(utm));
        localStorage.setItem('analytics_utm_timestamp', Date.now().toString());
      }
      
      // Return stored UTM if no current params (for attribution)
      if (Object.keys(utm).length === 0) {
        const stored = localStorage.getItem('analytics_utm');
        if (stored) {
          return JSON.parse(stored);
        }
      }
      
      return utm;
    } catch (error) {
      return {};
    }
  }

  // Get referrer information
  getReferrer() {
    if (typeof document === 'undefined') return null;
    return document.referrer || null;
  }

  // Track page load performance
  trackPageLoad(pageName) {
    if (typeof window === 'undefined' || typeof performance === 'undefined') return;
    
    try {
      const perfData = performance.getEntriesByType('navigation')[0];
    
      const metrics = {
        sessionId: this.sessionId,
        pageName,
        timestamp: Date.now(),
        // ✅ NEW: Attribution data
        utm: this.getUTMParameters(),
        referrer: this.getReferrer(),
        // Core Web Vitals
        loadTime: perfData?.loadEventEnd - perfData?.fetchStart || 0,
        domContentLoaded: perfData?.domContentLoadedEventEnd - perfData?.fetchStart || 0,
        timeToFirstByte: perfData?.responseStart - perfData?.requestStart || 0,
        // Additional metrics
        dns: perfData?.domainLookupEnd - perfData?.domainLookupStart || 0,
        tcp: perfData?.connectEnd - perfData?.connectStart || 0,
        request: perfData?.responseStart - perfData?.requestStart || 0,
        response: perfData?.responseEnd - perfData?.responseStart || 0,
        processing: perfData?.domComplete - perfData?.domLoading || 0,
        onload: perfData?.loadEventEnd - perfData?.loadEventStart || 0
      };

      this.metrics.pageLoads.push(metrics);
      this.sendToAnalytics('page_load', metrics);
      
      return metrics;
    } catch (error) {
      console.error('trackPageLoad error:', error);
      return null;
    }
  }

  // Track time to first interaction
  trackFirstInteraction(element, action) {
    const timeToInteraction = Date.now() - this.sessionStart;
    
    const metric = {
      sessionId: this.sessionId,
      element,
      action,
      timeToInteraction,
      timestamp: Date.now()
    };

    this.metrics.interactions.push(metric);
    this.sendToAnalytics('first_interaction', metric);
    
    return metric;
  }

  // Track user interactions
  trackInteraction(eventType, elementId, metadata = {}) {
    const metric = {
      sessionId: this.sessionId,
      eventType,
      elementId,
      timestamp: Date.now(),
      ...metadata
    };

    this.metrics.interactions.push(metric);
    this.sendToAnalytics('interaction', metric);
  }

  // Track API call performance
  trackAPICall(endpoint, method, startTime, endTime, status, error = null) {
    const duration = endTime - startTime;
    
    const metric = {
      sessionId: this.sessionId,
      endpoint,
      method,
      duration,
      status,
      error: error ? error.message : null,
      timestamp: Date.now(),
      success: status >= 200 && status < 300
    };

    this.metrics.apiCalls.push(metric);
    this.sendToAnalytics('api_call', metric);
    
    return metric;
  }

  // Track errors
  trackError(error, context = {}) {
    const errorMetric = {
      sessionId: this.sessionId,
      message: error.message,
      stack: error.stack,
      type: error.name,
      context,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    this.metrics.errors.push(errorMetric);
    this.sendToAnalytics('error', errorMetric);
    
    console.error('Error tracked:', errorMetric);
  }

  // Track task completion
  trackTaskCompletion(taskName, success, duration, metadata = {}) {
    const metric = {
      sessionId: this.sessionId,
      taskName,
      success,
      duration,
      timestamp: Date.now(),
      ...metadata
    };

    this.sendToAnalytics('task_completion', metric);
  }

  // Track user satisfaction (1-5 stars)
  trackSatisfaction(rating, feedback = '') {
    const metric = {
      sessionId: this.sessionId,
      rating,
      feedback,
      timestamp: Date.now(),
      sessionDuration: Date.now() - this.sessionStart
    };

    this.sendToAnalytics('satisfaction', metric);
  }

  // Initialize Performance Observer for paint timing
  initPerformanceObserver() {
    try {
      if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;
      
      // First Contentful Paint
      try {
        const paintObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.name === 'first-contentful-paint') {
              this.sendToAnalytics('fcp', {
                sessionId: this.sessionId,
                value: entry.startTime,
                timestamp: Date.now()
              });
            }
          }
        });
        
        paintObserver.observe({ entryTypes: ['paint'] });
      } catch (e) {
        console.warn('Paint observer not supported:', e.message);
      }

      // Largest Contentful Paint
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          
          this.sendToAnalytics('lcp', {
            sessionId: this.sessionId,
            value: lastEntry.renderTime || lastEntry.loadTime,
            timestamp: Date.now()
          });
        });
        
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      } catch (e) {
        console.warn('LCP observer not supported:', e.message);
      }
    } catch (error) {
      console.error('Performance observer initialization error:', error);
    }
  }

  // Initialize error tracking
  initErrorTracking() {
    try {
      if (typeof window === 'undefined') return;
      
      window.addEventListener('error', (event) => {
        try {
          this.trackError(event.error, {
            type: 'global',
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
          });
        } catch (e) {
          console.error('Error tracking failed:', e);
        }
      });

      window.addEventListener('unhandledrejection', (event) => {
        try {
          this.trackError(new Error(event.reason), {
            type: 'unhandled_promise_rejection'
          });
        } catch (e) {
          console.error('Promise rejection tracking failed:', e);
        }
      });
    } catch (error) {
      console.error('Error tracking initialization error:', error);
    }
  }

  // Get session summary
  getSessionSummary() {
    const sessionDuration = Date.now() - this.sessionStart;
    
    return {
      sessionId: this.sessionId,
      duration: sessionDuration,
      pageLoads: this.metrics.pageLoads.length,
      interactions: this.metrics.interactions.length,
      errors: this.metrics.errors.length,
      apiCalls: this.metrics.apiCalls.length,
      successfulAPICalls: this.metrics.apiCalls.filter(c => c.success).length,
      averageAPITime: this.calculateAverage(this.metrics.apiCalls.map(c => c.duration))
    };
  }

  // Calculate average
  calculateAverage(numbers) {
    if (numbers.length === 0) return 0;
    return numbers.reduce((a, b) => a + b, 0) / numbers.length;
  }

  // Calculate percentile
  calculatePercentile(numbers, percentile) {
    if (numbers.length === 0) return 0;
    const sorted = [...numbers].sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[index];
  }

  // Get API performance stats
  getAPIStats() {
    const durations = this.metrics.apiCalls.map(c => c.duration);
    
    return {
      totalCalls: this.metrics.apiCalls.length,
      successRate: (this.metrics.apiCalls.filter(c => c.success).length / this.metrics.apiCalls.length * 100) || 0,
      p50: this.calculatePercentile(durations, 50),
      p95: this.calculatePercentile(durations, 95),
      p99: this.calculatePercentile(durations, 99),
      average: this.calculateAverage(durations),
      errors: this.metrics.apiCalls.filter(c => !c.success).length
    };
  }

  // Send to analytics backend (customize based on your analytics service)
  sendToAnalytics(eventType, data) {
    try {
      // ✅ NEW: Add user ID to all events
      const enrichedData = {
        ...data,
        userId: this.userId,
        sessionId: this.sessionId,
        timestamp: Date.now()
      };
      
      // Option 1: Send to your own backend
      if (import.meta.env.MODE === 'production') {
        fetch('/api/analytics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ eventType, data: enrichedData })
        }).catch(err => console.warn('Analytics send failed:', err));
      }

      // Option 2: Google Analytics (if configured)
      if (typeof window !== 'undefined' && window.gtag) {
        window.gtag('event', eventType, enrichedData);
        // Set user ID in GA4 for cross-session tracking
        window.gtag('set', { 'user_id': this.userId });
      }

      // Option 3: Console log in development
      if (import.meta.env.DEV) {
        console.log('[Analytics]', eventType, enrichedData);
      }
    } catch (error) {
      // Silently fail - analytics shouldn't break the app
      console.warn('Analytics error:', error);
    }
  }

  // Export metrics to download
  exportMetrics() {
    const data = {
      session: this.getSessionSummary(),
      apiStats: this.getAPIStats(),
      allMetrics: this.metrics
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `KNOWALLEDGE-metrics-${this.sessionId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// Create singleton instance
const analytics = new Analytics();

export default analytics;
