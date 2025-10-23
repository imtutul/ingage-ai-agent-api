# Troubleshooting Guide: "Trouble Connecting to Server" Error

## Problem
New users see the error message: **"I'm sorry, I'm having trouble connecting to the server right now. Please try again later."**

## Root Cause
This error message comes from the **frontend application** when it cannot successfully communicate with the backend API. It's a generic error that masks the actual underlying issue.

## Common Causes & Solutions

### 1. ❌ **Authentication Not Set Up (Most Common)**

**Symptoms:**
- New users see error immediately when trying to query
- No sign-in button was clicked
- No authentication flow was triggered

**Solution:**
Ensure users complete the authentication flow:

1. **Frontend must implement sign-in flow:**
   - Add a "Sign In" button
   - Call `/auth/client-login` endpoint with tokens
   - Store session cookie returned by backend

2. **Check authentication status:**
   ```bash
   curl http://localhost:8000/auth/status \
     -H "Cookie: fabric_session_id=YOUR_SESSION_ID"
   ```

3. **Expected Flow:**
   ```
   User clicks "Sign In" 
   → Frontend uses MSAL.js to get tokens
   → Frontend calls /auth/client-login with tokens
   → Backend creates session and returns cookie
   → User can now make queries
   ```

---

### 2. 🍪 **Missing Session Cookie**

**Symptoms:**
- User authenticated but queries fail
- Backend logs show: "⚠️ No session cookie found"

**Why it happens:**
- Cookie not being sent with requests
- CORS not configured properly
- Frontend not including credentials

**Solution:**

**Backend (Already Configured):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net"
    ],
    allow_credentials=True,  # ← Critical for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Frontend Must:**
```typescript
// Fetch API
fetch('http://api.example.com/query', {
  credentials: 'include',  // ← Critical - must include this!
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ query: "..." })
})

// Axios
axios.post('http://api.example.com/query', data, {
  withCredentials: true  // ← Critical - must include this!
})
```

---

### 3. 🚫 **Token Permission Issues**

**Symptoms:**
- User authenticates successfully
- Queries return 403 Forbidden or permission errors
- Backend logs show token validation failures

**Why it happens:**
- User's Azure AD account doesn't have access to Fabric workspace
- Token lacks required scopes
- Service principal lacks permissions

**Solution:**

**Check User Permissions:**
1. Go to [Microsoft Fabric Portal](https://app.fabric.microsoft.com)
2. Navigate to your workspace: `d09dbe6d-b3f5-4188-a375-482e01aa1213`
3. Go to **Settings** → **Manage access**
4. Verify the user has at least **Viewer** role (Contributor/Admin for write operations)

**Required Token Scopes:**
The token must have these scopes:
- `https://api.fabric.microsoft.com/Workspace.Read.All`
- `https://api.fabric.microsoft.com/Dataset.Read.All`

**Frontend MSAL Configuration:**
```typescript
const msalConfig = {
  auth: {
    clientId: "YOUR_CLIENT_ID",
    authority: "https://login.microsoftonline.com/YOUR_TENANT_ID"
  }
};

const loginRequest = {
  scopes: [
    "https://api.fabric.microsoft.com/.default",  // Fabric token
    "User.Read"  // Graph token for user info
  ]
};
```

---

### 4. 🌐 **CORS Configuration Issues**

**Symptoms:**
- Browser console shows CORS errors
- Preflight OPTIONS requests fail
- Error: "Access-Control-Allow-Origin header is missing"

**Solution:**

**Add your frontend URL to CORS whitelist:**

Edit `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://your-frontend-domain.azurewebsites.net",  # Add your domain
        # Add any other frontend domains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**For development, you can temporarily use:**
```python
allow_origins=["*"]  # ⚠️ Only for development! Never in production!
```

---

### 5. ⏰ **Session Expired**

**Symptoms:**
- User was able to query before
- Now gets authentication errors
- Backend logs: "⚠️ Session expired or invalid"

**Why it happens:**
- Sessions expire after 24 hours (default)
- Server restarted (sessions stored in memory)

**Solution:**

**User needs to re-authenticate:**
- Frontend should detect 401 errors
- Automatically redirect to sign-in flow
- Clear old session cookie

**Frontend Implementation:**
```typescript
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Clear session and redirect to login
      clearSession();
      redirectToLogin();
    }
    return Promise.reject(error);
  }
);
```

---

### 6. 🔧 **Service Not Initialized**

**Symptoms:**
- All users get error
- Backend logs: "❌ Fabric client not initialized"

**Solution:**

**Check Backend Startup:**
```bash
# View server logs
python start_server.py

