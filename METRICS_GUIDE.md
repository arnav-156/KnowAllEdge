# KNOWALLEDGE Metrics System Guide

## Overview

This guide documents the comprehensive metrics tracking system integrated into KNOWALLEDGE. The system provides real-time insights into user experience, application performance, and backend health.

## Architecture

### Frontend Components

#### 1. **analytics.js** (`frontend/src/utils/analytics.js`)
Core analytics utility that tracks:
- **Session Management**: Unique session IDs, session duration
- **Page Load Times**: Using Navigation Timing API
- **Time to First Interaction**: Measures user engagement
- **API Call Performance**: Response times, status codes
- **Error Tracking**: Global errors, unhandled promise rejections
- **Performance Metrics**: First Contentful Paint (FCP), Largest Contentful Paint (LCP)

**Key Methods**:
```javascript
analytics.trackPageLoad('PageName')
analytics.trackFirstInteraction()
analytics.trackAPICall(endpoint, duration, status)
analytics.trackError(error, context)
analytics.trackTaskCompletion(taskName, success)
analytics.trackUserSatisfaction(rating)
analytics.exportMetrics() // Download session data
```

#### 2. **apiClient.js** (`frontend/src/utils/apiClient.js`)
Enhanced axios wrapper that automatically tracks:
- Request/response timing
- API success/failure rates
- Error logging with context
- User-friendly error formatting

**Usage**:
```javascript
import apiClient from './utils/apiClient';

// Automatically tracked
const response = await apiClient.createSubtopics(topic);
const presentation = await apiClient.createPresentation(topic, level, focus, detail);
```

#### 3. **MetricsDashboard.jsx** (`frontend/src/components/MetricsDashboard.jsx`)
Admin dashboard displaying:
- **User Experience**: Page load times, interaction latency, error rates
- **API Performance**: p50, p95, p99 response times, success rates
- **Backend Metrics**: Cache hit rate, concurrent users, uptime
- **Endpoint Breakdown**: Per-endpoint performance statistics
- **Status Codes**: HTTP status code distribution

**Access**: Navigate to `/metrics` or click "📊 Metrics Dashboard" button on homepage

### Backend Components

#### 1. **metrics.py** (`backend/metrics.py`)
Thread-safe metrics collector providing:
- Request tracking (endpoint, method, status, duration)
- Cache hit/miss recording
- Concurrent user management
- Statistical calculations (p50, p95, p99)
- Health status determination

**Key Features**:
```python
from metrics import metrics_collector, track_request_metrics

# Decorator for automatic tracking
@app.route('/api/endpoint')
@track_request_metrics
def endpoint():
    # Automatically tracked: duration, status, errors
    pass

# Manual tracking
metrics_collector.record_request('/api/test', 'POST', 200, 0.5)
metrics_collector.record_cache_event('hit')
metrics_collector.add_concurrent_user('user_id')
```

#### 2. **analytics_routes.py** (`backend/analytics_routes.py`)
Flask blueprint with endpoints:

**POST /api/analytics**
- Receives frontend metrics (page loads, interactions, errors)
- Stores in-memory and persists to JSONL file

**GET /api/analytics/summary**
- Returns aggregated frontend statistics
- Average load times, error rates, API success rates

**GET /api/analytics/errors**
- Returns recent error logs with context

## Metrics Tracked

### User Experience Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| Page Load Time | Navigation timing (DOMContentLoaded) | `analytics.js` |
| Time to First Interaction | Latency until user action | `analytics.js` |
| Error Rate | Frontend errors per session | `analytics.js` |
| Task Completion | Success/failure of user goals | `analytics.js` |
| User Satisfaction | Optional rating (1-5 stars) | `analytics.js` |
| Session Duration | Total time on site | `analytics.js` |

### Performance Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| API Response Time (p50) | Median response time | `metrics.py` |
| API Response Time (p95) | 95th percentile | `metrics.py` |
| API Response Time (p99) | 99th percentile | `metrics.py` |
| Success Rate | % of successful API calls | `metrics.py` |
| Cache Hit Rate | % of cache hits | `metrics.py` |
| Concurrent Users | Active users | `metrics.py` |

### Quality Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| Error Count | Backend errors | `metrics.py` |
| Endpoint Performance | Per-endpoint stats | `metrics.py` |
| Status Code Distribution | HTTP status breakdown | `metrics.py` |
| Uptime | Server uptime | `metrics.py` |

## Integration Guide

### Frontend Integration

1. **Import Analytics**:
```javascript
import analytics from './utils/analytics';
```

2. **Track Page Load**:
```javascript
useEffect(() => {
  analytics.trackPageLoad('PageName');
}, []);
```

3. **Track First Interaction**:
```javascript
useEffect(() => {
  const handleFirstInteraction = () => {
    analytics.trackFirstInteraction();
    window.removeEventListener('click', handleFirstInteraction);
  };
  
  window.addEventListener('click', handleFirstInteraction);
  
  return () => {
    window.removeEventListener('click', handleFirstInteraction);
  };
}, []);
```

4. **Replace Axios with apiClient**:
```javascript
// Before
import axios from 'axios';
const response = await axios.post('http://localhost:5000/api/create_subtopics', data);

// After
import apiClient from './utils/apiClient';
const response = await apiClient.createSubtopics(topic);
```

### Backend Integration

1. **Import Metrics**:
```python
from metrics import metrics_collector, track_request_metrics
from analytics_routes import analytics_bp
```

2. **Register Blueprint**:
```python
app.register_blueprint(analytics_bp)
```

