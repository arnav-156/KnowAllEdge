# 🚀 Monitoring Quick Start Guide

**Get your monitoring stack running in 15 minutes!**

---

## ✅ What's Already Working (No Setup Required)

1. **Prometheus Metrics**: http://localhost:5000/metrics
2. **Analytics Database**: SQLite-based, auto-created
3. **Token Counting**: Tracking Gemini API usage
4. **Cost Tracking**: Real-time cost estimates

**Test it now:**
```powershell
# Check Prometheus metrics
curl http://localhost:5000/metrics

# Check analytics
curl http://localhost:5000/api/analytics/summary

# Check token usage
curl http://localhost:5000/api/metrics/costs
```

---

## 🔧 Quick Setup (15 minutes)

### Step 1: Activate Sentry Error Tracking (5 minutes)

**Why?** Automatically catch and report errors with full context

1. **Sign up**: https://sentry.io (free tier: 5,000 errors/month)
2. **Create project**: "KNOWALLEDGE-backend" (Python/Flask)
3. **Copy DSN**: Looks like `https://abc123@o123.ingest.sentry.io/456`
4. **Add to `.env`**:
   ```bash
   # In backend/.env, uncomment and update:
   SENTRY_DSN=https://your-actual-dsn-here@o123.ingest.sentry.io/456
   ```
5. **Restart server**: `python main.py`

**Verify**:
```powershell
# Check logs for: "Sentry error tracking initialized"
# Test error tracking:
curl http://localhost:5000/api/test/sentry
# Should see error in Sentry dashboard within 30 seconds
```

---

### Step 2: Activate Google Analytics 4 (10 minutes)

**Why?** Track user behavior, conversion funnels, Core Web Vitals

1. **Sign up**: https://analytics.google.com/
2. **Create GA4 property**:
   - Property name: "KNOWALLEDGE"
   - Industry: Education
   - Business size: Small
3. **Copy Measurement ID**: Format `G-XXXXXXXXXX`
4. **Update frontend**:
   - Open `frontend/index.html`
   - Line 9: Replace `G-XXXXXXXXXX` with your actual ID
   - Line 12: Replace `G-XXXXXXXXXX` with your actual ID
5. **Optional - Add to `.env`**:
   ```bash
   # In backend/.env:
   GA4_MEASUREMENT_ID=G-XXXXXXXXXX
   ```
6. **Restart frontend**: `npm run dev`

**Verify**:
```powershell
# Visit: http://localhost:5173
# Open browser console (F12)
# Should see: gtag.js loaded
# Check GA4 Real-time report (after 1 minute)
```

---

## 📊 Available Endpoints

### Analytics
```powershell
# Summary (funnel + performance + DB size)
curl http://localhost:5000/api/analytics/summary

# Funnel conversion rates
curl http://localhost:5000/api/analytics/funnel

# Performance metrics (Core Web Vitals)
curl http://localhost:5000/api/analytics/performance

# Error summary
curl http://localhost:5000/api/analytics/errors
```

### Token Usage & Costs
```powershell
# Current usage and costs
curl http://localhost:5000/api/metrics/costs

# Estimate monthly costs
curl "http://localhost:5000/api/metrics/costs/estimate?daily_requests=100&avg_tokens=2000"
```

### Prometheus Metrics
```powershell
# All metrics (text format)
curl http://localhost:5000/metrics

# Example queries:
# - http_requests_total
# - http_request_duration_seconds
# - quota_requests_current_minute
# - cache_hit_rate
```

---

## 🎯 What to Monitor

### Daily
- **Sentry dashboard**: Any new errors?
- **GA4 Real-time**: Active users count
- **Token usage**: Are you approaching limits?
  ```powershell
  curl http://localhost:5000/api/metrics/costs | grep "percent_used"
  ```

### Weekly
- **Conversion funnel**: Where are users dropping off?
  ```powershell
  curl http://localhost:5000/api/analytics/funnel
  ```
- **Performance**: Is the site getting slower?
  ```powershell
  curl http://localhost:5000/api/analytics/performance
  ```

### Monthly
- **Cost trends**: Are API costs increasing?
  ```powershell
  curl http://localhost:5000/api/metrics/costs | grep "estimated_cost_monthly"
  ```

---

## ⚠️ Quota Limits (Free Tier)

### Gemini API
- 15 requests per minute
- 1M tokens per minute
- 1,500 requests per day
- 50M tokens per day

**Check current usage:**
```powershell
curl http://localhost:5000/api/metrics/costs
```

**Warning signs** (automatically tracked):
- ⚠️ 80%+ of any limit
- 🔴 429 errors (quota exceeded)

---

## 🚨 Troubleshooting

### Prometheus /metrics returns 404
**Fix**: Install prometheus-client
```powershell
pip install prometheus-client==0.20.0
```

### Sentry not capturing errors
**Check**:
1. SENTRY_DSN in `.env` correct?
2. Server restarted after adding DSN?
3. Test with: `curl http://localhost:5000/api/test/sentry`

### GA4 not showing events
**Check**:
1. Measurement ID correct in `frontend/index.html`?
2. Ad blocker disabled?
3. Browser console shows gtag.js loaded?
4. Wait 1-2 minutes for processing

### Analytics database growing too fast
**Cleanup**:
```powershell
# Delete data older than 30 days
curl -X POST "http://localhost:5000/api/analytics/cleanup?days=30"
```

---

## 🎓 Next Steps

### Today (15 minutes)
- ✅ Activate Sentry
- ✅ Activate GA4
- ✅ Test endpoints

### This Week (3 hours)
- [ ] Install Grafana: `docker run -d -p 3000:3000 grafana/grafana`
- [ ] Add Prometheus data source in Grafana
- [ ] Create dashboard (see MONITORING_ANALYTICS_IMPLEMENTATION.md)
- [ ] Set up alerts (error rate > 5%)

### This Month (6 hours)
- [ ] Integrate token counting into ALL API calls
- [ ] Add semantic caching (90% cost reduction)
- [ ] Deploy to production (Railway/Render)
- [ ] Set up uptime monitoring

---

## 📚 Full Documentation

- **Complete Guide**: `MONITORING_ANALYTICS_IMPLEMENTATION.md`
- **Implementation Status**: `MONITORING_IMPLEMENTATION_COMPLETE.md`
- **Metrics Reference**: `METRICS_GUIDE.md`

---

## ✅ Checklist

- [ ] Prometheus metrics working (`/metrics` returns 200)
- [ ] Sentry DSN added to `.env`
- [ ] GA4 Measurement ID in `frontend/index.html`
- [ ] Analytics database created (`analytics.db` exists)
- [ ] Token counter tracking usage
- [ ] All endpoints tested

**Status**: Ready for production! 🎉

---

**Last Updated**: November 20, 2025  
**Estimated Setup Time**: 15 minutes  
**Difficulty**: Easy (copy-paste configuration)
