# 🚀 Quick Fix for 403 Error

## The Problem
Your token only has `User.Read` scope (Microsoft Graph).
You need `https://api.fabric.microsoft.com/.default` scope.

---

## 5-Minute Fix

### Step 1: Update Your Login Code

**Find this in your frontend:**
```typescript
// Current (WRONG)
msalInstance.loginPopup({
  scopes: ['User.Read']
});
```

**Replace with:**
```typescript
// Step 1: Login with Graph
const graphResponse = await msalInstance.loginPopup({
  scopes: ['User.Read']
});

// Step 2: Get Fabric token
const fabricResponse = await msalInstance.acquireTokenSilent({
  scopes: ['https://api.fabric.microsoft.com/.default'],
  account: graphResponse.account
});

// Step 3: Send Fabric token to backend
await fetch('https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net/auth/client-login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    access_token: fabricResponse.accessToken  // ← Fabric token, not Graph token!
  })
});
```

### Step 2: Update All API Calls

Make sure EVERY fetch to your backend includes:
```typescript
credentials: 'include'  // ← This sends the session cookie!
```

Example:
```typescript
fetch('https://YOUR_BACKEND_URL/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',  // ← IMPORTANT!
  body: JSON.stringify({ query: 'total plan count' })
});
```

---

## What This Does

1. **First token** (Graph) - Validates you're a real Microsoft user
2. **Second token** (Fabric) - Gives permission to access Fabric API
3. **Backend gets Fabric token** - Uses it to query Data Agent on your behalf
4. **Session cookie** - Remembers you're logged in

---

## Testing

After updating, try logging in again. Check browser console for:
```
🔐 Step 1: Authenticating with Microsoft...
✅ Graph authentication successful
🔐 Step 2: Getting Fabric API token...
✅ Fabric token acquired
```

Then check your backend console (where server is running) for:
```
🔍 Token audience: https://api.fabric.microsoft.com  ✅
🔍 Token scopes: ...  ✅
```

If audience is `https://graph.microsoft.com` ❌ - You're sending the wrong token!

---

## Still Not Working?

### Error: "consent_required"
**Fix:** Use popup instead of silent:
```typescript
const fabricResponse = await msalInstance.acquireTokenPopup({
  scopes: ['https://api.fabric.microsoft.com/.default']
});
```

### Error: "Invalid token" or "Session expired"
**Fix:** Make sure you're sending the **Fabric token**, not the Graph token!

### Error: Still 403
**Cause:** Check backend logs - if token audience is correct, then it's a permission issue in Fabric.
**Fix:** Make sure user `ahaque@insightintechnology.com` has access to the AI Skill.

---

## Complete Working Example

```typescript
// auth.service.ts (or similar)

export class AuthService {
  private msalInstance = new PublicClientApplication({
    auth: {
      clientId: 'YOUR_CLIENT_ID',
      authority: 'https://login.microsoftonline.com/4d4eca3f-b031-47f1-8932-59112bf47e6b'
    }
  });

  async login() {
    // Get Graph token
    const graphResponse = await this.msalInstance.loginPopup({
      scopes: ['User.Read']
    });

    // Get Fabric token (try silent first, then popup)
    let fabricToken;
    try {
      const fabricResponse = await this.msalInstance.acquireTokenSilent({
        scopes: ['https://api.fabric.microsoft.com/.default'],
        account: graphResponse.account
      });
      fabricToken = fabricResponse.accessToken;
    } catch (error) {
      // If silent fails, use popup
      const fabricResponse = await this.msalInstance.acquireTokenPopup({
        scopes: ['https://api.fabric.microsoft.com/.default']
      });
      fabricToken = fabricResponse.accessToken;
    }

    // Send to backend
    const response = await fetch(
      'https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net/auth/client-login',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ access_token: fabricToken })
      }
    );

    if (!response.ok) {
      throw new Error('Backend authentication failed');
    }

    console.log('✅ Login successful!');
  }

  async query(question: string) {
    const response = await fetch(
      'https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net/query',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ query: question })
      }
    );

    if (!response.ok) {
      throw new Error('Query failed');
    }

    return await response.json();
  }
}
```

---

## Next Steps

1. ✅ Update frontend login code (above)
2. ✅ Test login - should see no errors
3. ✅ Test query - should get real data instead of 403
4. ✅ Check backend console logs to verify token is correct

**Time estimate:** 5-10 minutes

Need detailed instructions? See `FRONTEND_AUTH_FIX.md`
