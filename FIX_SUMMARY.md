# 🎯 How to Fix Your 401 Unauthorized Error

## Problem Summary
Your frontend is correctly getting the Fabric token, but when you send it to the backend, you get **401 Unauthorized** because:
1. You're testing against **production backend** URL, but your **local backend** is running
2. The backend was trying to validate the Fabric token with Graph API (which doesn't work)

## ✅ What I Fixed (Backend)
The backend now:
- Accepts Fabric token directly
- Extracts user info from the token itself (no Graph API needed)
- Stores the Fabric token for queries

## 🔧 What You Need to Fix (Frontend)

### Option 1: Test Locally (QUICK - Recommended for now)

Change your backend URL in the frontend to point to local:

```typescript
// In your frontend config or auth service:
const API_BASE_URL = 'http://localhost:8000';  // ← Change to this

// Was probably:
// const API_BASE_URL = 'https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net';
```

### Option 2: Deploy to Production

If you want to test against production:
1. Deploy the updated `main.py` to Azure
2. Keep frontend URL as is
3. Test

---

## Testing Steps

### 1. Update Frontend URL
```typescript
// auth.service.ts or similar
const API_URL = 'http://localhost:8000';  // Local testing
```

### 2. Try Login Again
Click "Sign In with Microsoft" in your app.

### 3. Check Console
You should see:
```
✅ Fabric token acquired via popup
✅ Sending token to backend...
✅ Backend authentication successful
```

### 4. Try a Query
Ask: "total plan count"

Should get real data instead of 403!

---

## Quick Test (Browser Console)

After you get the Fabric token, run this in browser console:

```javascript
// Replace YOUR_FABRIC_TOKEN with the actual token from your auth flow
const fabricToken = 'YOUR_FABRIC_TOKEN';

// Test auth
fetch('http://localhost:8000/auth/client-login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({ access_token: fabricToken })
})
.then(r => {
  console.log('Status:', r.status);
  return r.json();
})
.then(data => console.log('Result:', data));
```

Expected output:
```json
{
  "success": true,
  "message": "Client-side authentication successful",
  "user": {
    "email": "ahaque@insightintechnology.com",
    ...
  }
}
```

---

## What Should Happen

### Before Fix:
```
POST /auth/client-login → 401 Unauthorized ❌
```

### After Fix:
```
POST /auth/client-login → 200 OK ✅
GET /auth/status → 200 OK (user authenticated) ✅
POST /query → 200 OK (real data returned) ✅
```

---

## If Still Not Working

### Check 1: Backend Running?
Look for this in terminal:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Check 2: Frontend URL Correct?
Should be `http://localhost:8000` (with cookies enabled)

### Check 3: CORS Error?
If you see CORS errors, the frontend URL might not be in the allowed origins. Check that your frontend is running on `localhost:4200` or add your URL to `main.py` CORS config.

---

## Summary

**What was wrong:**
- Frontend sends Fabric token ✅
- Backend tries to validate with Graph API ❌
- Validation fails → 401 error ❌

**What's fixed:**
- Frontend sends Fabric token ✅
- Backend extracts user from Fabric token ✅
- Creates session with Fabric token ✅
- Queries work! ✅

**What you need to do:**
1. Update frontend to use `http://localhost:8000`
2. Try login again
3. Test a query

**Time: 2 minutes**

---

For detailed instructions, see:
- `IMMEDIATE_FIX.md` - Detailed fix guide
- `QUICK_FIX.md` - Original guide (still useful)
- `FRONTEND_AUTH_FIX.md` - Complete reference
