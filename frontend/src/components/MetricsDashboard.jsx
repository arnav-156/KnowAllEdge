/**
 * Admin Metrics Dashboard Component
 * Displays real-time performance and usage metrics
 */

import React, { useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';
import analytics from '../utils/analytics';
import './MetricsDashboard.css';

const MetricsDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [frontendMetrics, setFrontendMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchMetrics();
    
    const interval = setInterval(() => {
      if (autoRefresh) {
        fetchMetrics();
      }
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const fetchMetrics = async () => {
    try {
      // Fetch backend metrics
      const backendResponse = await fetch('http://localhost:5000/api/metrics');
      const backendData = await backendResponse.json();
      setMetrics(backendData);

      // Get frontend session metrics
      const frontendData = {
        session: analytics.getSessionSummary(),
        api: analytics.getAPIStats()
      };
      setFrontendMetrics(frontendData);

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      setLoading(false);
    }
  };

  const exportMetrics = () => {
    analytics.exportMetrics();
  };

  if (loading) {
    return <div className="metrics-loading">Loading metrics...</div>;
  }

  return (
    <div className="metrics-dashboard">
      <div className="metrics-header">
        <h1>📊 KNOWALLEDGE Metrics Dashboard</h1>
        <div className="metrics-controls">
          <label>
            <input 
              type="checkbox" 
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh (5s)
          </label>
          <button onClick={fetchMetrics}>Refresh Now</button>
          <button onClick={exportMetrics}>Export Session Data</button>
        </div>
      </div>

      {/* User Experience Metrics */}
      <section className="metrics-section">
        <h2>👤 User Experience Metrics</h2>
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Page Load Time</h3>
            <div className="metric-value">
              {frontendMetrics?.session?.pageLoads > 0 
                ? `${(frontendMetrics.session.averageAPITime || 0).toFixed(0)}ms`
                : 'N/A'}
            </div>
            <div className="metric-label">Average page load</div>
          </div>

          <div className="metric-card">
            <h3>Time to First Interaction</h3>
            <div className="metric-value">
              {frontendMetrics?.session?.interactions > 0
                ? `${(analytics.metrics.interactions[0]?.timeToInteraction / 1000 || 0).toFixed(1)}s`
                : 'N/A'}
            </div>
            <div className="metric-label">From page load</div>
          </div>

          <div className="metric-card">
            <h3>Error Rate</h3>
            <div className={`metric-value ${frontendMetrics?.session?.errors > 0 ? 'metric-warning' : 'metric-success'}`}>
              {frontendMetrics?.session?.errors || 0}
            </div>
            <div className="metric-label">Errors in session</div>
          </div>

          <div className="metric-card">
            <h3>Session Duration</h3>
            <div className="metric-value">
              {frontendMetrics?.session?.duration 
                ? `${(frontendMetrics.session.duration / 1000 / 60).toFixed(1)}m`
                : 'N/A'}
            </div>
            <div className="metric-label">Current session</div>
          </div>
        </div>
      </section>

      {/* Performance Metrics */}
      <section className="metrics-section">
        <h2>⚡ API Performance Metrics</h2>
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Response Time (p50)</h3>
            <div className="metric-value">
              {frontendMetrics?.api?.p50?.toFixed(0) || 0}ms
            </div>
            <div className="metric-label">Median response time</div>
          </div>

          <div className="metric-card">
            <h3>Response Time (p95)</h3>
            <div className="metric-value">
              {frontendMetrics?.api?.p95?.toFixed(0) || 0}ms
            </div>
            <div className="metric-label">95th percentile</div>
          </div>

          <div className="metric-card">
            <h3>Response Time (p99)</h3>
            <div className="metric-value">
              {frontendMetrics?.api?.p99?.toFixed(0) || 0}ms
            </div>
            <div className="metric-label">99th percentile</div>
          </div>

          <div className="metric-card">
            <h3>API Success Rate</h3>
            <div className={`metric-value ${frontendMetrics?.api?.successRate >= 95 ? 'metric-success' : 'metric-warning'}`}>
              {frontendMetrics?.api?.successRate?.toFixed(1) || 0}%
            </div>
            <div className="metric-label">{frontendMetrics?.api?.totalCalls || 0} total calls</div>
          </div>
        </div>
      </section>

      {/* Backend Metrics */}
      {metrics && (
        <section className="metrics-section">
          <h2>🖥️ Backend Metrics</h2>
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Cache Hit Rate</h3>
              <div className={`metric-value ${metrics.cache?.hit_rate_percent >= 70 ? 'metric-success' : 'metric-warning'}`}>
                {metrics.cache?.hit_rate_percent || 0}%
              </div>
              <div className="metric-label">
                {metrics.cache?.hits || 0} hits / {metrics.cache?.misses || 0} misses
              </div>
            </div>

            <div className="metric-card">
              <h3>Total Requests</h3>
              <div className="metric-value">
                {metrics.total_requests || 0}
              </div>
              <div className="metric-label">
                {metrics.requests_per_second?.toFixed(2) || 0} req/s
              </div>
            </div>

            <div className="metric-card">
              <h3>Error Rate</h3>
              <div className={`metric-value ${metrics.error_rate_percent > 5 ? 'metric-warning' : 'metric-success'}`}>
                {metrics.error_rate_percent || 0}%
              </div>
              <div className="metric-label">
                {metrics.error_count || 0} errors
              </div>
            </div>

            <div className="metric-card">
              <h3>Concurrent Users</h3>
              <div className="metric-value">
                {metrics.concurrent_users || 0}
              </div>
              <div className="metric-label">Active now</div>
            </div>
          </div>

          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Uptime</h3>
              <div className="metric-value">
                {metrics.uptime_formatted || 'N/A'}
              </div>
              <div className="metric-label">Since server start</div>
            </div>
          </div>
        </section>
      )}

      {/* Endpoint Performance */}
      {metrics?.endpoints && (
        <section className="metrics-section">
          <h2>📍 Endpoint Performance</h2>
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>Calls</th>
                <th>Avg (ms)</th>
                <th>P50 (ms)</th>
                <th>P95 (ms)</th>
                <th>P99 (ms)</th>
                <th>Min (ms)</th>
                <th>Max (ms)</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metrics.endpoints).map(([endpoint, stats]) => (
                <tr key={endpoint}>
                  <td className="endpoint-name">{endpoint}</td>
                  <td>{stats.calls}</td>
                  <td>{stats.avg_ms.toFixed(0)}</td>
                  <td>{stats.p50_ms.toFixed(0)}</td>
                  <td className={stats.p95_ms > 3000 ? 'metric-warning' : ''}>
                    {stats.p95_ms.toFixed(0)}
                  </td>
                  <td className={stats.p99_ms > 5000 ? 'metric-warning' : ''}>
                    {stats.p99_ms.toFixed(0)}
                  </td>
                  <td>{stats.min_ms.toFixed(0)}</td>
                  <td>{stats.max_ms.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Status Codes */}
      {metrics?.status_codes && (
        <section className="metrics-section">
          <h2>📊 HTTP Status Codes</h2>
          <div className="status-codes">
            {Object.entries(metrics.status_codes).map(([code, count]) => (
              <div key={code} className="status-code-item">
                <span className={`status-code code-${code}`}>{code}</span>
                <span className="status-count">{count}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="metrics-footer">
        <p>Last updated: {new Date().toLocaleTimeString()}</p>
        <p>Session ID: {frontendMetrics?.session?.sessionId}</p>
      </div>
    </div>
  );
};

export default MetricsDashboard;
