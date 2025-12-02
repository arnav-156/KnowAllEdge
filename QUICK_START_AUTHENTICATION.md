# 🚀 Quick Start Guide - Complete Authentication System

## Overview

This guide will help you get started with the complete authentication system in under 5 minutes.

---

## ✅ Prerequisites

- ✅ Python 3.8+ installed
- ✅ Node.js 16+ installed
- ✅ Backend dependencies installed (PyJWT, cryptography)
- ✅ Frontend dependencies installed (npm install)
- ✅ Master password generated and configured

---

## 🏃 Quick Start (3 Steps)

### **Step 1: Start Backend** (Terminal 1)

```powershell
cd backend
python main.py
```

**Expected output:**
```
🔐 Security initialized with encrypted secrets
🛡️ ADMIN API KEY: sk_admin_xxxxx (SAVE THIS!)
⚠️ WARNING: Save your admin API key now. It won't be shown again.
 * Running on http://127.0.0.1:5000
```

### **Step 2: Start Frontend** (Terminal 2)

```powershell
cd frontend
npm run dev
```

**Expected output:**
```
VITE v5.2.7  ready in 348 ms
➜  Local:   http://localhost:5174/
```

### **Step 3: Test Authentication**

1. Open browser: **http://localhost:5174**
2. You should see:
   - ✅ Navbar at top with logo and "Login / Register" button
   - ✅ Homepage content below

---

## 🎯 Test Complete Flow (5 Minutes)

### **Test 1: User Registration**

1. Click "🔐 Login / Register" in navbar
2. Fill registration form:
   - **User ID**: `testuser`
   - **Quota Tier**: `Free (10 req/min, 100 req/day)`
3. Click "Register"
4. ✅ Success screen appears with API key
5. Click "📋 Copy to Clipboard"
6. ✅ API key copied (e.g., `sk_free_abc123xyz`)
7. Wait 5 seconds for auto-redirect
8. ✅ Redirected to homepage

### **Test 2: Check Navbar Profile**

1. Look at top-right of navbar
2. ✅ Should see your avatar (first letter of username)
3. ✅ Should see your username
4. Click on profile button
5. ✅ Dropdown appears with:
   - Your username
   - Tier badge (🆓 free)
   - Quota limits
   - Home button
   - Logout button

### **Test 3: Protected Routes**

1. Navigate to http://localhost:5174/GraphPage
2. ✅ Page loads successfully (no redirect)
3. Click "Logout" in profile dropdown
4. Confirm logout
5. Try to navigate to http://localhost:5174/GraphPage again
6. ✅ Redirected to /auth page (authentication required)

### **Test 4: Login Flow**

1. On /auth page, click "Login" tab
2. Paste your API key from registration
3. Click "Login"
4. ✅ Redirected to homepage
5. ✅ Profile menu shows your info again

### **Test 5: Authentication Persistence**

1. While logged in, refresh page (F5)
2. ✅ Still logged in (no redirect)
3. ✅ Profile menu still shows your info
4. Close browser tab
5. Reopen http://localhost:5174
6. ✅ Still logged in (credentials persisted)

---

## 🎨 Visual Checklist

### **Homepage (Logged Out)**

```
┌─────────────────────────────────────────────────┐
│ KNOWALLEDGE    📊 Metrics    🔐 Login/Register │ ← Navbar
└─────────────────────────────────────────────────┘
│                                                 │
│     Welcome to KNOWALLEDGE.                     │
│                                                 │
│   Your intuitive landscape for learning.        │
│                                                 │
│   What do you want to learn about today?        │
│                                                 │
│   [Search box]                                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

### **Homepage (Logged In)**

```
┌─────────────────────────────────────────────────┐
│ KNOWALLEDGE    📊 Metrics    👤 testuser ▼     │ ← Navbar
└─────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────┐
                    │   👤 testuser           │
                    │   🆓 free               │
                    ├─────────────────────────┤
                    │ 📊 Your Quota Limits    │
                    │  Requests/Min: 10       │
                    │  Requests/Day: 100      │
                    ├─────────────────────────┤
                    │  🏠 Home                │
                    │  🚪 Logout              │
                    └─────────────────────────┘
```

### **Auth Page (Registration)**

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  [Purple Gradient Background]                   │
│                                                 │
│   ┌───────────────────────────────────────┐     │
│   │                                       │     │
│   │   🔐 Authentication                   │     │
│   │                                       │     │
│   │   [Register] [Login] ← Tabs          │     │
│   │                                       │     │
│   │   User ID:                            │     │
│   │   [testuser___________________]       │     │
│   │                                       │     │
│   │   Quota Tier:                         │     │
│   │   [Free ▼]                            │     │
│   │                                       │     │
│   │   [Register]                          │     │
│   │                                       │     │
│   └───────────────────────────────────────┘     │
│                                                 │
└─────────────────────────────────────────────────┘
```

