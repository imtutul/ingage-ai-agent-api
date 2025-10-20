# 🔧 Quick Fix for 400 Bad Request Error

## The Problem

Looking at your screenshot, you're seeing:
1. ✅ Microsoft consent screen appears (good!)
2. ✅ "Graph authentication successful!"
3. ✅ "Step 2: Acquiring Fabric API token..."
4. ❌ **400 (Bad Request)** when sending token to backend
5. ❌ CORS errors in console

## Root Cause

Your frontend is trying to send the token to the **production backend URL**, but you need to:
- Either point to **local backend** (`http://localhost:8000`)
- Or **deploy the updated backend** to production

---

## Solution 1: Test Locally (QUICKEST - 2 minutes)

### Update Your Frontend Config

Find where your frontend defines the API URL (likely in `environment.ts`, `config.ts`, or similar):

```typescript
// Change from:
const API_URL = 'https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net';

// To:
const API_URL = 'http://localhost:8000';
```

### Restart Your Frontend

```bash
# If Angular:
ng serve

# If React:
npm start

# If other:
npm run dev
```

### Try Login Again

Should work now! ✅

---

## Solution 2: Deploy to Production (RECOMMENDED - 20 minutes)

Your local backend has the fixes, but production doesn't. Deploy the updated code:

### Step 1: Check if Backend is Running Locally

Your terminal shows: `✅ Uvicorn running on http://0.0.0.0:8000`

This is **local only**. Production needs the update.

### Step 2: Deploy to Azure

```bash
cd "E:\Drive D\Personnal Source Code\Ingage AI Agent\ingage-ai-agent-api"

# Commit changes
git add .
git commit -m "Fix client-side authentication with Fabric token"
git push

# Deploy (if you have Azure CLI)
az webapp up --name ingage-ai-agent-api-c6f9htcfd3baa2b4
```

### Step 3: Verify Deployment

```bash
# Check health
curl https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net/health
```

### Step 4: Test Again from Frontend

Login should now work! ✅

---

## Solution 3: Test with Console (DEBUG - 5 minutes)

If you want to verify the token is correct before fixing the URL:

### Open Browser Console

Press **F12** → **Console** tab

### Get the Fabric Token

After you click "Accept" on the consent screen, your frontend should have the token. Find it in your code where it says:

```typescript
console.log("Got Fabric API access token from MSAL");
```

The token should be in the variable (e.g., `fabricResponse.accessToken`).

### Test Manually

```javascript
// Replace with your actual token
const fabricToken = 'YOUR_FABRIC_TOKEN_HERE';

// Test against LOCAL backend
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
.then(data => console.log('Result:', data))
.catch(err => console.error('Error:', err));
```

If this works (returns 200 OK), then the issue is just the frontend URL configuration!

---

## What the Errors Mean

### "Cross-Origin-Opener-Policy policy would block the window.closed call"
- **Not critical** - This is a warning from Microsoft's consent popup
- Happens when using `popup` login flow
- Doesn't prevent authentication

### "400 (Bad Request)"
- **Critical** - The backend rejected the request
- Causes:
  1. Wrong URL (production vs local)
  2. Token format issue
  3. CORS not configured

### "CORS error"
- **Could be critical** - Backend might not allow your frontend origin
- But your local backend should already have CORS configured for `localhost:4200`

---

## Expected Flow (What Should Happen)

1. **User clicks "Sign In with Microsoft"**
2. **MSAL popup opens** → User sees consent screen
3. **User accepts permissions**
4. **Frontend gets Fabric token**
5. **Frontend sends token to backend** via POST `/auth/client-login`
6. **Backend validates token** and creates session
7. **Backend returns 200 OK** with user info
8. **Frontend stores session cookie**
9. **User can now query!**

Currently, you're stuck at step 5-6.

---

## Quick Diagnostic

Run this in your backend terminal to see if it's receiving requests:

```bash
# Your backend is running, so just watch for POST requests
# When you try to login, you should see:
# INFO: 127.0.0.1:XXXXX - "POST /auth/client-login HTTP/1.1" 200 OK
```

If you **don't see any POST requests**, it confirms your frontend is pointing to the wrong URL.

If you **see POST requests with errors**, the issue is with the backend code.

---

## Recommended Action

**For immediate testing:**
1. Update frontend API URL to `http://localhost:8000`
2. Restart frontend
3. Try login again

**For production deployment:**
1. Deploy updated `main.py` to Azure
2. Keep frontend pointing to production URL
3. Test

---

## Still Not Working?

Share:
1. Your frontend authentication code (where you call `/auth/client-login`)
2. The exact error message from backend logs
3. The full URL your frontend is trying to reach

I'll help you debug further!
