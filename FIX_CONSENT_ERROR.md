# 🔧 Fix for "consent_required" Error (AADSTS65001)

## The Error

```json
{
  "error": "invalid_grant",
  "error_description": "AADSTS65001: The user or administrator has not consented to use the application with ID '3503e363-86d6-4b02-807d-489886873632' named 'fabric-data-agent-service'",
  "suberror": "consent_required"
}
```

## What This Means

Azure is saying: **"The user has never given permission to access Fabric API"**

This happens when:
1. First time requesting Fabric API scope
2. Admin consent is required but not granted
3. User dismissed the consent popup

---

## The Solution: Handle Consent Popup

Your frontend needs to **catch the error** and **show a popup** for consent.

### Update Your Frontend Authentication Code

Find where you call `acquireTokenSilent()` and wrap it with error handling:

```typescript
async login() {
  try {
    // Step 1: Login with Graph scope
    console.log('🔐 Step 1: Authenticating with Microsoft...');
    const graphResponse = await this.msalInstance.loginPopup({
      scopes: ['User.Read']
    });
    console.log('✅ Graph authentication successful!');

    // Step 2: Get Fabric token
    console.log('🔐 Step 2: Acquiring Fabric API token...');
    let fabricToken;
    
    try {
      // Try silent first
      const fabricResponse = await this.msalInstance.acquireTokenSilent({
        scopes: ['https://api.fabric.microsoft.com/.default'],
        account: graphResponse.account
      });
      fabricToken = fabricResponse.accessToken;
      console.log('✅ Fabric token acquired silently');
      
    } catch (silentError: any) {
      // Handle consent_required, interaction_required, etc.
      if (silentError.errorCode === 'consent_required' || 
          silentError.errorCode === 'interaction_required' ||
          silentError.errorCode === 'login_required') {
        
        console.log('⚠️ Interaction required, using popup for Fabric token...');
        
        // Show popup for consent
        const fabricResponse = await this.msalInstance.acquireTokenPopup({
          scopes: ['https://api.fabric.microsoft.com/.default'],
          account: graphResponse.account
        });
        
        fabricToken = fabricResponse.accessToken;
        console.log('✅ Fabric token acquired via popup');
        
      } else {
        // Other error
        console.error('❌ Failed to get Fabric token:', silentError);
        throw silentError;
      }
    }

    // Step 3: Send Fabric token to backend
    console.log('🔐 Step 3: Sending token to backend...');
    await this.authenticateWithBackend(fabricToken);
    console.log('✅ Backend authentication successful!');
    
  } catch (error) {
    console.error('❌ Login failed:', error);
    throw error;
  }
}

private async authenticateWithBackend(fabricToken: string): Promise<void> {
  const response = await fetch('http://localhost:8000/auth/client-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      access_token: fabricToken
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Backend authentication failed: ${JSON.stringify(error)}`);
  }

  console.log('✅ Backend authentication successful');
}
```

---

## Key Changes Explained

### Before (Wrong - Always Silent)
```typescript
// This FAILS on first login because user hasn't consented
const fabricResponse = await this.msalInstance.acquireTokenSilent({
  scopes: ['https://api.fabric.microsoft.com/.default'],
  account: graphResponse.account
});
```

### After (Correct - Try Silent, Fallback to Popup)
```typescript
try {
  // Try silent first (works if user already consented)
  const fabricResponse = await this.msalInstance.acquireTokenSilent({...});
} catch (error) {
  if (error.errorCode === 'consent_required') {
    // Show popup for consent (first time or expired consent)
    const fabricResponse = await this.msalInstance.acquireTokenPopup({...});
  }
}
```

---

## Alternative: Always Use Popup (Simpler)

If you want to keep it simple, just use popup every time:

```typescript
async login() {
  try {
    // Step 1: Graph authentication
    const graphResponse = await this.msalInstance.loginPopup({
      scopes: ['User.Read']
    });

    // Step 2: Fabric token (always use popup - simpler)
    const fabricResponse = await this.msalInstance.acquireTokenPopup({
      scopes: ['https://api.fabric.microsoft.com/.default'],
      account: graphResponse.account,
      prompt: 'consent'  // Force consent screen
    });

    // Step 3: Send to backend
    await this.authenticateWithBackend(fabricResponse.accessToken);
    
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}
```

**Pros:** Simpler, always shows consent  
**Cons:** Extra popup even if user already consented

---

## Why This Error Happens

### Your Frontend Code Currently:

1. ✅ Gets Graph token with popup (works)
2. ❌ Tries to get Fabric token **silently** (fails because no prior consent)
3. ❌ Doesn't handle the `consent_required` error
4. ❌ Never shows the Fabric consent popup

### What Should Happen:

1. ✅ Gets Graph token with popup
2. ✅ Tries to get Fabric token silently
3. ✅ Catches `consent_required` error
4. ✅ Shows Fabric consent popup
5. ✅ User accepts → gets Fabric token
6. ✅ Sends to backend

---

## Expected User Experience

### First Login:
1. Click "Sign In with Microsoft"
2. **Popup 1:** Microsoft Graph consent (User.Read) → User accepts
3. **Popup 2:** Fabric API consent (Fabric permissions) → User accepts
4. Backend session created
5. User can query! ✅

### Subsequent Logins:
1. Click "Sign In with Microsoft"
2. **Popup 1:** Microsoft Graph (quick redirect, no consent needed)
3. **No Popup 2:** Fabric token acquired silently ✅
4. Backend session created
5. User can query! ✅

---

## Testing Steps

### 1. Update Your Code

Add the error handling for `consent_required` (code above).

### 2. Clear Browser Cache

```javascript
// In browser console (F12)
localStorage.clear();
sessionStorage.clear();

// Or use incognito/private mode
```

This ensures you're testing as a "first-time user".

### 3. Try Login

You should see:
1. Graph consent popup
2. **Fabric consent popup** (this is new!)
3. Both accepted
4. Success! ✅

### 4. Verify in Console

You should see:
```
✅ Graph authentication successful!
⚠️ Interaction required, using popup for Fabric token...
✅ Fabric token acquired via popup
✅ Backend authentication successful!
```

---

## Common Mistakes to Avoid

### ❌ Wrong: Ignoring the Error
```typescript
try {
  const token = await acquireTokenSilent({...});
} catch (error) {
  console.error(error);  // Just logs it, doesn't fix it
}
```

### ✅ Right: Handling with Popup
```typescript
try {
  const token = await acquireTokenSilent({...});
} catch (error) {
  if (error.errorCode === 'consent_required') {
    const token = await acquireTokenPopup({...});  // Shows consent popup
  }
}
```

---

## Admin Consent (Alternative Solution)

If you want to **skip the popup entirely**, have an admin pre-consent for all users:

### Step 1: Get Admin Consent URL

```
https://login.microsoftonline.com/4d4eca3f-b031-47f1-8932-59112bf47e6b/adminconsent
?client_id=YOUR_APP_CLIENT_ID
&redirect_uri=https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net
```

### Step 2: Admin Opens URL and Accepts

This grants consent for **all users** in the tenant.

### Step 3: Users Can Login Without Popup

After admin consent, `acquireTokenSilent()` will work for all users.

---

## Summary

**The Fix:**
1. Catch `consent_required` error
2. Show popup with `acquireTokenPopup()`
3. User accepts consent
4. Get Fabric token
5. Send to backend

**Update your login code to include the try-catch with popup fallback!**

Then try logging in again - it should work! 🚀

---

## Quick Copy-Paste Solution

Here's the complete fixed login function:

```typescript
async login() {
  try {
    // Step 1: Graph login
    const graphResponse = await this.msalInstance.loginPopup({
      scopes: ['User.Read']
    });
    console.log('✅ Graph authenticated');

    // Step 2: Fabric token with fallback
    let fabricToken;
    try {
      // Try silent
      const silentResponse = await this.msalInstance.acquireTokenSilent({
        scopes: ['https://api.fabric.microsoft.com/.default'],
        account: graphResponse.account
      });
      fabricToken = silentResponse.accessToken;
      console.log('✅ Fabric token (silent)');
    } catch (err: any) {
      // Fallback to popup
      if (err.errorCode === 'consent_required' || 
          err.errorCode === 'interaction_required') {
        const popupResponse = await this.msalInstance.acquireTokenPopup({
          scopes: ['https://api.fabric.microsoft.com/.default'],
          account: graphResponse.account
        });
        fabricToken = popupResponse.accessToken;
        console.log('✅ Fabric token (popup)');
      } else {
        throw err;
      }
    }

    // Step 3: Backend auth
    const response = await fetch('http://localhost:8000/auth/client-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ access_token: fabricToken })
    });

    if (!response.ok) throw new Error('Backend auth failed');
    
    console.log('✅ Login complete!');
    return await response.json();
    
  } catch (error) {
    console.error('❌ Login failed:', error);
    throw error;
  }
}
```

**Copy this, update your code, and try again!** 🎉