### **Success Screen**

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  [Purple Gradient Background]                   │
│                                                 │
│   ┌───────────────────────────────────────┐     │
│   │                                       │     │
│   │           ✅                          │     │
│   │                                       │     │
│   │   Registration Successful!            │     │
│   │                                       │     │
│   │   Your API Key:                       │     │
│   │   ┌─────────────────────────────┐     │     │
│   │   │ sk_free_abc123xyz    [📋]  │     │     │
│   │   └─────────────────────────────┘     │     │
│   │                                       │     │
│   │   ⚠️ SAVE THIS KEY!                  │     │
│   │                                       │     │
│   │   Redirecting in 5 seconds...         │     │
│   │                                       │     │
│   │   [Go to Homepage Now]                │     │
│   │                                       │     │
│   └───────────────────────────────────────┘     │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### **Issue: Navbar not showing**

**Check:**
1. Is frontend running on correct port? (5173 or 5174)
2. Any console errors? (F12 → Console)
3. Clear cache and refresh (Ctrl+Shift+R)

**Solution:**
```powershell
# Stop frontend (Ctrl+C)
# Restart
cd frontend
npm run dev
```

### **Issue: "Cannot find module" errors**

**Solution:**
```powershell
cd frontend
npm install
npm run dev
```

### **Issue: Backend not starting**

**Check:**
1. Is Python installed? `python --version`
2. Are dependencies installed? `pip list | grep PyJWT`
3. Is .env configured?

**Solution:**
```powershell
cd backend
pip install -r requirements.txt
python main.py
```

### **Issue: Registration fails with error**

**Check:**
1. Is backend running? (http://localhost:5000)
2. Check backend terminal for errors
3. Check browser console (F12 → Console)

**Solution:**
1. Verify backend is running
2. Check if GOOGLE_API_KEY is set in .env or .secrets
3. Restart backend

### **Issue: Profile dropdown not appearing**

**Check:**
1. Are you logged in? (localStorage has credentials)
2. Check browser console for errors
3. Is AuthContext properly initialized?

**Solution:**
```javascript
// Open browser console (F12)
console.log('API Key:', localStorage.getItem('KNOWALLEDGE_api_key'));
console.log('JWT Token:', localStorage.getItem('KNOWALLEDGE_jwt_token'));
```

If empty, log in again.

---

## 📊 Current Status

### **Backend**
✅ Running on http://localhost:5000
✅ Authentication endpoints active
✅ Security headers enabled
✅ Secrets encrypted

### **Frontend**
✅ Running on http://localhost:5174
✅ Navbar with user profile
✅ Auth page for login/registration
✅ Protected routes configured
✅ Authentication state management

### **Features Working**
✅ User registration
✅ User login
✅ Protected routes
✅ Navbar profile menu
✅ Logout functionality
✅ Authentication persistence
✅ Mobile responsive design

---

## 🎯 Next Actions

### **For Testing:**
1. ✅ Register a new user
2. ✅ Test login flow
3. ✅ Test protected routes
4. ✅ Test logout
5. ✅ Test authentication persistence

### **For Development:**
- Continue building features
- Add more protected pages
- Customize UI colors/design
- Add user settings page

### **For Production:**
- Set FORCE_HTTPS=true
- Get SSL certificate
- Configure production domain
- Set up monitoring
- Deploy backend + frontend

---

## 📚 Documentation

- **Complete Implementation:** `COMPLETE_AUTH_SYSTEM_SUMMARY.md`
- **Frontend Auth:** `FRONTEND_AUTH_COMPLETE.md`
- **Navbar & Routes:** `NAVBAR_PROTECTED_ROUTES_COMPLETE.md`
- **Backend Security:** `SECURITY_IMPLEMENTATION_GUIDE.md`
- **Setup Guide:** `SECURITY_SETUP_COMPLETE.md`

---

## 🎉 Success Criteria

✅ Backend running without errors
✅ Frontend running without errors
✅ Navbar visible and functional
✅ Registration flow works
✅ Login flow works
✅ Protected routes redirect properly
✅ Profile dropdown displays correctly
✅ Logout works
✅ Authentication persists after refresh

**All criteria met? 🎉 You're ready to start using the authentication system!**

---

## 📞 Support

If you encounter issues:

1. Check browser console (F12 → Console)
2. Check backend terminal output
3. Review documentation files
4. Clear localStorage and try again
5. Restart both backend and frontend

**Status:** ✅ System fully operational and ready for use!

---

**Quick Links:**
- Frontend: http://localhost:5174
- Backend: http://localhost:5000
- Auth Page: http://localhost:5174/auth
- Metrics: http://localhost:5174/metrics (admin only)
