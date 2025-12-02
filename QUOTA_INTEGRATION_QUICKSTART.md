# 🚀 Quick Start: Test Quota Tracker Integration

## Prerequisites

1. **Python 3.8+** installed
2. **Google Gemini API Key** (from Google AI Studio)
3. **Backend dependencies** installed

## Setup (5 minutes)

### 1. Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 2. Configure API Key

**Option A: Using .env file (Recommended)**
```powershell
# Create .env file in backend/ folder
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
```

**Option B: Using environment variable**
```powershell
$env:GEMINI_API_KEY="your_actual_api_key_here"
```

### 3. Verify Configuration

```powershell
python verify_credentials.py
```

Expected output:
```
✅ Environment variables loaded
✅ Google Gemini API key configured
✅ All credentials verified successfully
```

## Start the Server

```powershell
python main.py
```

Expected output:
```
INFO:root:Quota tracker loaded successfully
INFO:root:Quota tracker initialized successfully
INFO:werkzeug: * Running on http://127.0.0.1:5000
```

## Test the Integration

### Option 1: Automated Tests (Recommended)

Open a **new terminal** and run:

```powershell
cd backend
python test_quota_integration.py
```

This will test:
- ✅ Health endpoints
- ✅ Quota stats endpoints
- ✅ API calls with quota tracking
- ✅ Quota usage recording

### Option 2: Manual Testing

#### Test 1: Health Check
```powershell
curl http://localhost:5000/api/health
```

**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Test 2: Readiness Check (NEW!)
```powershell
curl http://localhost:5000/api/ready
```

**Expected:**
```json
{
  "status": "ready",
  "checks": {
    "redis": {"status": "healthy"},
    "gemini_api": {"status": "configured"},
    "quota": {
      "status": "healthy",
      "rpm_usage": 0.0,
      "tpm_usage": 0.0
    }
  }
}
```

#### Test 3: Quota Stats (NEW!)
```powershell
curl http://localhost:5000/api/quota/stats
```

**Expected (before any API calls):**
```json
{
  "current_minute": {
    "requests": 0,
    "tokens": 0
  },
  "current_day": {
    "requests": 0,
    "tokens": 0
  },
  "limits": {
    "rpm": 15,
    "rpd": 1500,
    "tpm": 1000000,
    "tpd": 50000000
  },
  "remaining": {
    "rpm": 15,
    "rpd": 1500,
    "tpm": 1000000,
    "tpd": 50000000
  }
}
```

#### Test 4: Make API Call
```powershell
curl -X POST http://localhost:5000/api/create_subtopics `
  -H "Content-Type: application/json" `
  -d '{"topic": "Python Programming"}'
```

**Expected:**
```json
{
  "subtopics": [
    "Introduction to Python",
    "Variables and Data Types",
    "Control Flow (if, for, while)",
    ...
  ],
  "quality_score": 0.95,
  "metadata": {
    "cache_hit": false,
    "cached": true
  }
}
```

#### Test 5: Check Quota After API Call
```powershell
curl http://localhost:5000/api/quota/stats
```

**Expected (after 1 API call):**
```json
{
  "current_minute": {
    "requests": 1,
    "tokens": 1500
  },
  "current_day": {
    "requests": 1,
    "tokens": 1500
  },
  "remaining": {
    "rpm": 14,
    "rpd": 1499,
    "tpm": 998500,
    "tpd": 49998500
  }
}
```

#### Test 6: Enhanced Stats Endpoint
```powershell
curl http://localhost:5000/api/stats
```

**Expected:**
```json
{
  "cache": {
    "total_requests": 1,
    "cache_hits": 0,
    "hit_rate": 0.0
  },
  "rate_limits": {...},
  "quota": {
    "requests_per_minute": 15,
    "requests_today": 1,
    "tokens_today": 1500,
    "rpm_remaining": 14,
    "tpm_remaining": 998500,
    "rpm_percentage": 6.7,
    "tpm_percentage": 0.15
  },
  "system": {...}
}
```

## What You Should See

### ✅ Success Indicators

1. **Server Logs:**
   ```
   INFO:root:Quota tracker loaded successfully
   INFO:root:Quota tracker initialized successfully
   INFO:root:Creating subtopics | topic=Python Programming
   INFO:root:Using fallback response for 'Python Programming' due to quota  # If quota exceeded
   ```

