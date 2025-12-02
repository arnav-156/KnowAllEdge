# Metrics System Quick Start Guide

## Installation Complete ✅

All metrics tracking components have been successfully integrated into KNOWALLEDGE!

## What Was Added

### Frontend Files Created
- ✅ `frontend/src/utils/analytics.js` - Core analytics tracking
- ✅ `frontend/src/utils/apiClient.js` - Enhanced API wrapper
- ✅ `frontend/src/components/MetricsDashboard.jsx` - Admin dashboard
- ✅ `frontend/src/components/MetricsDashboard.css` - Dashboard styles

### Backend Files Created
- ✅ `backend/metrics.py` - Metrics collector
- ✅ `backend/analytics_routes.py` - Analytics endpoints

### Files Modified
- ✅ `frontend/src/App.jsx` - Added metrics route
- ✅ `frontend/src/Homepage.jsx` - Analytics integration + dashboard link
- ✅ `frontend/src/SubtopicPage.jsx` - Analytics + apiClient integration
- ✅ `frontend/src/Loadingscreen.jsx` - Analytics + apiClient integration
- ✅ `frontend/src/GraphPage.jsx` - Analytics integration
- ✅ `backend/main.py` - Metrics integration + analytics blueprint

## Quick Test (5 minutes)

### 1. Start the Backend
```powershell
cd backend
python main.py
```

Expected output:
```
Starting KNOWALLEDGE API Server
Google AI: Configured
Analytics blueprint registered ✓
Server running on http://localhost:5000
```

### 2. Start the Frontend
```powershell
cd frontend
npm run dev
```

Expected output:
```
VITE ready in 500ms
Local: http://localhost:5173
```

### 3. Test User Flow

1. **Open Homepage**: http://localhost:5173
   - Notice "📊 Metrics Dashboard" button (bottom right)
   - Page load time is being tracked ✅

2. **Enter a Topic**: e.g., "Artificial Intelligence"
   - Click "Generate subtopics"
   - API call is being tracked ✅

3. **Select Subtopics**:
   - Choose 3-5 subtopics
   - Select education level and detail
   - Click "Generate"
   - API calls are being tracked ✅

4. **View Concept Map**:
   - Task completion tracked ✅

5. **Open Metrics Dashboard**:
   - Click "📊 Metrics Dashboard" button
   - Or navigate to: http://localhost:5173/metrics

### 4. Verify Metrics Dashboard

You should see:

#### User Experience Section
- **Page Load Time**: ~500-1000ms ✅
- **Time to First Interaction**: ~1-3 seconds ✅
- **Error Count**: 0 (hopefully!) ✅
- **Session Duration**: Current session time ✅

#### API Performance Section
- **p50 Response Time**: ~800-1500ms ✅
- **p95 Response Time**: ~2000-3000ms ✅
- **p99 Response Time**: ~3000-5000ms ✅
- **Success Rate**: 100% ✅

#### Backend Metrics Section
- **Cache Hit Rate**: 0-75% (depends on repeat requests) ✅
- **Total Requests**: Number of API calls made ✅
- **Error Rate**: 0% ✅
- **Concurrent Users**: 1 (just you) ✅
- **Uptime**: Server uptime in seconds ✅

#### Endpoint Performance Table
Should show statistics for:
- `/api/create_subtopics`
- `/api/create_presentation`
- `/api/health`
- `/api/analytics/summary`

#### Status Code Distribution
- **200**: Most requests ✅
- **400/500**: Only if errors occurred

### 5. Test Export Feature

On the metrics dashboard:
1. Click "Export Session Data"
2. Downloads `KNOWALLEDGE-metrics-{timestamp}.json`
3. Open file to see all tracked events

## Verification Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Homepage loads and tracks page load
- [ ] API calls work (subtopics, presentation)
- [ ] Metrics dashboard accessible via button
- [ ] Dashboard shows user experience metrics
- [ ] Dashboard shows API performance metrics
- [ ] Dashboard shows backend metrics
- [ ] Dashboard shows endpoint breakdown
- [ ] Auto-refresh works (toggle on/off)
- [ ] Export downloads JSON file
- [ ] No errors in browser console
- [ ] No errors in backend logs (`backend/app.log`)

## Expected Behavior

### First Request (Cache Miss)
- **Response Time**: ~1500-3000ms
- **Cache Hit Rate**: 0%
- **Status**: 200 OK

### Second Request (Same Topic)
- **Response Time**: ~50-200ms (much faster!)
- **Cache Hit Rate**: 50%+
- **Status**: 200 OK

### Dashboard Auto-Refresh
- Updates every 5 seconds
- Toggle to disable/enable
- Shows "Last updated" timestamp

## Troubleshooting

### Metrics Dashboard Shows No Data

**Problem**: All metrics show 0 or "N/A"

**Solutions**:
1. Make sure you've used the app (generate subtopics, etc.)
2. Check browser console for errors
3. Verify `/api/analytics/summary` returns 200 OK
4. Check that apiClient is being used (not plain axios)

**Test Backend Directly**:
```powershell
curl http://localhost:5000/api/health
```

Should return JSON with metrics.

### API Calls Not Being Tracked

**Problem**: Endpoint Performance table is empty

**Solutions**:
1. Verify backend imports: `from metrics import metrics_collector, track_request_metrics`
2. Check decorators are on routes: `@track_request_metrics`
3. Restart backend server
4. Make a test API call