# Expected output:
✅ Fabric Data Agent Client initialized successfully
🔐 Authentication will occur when first user makes a request
```

**Verify Environment Variables:**
```bash
# Check .env file
cat .env

# Required variables:
DATA_AGENT_URL=https://...
TENANT_ID=...
CLIENT_ID=...
CLIENT_SECRET=...
```

---

## Diagnostic Commands

### Check Backend Health
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "fabric_client_initialized": true,
  "tenant_id": "abc123..."
}
```

### Test Authentication
```bash
# Get auth status (should fail without cookie)
curl http://localhost:8000/auth/status

# Expected: No session found
```

### Check Backend Logs
```bash
# Start server with verbose logging
python start_server.py

# Watch for these messages:
# ⚠️ No session cookie found
# ⚠️ Session expired or invalid
# ❌ Query failed: [specific error]
```

### Frontend Network Tab
1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Try to make a query
4. Look for:
   - `/query` request
   - Status code (401, 403, 500?)
   - Response body (actual error message)
   - Request headers (Cookie sent?)

---

## Quick Fixes by Error Type

| Backend Log Message | User Action | Developer Action |
|---------------------|-------------|------------------|
| "⚠️ No session cookie found" | Sign in again | Check frontend includes credentials |
| "⚠️ Session expired" | Sign in again | Implement session refresh |
| "❌ Fabric client not initialized" | Wait and retry | Check environment variables |
| "403" or "forbidden" | Contact admin | Add user to Fabric workspace |
| "401" or "unauthorized" | Sign in again | Check token scopes |

---

## Recommended Improvements

### 1. **Better Error Messages in Frontend**

Instead of generic "trouble connecting":

```typescript
try {
  const response = await fetch('/query', {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify({ query })
  });
  
  const data = await response.json();
  
  if (!data.success) {
    // Backend now returns user-friendly messages
    displayError(data.response);  // "Please sign in to continue..."
  }
} catch (error) {
  if (error.status === 401) {
    displayError("Please sign in to continue");
  } else if (error.status === 403) {
    displayError("You don't have permission. Contact your administrator.");
  } else {
    displayError("Unable to connect. Please try again later.");
  }
}
```

### 2. **Automatic Session Refresh**

```typescript
// Check session before each query
const checkSession = async () => {
  const response = await fetch('/auth/status', { credentials: 'include' });
  if (!response.ok || !(await response.json()).authenticated) {
    // Trigger re-authentication
    await reauthenticate();
  }
};
```

### 3. **User Onboarding Flow**

1. First-time user lands on page
2. Show welcome message with "Sign In" button
3. After sign-in, show tutorial
4. Guide them through first query

### 4. **Admin Dashboard**

Create an admin page showing:
- Connected users
- Active sessions
- Failed authentication attempts
- Permission issues

---

## Testing Checklist

- [ ] New user clicks "Sign In" button
- [ ] MSAL authentication flow completes
- [ ] Frontend receives tokens
- [ ] Frontend calls `/auth/client-login` with tokens
- [ ] Backend returns session cookie
- [ ] Frontend includes cookie in subsequent requests
- [ ] User can make queries successfully
- [ ] Error messages are clear and actionable
- [ ] Session expires after 24 hours
- [ ] Re-authentication works smoothly

---

## Still Having Issues?

1. **Check Backend Logs:**
   ```bash
   tail -f server.log  # or wherever logs are
   ```

2. **Enable Debug Mode:**
   ```python
   # In main.py
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Test with Diagnostic Scripts:**
   ```bash
   python diagnose_permissions.py
   python verify_data_access.py
   ```

4. **Contact Support:**
   - Include backend logs
   - Include browser console errors
   - Include network tab screenshots
   - Mention user's email/UPN

---

## Summary

The "trouble connecting to server" error is almost always due to **authentication not being set up properly**. The fixes in this commit now return user-friendly error messages instead of generic HTTP exceptions, which will help users understand what they need to do (sign in, re-authenticate, contact admin, etc.).

**Key Changes Made:**
- ✅ Return user-friendly error messages instead of HTTP exceptions
- ✅ Better error handling with specific guidance
- ✅ Detailed logging for troubleshooting
- ✅ This troubleshooting guide
