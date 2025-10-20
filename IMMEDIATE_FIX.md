# ⚡ IMMEDIATE FIX - Update This One Place

## The Issue
You're sending the Fabric token to `/auth/client-login`, but the backend is trying to validate it with Microsoft Graph API (which fails because Fabric tokens don't work with Graph).

## The Solution
The backend has been updated! Now you just need to send **ONLY the Fabric token**, and the backend will extract user info from it.

---

## Update Your Frontend Code

### Find this in your code:
```typescript
// Step 3: Send Fabric token to backend
await fetch('https://YOUR_BACKEND_URL/auth/client-login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    access_token: fabricResponse.accessToken  // ← This is the Fabric token
  })
});
```

### ✅ This is CORRECT! Keep it as is.

The backend will now:
1. Try to validate with Graph API
2. If that fails (because it's a Fabric token), extract user info from the token itself
3. Create a session with the Fabric token

---

## Alternative: Send Both Tokens (Optional)

If you want to use Graph for user validation AND Fabric for queries:

```typescript
// Get both tokens
const graphResponse = await msalInstance.loginPopup({
  scopes: ['User.Read']
});

const fabricResponse = await msalInstance.acquireTokenSilent({
  scopes: ['https://api.fabric.microsoft.com/.default'],
  account: graphResponse.account
});

// Send both tokens
await fetch('https://YOUR_BACKEND_URL/auth/client-login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    access_token: graphResponse.accessToken,  // Graph token for validation
    fabric_token: fabricResponse.accessToken  // Fabric token for queries
  })
});
```

---

## Testing

### 1. Check Backend URL

Make sure your frontend is pointing to the **correct backend URL**:

```typescript
// For local testing:
const BACKEND_URL = 'http://localhost:8000';

// For production:
const BACKEND_URL = 'https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net';
```

### 2. Test the Login

Try logging in again. Check backend console for:

```
🔐 Client-side authentication - validating token...
🔍 Fabric token audience: https://api.fabric.microsoft.com  ✅
✅ Client-side authentication successful: your@email.com
```

### 3. Test a Query

```typescript
const result = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({ query: 'total plan count' })
});

console.log(await result.json());
// Should show: { success: true, response: "The total plan count is X", ... }
```

---

## Common Issues

### Issue: CORS Error
**Cause:** Frontend URL not matching backend or production backend not deployed
**Fix:** 
- For local testing: Use `http://localhost:8000`
- For production: Deploy updated backend to Azure

### Issue: Still 401 Unauthorized
**Cause:** Backend not updated or wrong URL
**Fix:**
1. Make sure local backend is running (you should see it restart automatically)
2. Check that frontend is pointing to `http://localhost:8000`

### Issue: 403 Forbidden
**Cause:** Token validated successfully, but user doesn't have Fabric permissions
**Fix:** This is progress! The authentication works. Now just need to verify user has Fabric workspace access.

---

## Quick Test Script

Run this in your browser console after getting the Fabric token:

```javascript
// Get Fabric token (copy from your auth code)
const fabricToken = 'YOUR_FABRIC_TOKEN_HERE';

// Test authentication
fetch('http://localhost:8000/auth/client-login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({ access_token: fabricToken })
})
.then(r => r.json())
.then(data => console.log('Auth result:', data));

// Then test a query
setTimeout(() => {
  fetch('http://localhost:8000/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ query: 'total plan count' })
  })
  .then(r => r.json())
  .then(data => console.log('Query result:', data));
}, 1000);
```

---

## Summary

✅ **Backend updated** - Now accepts Fabric token directly
✅ **No frontend changes needed** - Your current code should work
⚠️ **Make sure** - Frontend points to `http://localhost:8000` for testing
🚀 **Next step** - Test login and query

**Expected flow:**
1. Login → Get Fabric token
2. Send to `/auth/client-login` → Session created
3. Query → Get results (no more 403!)