### Frontend Metrics Not Appearing

**Problem**: Page load time shows 0

**Solutions**:
1. Check analytics.js imported correctly
2. Verify `analytics.trackPageLoad()` called in useEffect
3. Check browser console for errors
4. Hard refresh browser (Ctrl+Shift+R)

### High Error Rates

**Problem**: Error rate > 0%

**Solutions**:
1. Check `/api/analytics/errors` endpoint
2. Review browser console
3. Check backend logs: `backend/app.log`
4. Verify Google AI API key is valid
5. Check rate limiting isn't triggered

## Performance Benchmarks

### Expected Response Times

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| `/api/create_subtopics` | 1000ms | 2000ms | 3000ms |
| `/api/create_presentation` | 2500ms | 4000ms | 6000ms |
| `/api/health` | 50ms | 100ms | 150ms |
| `/api/analytics/summary` | 100ms | 200ms | 300ms |

### Expected Cache Performance

- **Cache Hit Rate**: 40-70% (after warming up)
- **Cache TTL**: 3600 seconds (1 hour)
- **Cache Size**: <100 entries typically

### Expected Error Rates

- **Production**: <1% error rate
- **Development**: <5% error rate (more frequent changes)

## Next Steps

### 1. Customize Thresholds

Edit `MetricsDashboard.jsx`:
```javascript
// Change warning thresholds
const avgLoadTime = frontendStats.avgPageLoad;
const isSlowLoad = avgLoadTime > 2000; // Adjust this (default: 2000ms)
```

### 2. Add Custom Events

Track custom user actions:
```javascript
// In your component
import analytics from './utils/analytics';

const handleCustomAction = () => {
  // Your action code...
  analytics.trackTaskCompletion('custom_action_name', true);
};
```

### 3. Add More Endpoints

To track new API endpoints:
```python
# backend/main.py
@app.route('/api/new_endpoint')
@track_request_metrics  # Add this decorator
def new_endpoint():
    # Your code...
```

### 4. Set Up Monitoring

Add alert system (future enhancement):
- Email notifications for high error rates
- Slack integration for performance degradation
- Grafana dashboards for advanced visualization

### 5. Production Deployment

Before deploying:
1. **Secure Metrics Dashboard**: Add authentication
2. **Persistent Storage**: Use Redis/PostgreSQL for metrics
3. **HTTPS**: Enable SSL/TLS
4. **Rate Limiting**: Adjust based on traffic
5. **Logging**: Set up centralized logging (e.g., ELK stack)

## Testing Scenarios

### Scenario 1: Happy Path
1. Enter topic: "Machine Learning"
2. Generate subtopics (should take ~1-2 seconds)
3. Select 3 subtopics
4. Generate presentation (should take ~3-5 seconds)
5. View concept map
6. Check metrics dashboard

**Expected Metrics**:
- 3-4 page loads
- 2 API calls
- 100% success rate
- 0 errors

### Scenario 2: Cache Testing
1. Generate subtopics for "Python Programming"
2. Note response time (e.g., 1500ms)
3. Go back and generate same topic again
4. Note response time (should be <200ms)
5. Check cache hit rate (should increase)

**Expected Metrics**:
- Cache hit rate: 50%+
- p50 response time: decreases on second request

### Scenario 3: Error Handling
1. Try invalid topic (empty string, special characters)
2. Should see error message
3. Check metrics dashboard
4. View error count (should increment)
5. Check `/api/analytics/errors` endpoint

**Expected Metrics**:
- Error count: 1+
- Error rate: >0%
- Error details in logs

## Support

### Logs to Check

1. **Backend Logs**: `backend/app.log`
   - API errors
   - Performance warnings
   - Cache events

2. **Frontend Console**: Browser DevTools (F12)
   - JavaScript errors
   - API response errors
   - Analytics events

3. **Metrics File**: `backend/frontend_metrics.jsonl`
   - Raw frontend metrics
   - JSONL format (one JSON object per line)

### Debug Mode

Enable verbose logging:

**Backend**:
```python
# backend/main.py
logging.basicConfig(level=logging.DEBUG)  # Change from INFO
```

**Frontend**:
```javascript
// In browser console
localStorage.setItem('debug', 'true');
```

### Health Check

Quick health verification:
```powershell
# Backend health
curl http://localhost:5000/api/health

# Metrics summary
curl http://localhost:5000/api/analytics/summary

# Recent errors
curl http://localhost:5000/api/analytics/errors
```

## Documentation

- **Full Guide**: `METRICS_GUIDE.md` - Comprehensive documentation
- **API Docs**: http://localhost:5000/api/docs - OpenAPI specification
- **Main README**: `README.md` - Project overview

## Success Indicators

Your metrics system is working if:

✅ Dashboard loads without errors  
✅ Metrics update in real-time  
✅ All API calls are tracked  
✅ Page load times are recorded  
✅ Cache hit rate increases over time  
✅ Error tracking works (when errors occur)  
✅ Export functionality downloads data  
✅ Backend endpoints return 200 OK  
✅ No console errors  
✅ Performance metrics look reasonable  

## Congratulations! 🎉

Your comprehensive metrics tracking system is now live. You can:
- Monitor user experience in real-time
- Track API performance with percentiles
- Identify bottlenecks and errors
- Make data-driven optimization decisions
- Export data for further analysis

Happy monitoring! 📊