3. **Add Decorator to Routes**:
```python
@app.route('/api/endpoint')
@track_request_metrics
def endpoint():
    # Automatically tracked
    pass
```

4. **Track Cache Events**:
```python
if cache_hit:
    metrics_collector.record_cache_event('hit')
else:
    metrics_collector.record_cache_event('miss')
```

## Usage Examples

### Viewing Metrics Dashboard

1. Start both servers:
```bash
# Backend
cd backend
python main.py

# Frontend
cd frontend
npm run dev
```

2. Navigate to: `http://localhost:5173/metrics`

3. View real-time metrics (auto-refreshes every 5 seconds)

### Exporting Session Data

Click "Export Session Data" button on the dashboard to download a JSON file with:
- Page load times
- API call history
- Error logs
- Performance metrics

### Monitoring API Performance

The dashboard shows:
- **p50** (median): Typical response time
- **p95**: 95% of requests faster than this
- **p99**: 99% of requests faster than this
- **Min/Max**: Fastest and slowest responses

**Interpretation**:
- p50 < 500ms: Good ✅
- p50 > 1000ms: Needs optimization ⚠️
- p99 > 3000ms: Critical ❌

### Tracking User Tasks

```javascript
// Track successful task completion
analytics.trackTaskCompletion('generate_concept_map', true);

// Track failed task
analytics.trackTaskCompletion('upload_image', false, 'File too large');
```

### Error Tracking

Automatic tracking of:
- Unhandled JavaScript errors
- Unhandled promise rejections
- API failures

Manual error tracking:
```javascript
try {
  await riskyOperation();
} catch (error) {
  analytics.trackError(error, { 
    page: 'SubtopicPage', 
    action: 'fetchSubtopics' 
  });
}
```

## Performance Optimization Tips

### Frontend

1. **Reduce API Calls**: Use local state when possible
2. **Lazy Load Components**: Reduce initial page load
3. **Optimize Images**: Compress before upload
4. **Cache Static Assets**: Use service workers

### Backend

1. **Increase Cache TTL**: For rarely changing data
2. **Parallel Processing**: Already implemented for presentations
3. **Rate Limiting**: Adjust based on metrics
4. **Database Indexing**: If adding persistent storage

### Monitoring Recommendations

1. **Set Alerts**:
   - Error rate > 5%
   - p99 response time > 3000ms
   - Cache hit rate < 60%

2. **Regular Reviews**:
   - Daily: Error logs
   - Weekly: Performance trends
   - Monthly: Capacity planning

3. **User Feedback**:
   - Track satisfaction ratings
   - Monitor task completion rates
   - Analyze common error patterns

## Data Persistence

### Frontend Metrics

- **In-Memory**: Last 1000 events per session
- **File**: `backend/frontend_metrics.jsonl` (append-only)
- **Export**: On-demand JSON download

### Backend Metrics

- **In-Memory**: Full request history
- **Aggregated**: Real-time statistics calculation
- **Retention**: Until server restart (add Redis for persistence)

## Health Metrics API

**GET /api/health**

Returns:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "cache_size": 42,
  "metrics": {
    "total_requests": 1234,
    "error_rate": 0.02,
    "cache_hit_rate": 0.75,
    "avg_response_time": 450,
    "p50_response_time": 380,
    "p95_response_time": 920,
    "p99_response_time": 1500,
    "concurrent_users": 8,
    "uptime_seconds": 86400,
    "health_status": "healthy"
  }
}
```

**Health Status**:
- `healthy`: All metrics within normal ranges
- `degraded`: Some metrics elevated
- `unhealthy`: Critical thresholds exceeded

## Troubleshooting

### Metrics Not Appearing

1. **Check Browser Console**: Verify analytics.js loaded
2. **Verify Endpoints**: Ensure `/api/analytics` returns 200
3. **Check CORS**: Confirm frontend allowed in backend
4. **Restart Servers**: Clear stale connections

### High Error Rates

1. **Check Error Logs**: `/api/analytics/errors`
2. **Review Stack Traces**: Frontend console
3. **API Status**: Verify backend health
4. **Rate Limiting**: Check if hitting limits

### Slow Performance

1. **Check p95/p99**: Identify slow endpoints
2. **Cache Hit Rate**: Should be > 60%
3. **Concurrent Users**: Check if overloaded
4. **LLM API**: Google AI may have delays

## Future Enhancements

### Planned Features

1. **Persistent Storage**: Redis for metrics
2. **Grafana Integration**: Advanced visualizations
3. **Alert System**: Email/Slack notifications
4. **A/B Testing**: Feature flag support
5. **User Segmentation**: Cohort analysis
6. **Session Replay**: Video recordings
7. **Performance Budgets**: Automated enforcement
8. **Synthetic Monitoring**: Automated tests

### Contributing

When adding new metrics:

1. **Frontend**: Add method to `analytics.js`
2. **Backend**: Update `metrics.py` collector
3. **Dashboard**: Add visualization to `MetricsDashboard.jsx`
4. **Documentation**: Update this guide

## Security Considerations

1. **PII Protection**: No personal data in metrics
2. **Access Control**: Secure metrics dashboard (add auth)
3. **Rate Limiting**: Prevent metrics endpoint abuse
4. **Data Retention**: Purge old logs regularly
5. **HTTPS**: Use in production

## Support

For issues or questions:
1. Check error logs: `backend/app.log`
2. Review frontend console
3. Check metrics dashboard for anomalies
4. Verify environment configuration

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Maintainer**: KNOWALLEDGE Team