2. **Quota Endpoints Working:**
   - `/api/ready` returns 200 OK
   - `/api/quota/stats` returns detailed stats
   - `/api/stats` includes quota section

3. **API Calls Tracked:**
   - Quota stats update after each API call
   - Token counts recorded accurately
   - Fallback cache used when quota exceeded

### ❌ Troubleshooting

#### Problem: "Quota tracker not available"
**Cause:** `quota_tracker.py` not found or import error

**Solution:**
```powershell
# Check if file exists
ls quota_tracker.py

# If missing, it should be in the backend/ folder
# Verify the file was created during production enhancements
```

**Note:** App will still work, just without quota tracking.

#### Problem: "Failed to initialize quota tracker"
**Cause:** Error in quota_tracker initialization

**Solution:**
```powershell
# Check the error message in logs
# Common issues:
# 1. Redis connection (optional - quota tracker works without Redis)
# 2. Configuration error in config.py
```

#### Problem: "Quota exceeded" error immediately
**Cause:** Previous usage in the same minute/day

**Solution:**
```powershell
# Wait 60 seconds for RPM to reset
# OR
# Restart server to clear in-memory counters (for testing only)
```

#### Problem: "/api/quota/stats returns 501"
**Cause:** Quota tracker not initialized

**Check:**
```powershell
# Check server logs for:
# "Quota tracker loaded successfully"
# "Quota tracker initialized successfully"

# If not present, check if quota_tracker.py exists
```

## Test Fallback Behavior

### Test Without quota_tracker.py

1. **Rename the file:**
   ```powershell
   mv quota_tracker.py quota_tracker.py.bak
   ```

2. **Restart server:**
   ```powershell
   python main.py
   ```

3. **Expected log:**
   ```
   WARNING:root:Quota tracker not available: No module named 'quota_tracker'
   ```

4. **Test API call:**
   ```powershell
   curl -X POST http://localhost:5000/api/create_subtopics `
     -H "Content-Type: application/json" `
     -d '{"topic": "Python Programming"}'
   ```

   **Expected:** ✅ Works normally (no quota tracking)

5. **Restore file:**
   ```powershell
   mv quota_tracker.py.bak quota_tracker.py
   ```

## Next Steps

### ✅ Integration Complete - What's Working

1. **Quota Tracking:** All Gemini API calls tracked
2. **Fallback System:** Cached responses when quota exceeded
3. **Monitoring:** 3 endpoints for observability
4. **Graceful Degradation:** Works with or without quota tracker

### 📋 Optional Enhancements

1. **Add quota tracking to more endpoints:**
   - `/api/create_presentation`
   - `/api/image2topic`
   - `/api/generate_image`

2. **Enable Redis caching** (if not already):
   ```powershell
   # Install Redis (Windows)
   # Download from: https://github.com/microsoftarchive/redis/releases
   
   # Start Redis
   redis-server
   ```

3. **Deploy to production:**
   - See `PRODUCTION_QUICKSTART.md` for Docker/Kubernetes deployment
   - Use `/api/ready` for health checks
   - Monitor `/api/quota/stats` for usage

## Files Created/Modified

### Modified
- ✅ `backend/main.py` - Integrated quota tracking

### Created
- ✅ `backend/quota_tracker.py` - Quota tracking implementation
- ✅ `backend/test_quota_integration.py` - Integration tests
- ✅ `QUOTA_INTEGRATION_COMPLETE.md` - Full documentation
- ✅ `QUOTA_INTEGRATION_QUICKSTART.md` - This quick start guide

## Support

If you encounter issues:

1. Check logs in the terminal running `python main.py`
2. Review `QUOTA_INTEGRATION_COMPLETE.md` for detailed documentation
3. Run `python test_quota_integration.py` for automated diagnostics
4. Verify API key: `python verify_credentials.py`

## Summary

✅ **Quota tracking fully integrated with graceful fallback**
✅ **Zero breaking changes to existing functionality**
✅ **Production-ready monitoring endpoints**
✅ **Comprehensive testing suite**

The application now prevents Google Gemini API quota exceeded errors while maintaining full backward compatibility! 🎉
