# Frontend Authentication Fix Guide

## Problem
Getting 403 Forbidden error when querying Fabric Data Agent because the access token doesn't have the required Fabric API permissions.

## Root Cause
Frontend is requesting only `User.Read` scope, which gives access to Microsoft Graph but NOT to Fabric API.

## Solution
Request TWO separate tokens:
1. **Graph Token** - For user authentication/validation
2. **Fabric Token** - For Fabric API queries

---

## Implementation Guide

### Option A: Two-Token Approach (RECOMMENDED)

This approach gets separate tokens for Graph and Fabric APIs.

#### 1. Update MSAL Configuration

```typescript
// auth-config.ts or similar
import { Configuration, PopupRequest } from '@azure/msal-browser';

export const msalConfig: Configuration = {
  auth: {
    clientId: 'YOUR_CLIENT_ID',  // From Azure AD App Registration
    authority: 'https://login.microsoftonline.com/4d4eca3f-b031-47f1-8932-59112bf47e6b',
    redirectUri: window.location.origin,  // or specific URL
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  }
};

// Request for Microsoft Graph (user validation)
export const graphLoginRequest: PopupRequest = {
  scopes: ['User.Read']
};

// Request for Fabric API (data queries)
export const fabricTokenRequest: PopupRequest = {
  scopes: ['https://api.fabric.microsoft.com/.default']
};
```

#### 2. Update Login Flow

**Angular Example:**

```typescript
// auth.service.ts
import { Injectable } from '@angular/core';
import { MsalService } from '@azure/msal-angular';
import { graphLoginRequest, fabricTokenRequest } from './auth-config';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private fabricToken: string | null = null;

  constructor(private msalService: MsalService) {}

  async login(): Promise<void> {
    try {
      // Step 1: Login with Graph scope
      console.log('🔐 Step 1: Authenticating with Microsoft...');
      const graphResponse = await this.msalService.instance.loginPopup(graphLoginRequest);
      console.log('✅ Graph authentication successful');

      // Step 2: Get Fabric token silently
      console.log('🔐 Step 2: Getting Fabric API token...');
      const fabricResponse = await this.msalService.instance.acquireTokenSilent({
        ...fabricTokenRequest,
        account: graphResponse.account
      });
      
      this.fabricToken = fabricResponse.accessToken;
      console.log('✅ Fabric token acquired');

      // Step 3: Send Fabric token to backend
      await this.authenticateWithBackend(this.fabricToken);
      
    } catch (error) {
      console.error('❌ Login failed:', error);
      
      // If silent token acquisition fails, try popup
      if (error.errorCode === 'consent_required' || 
          error.errorCode === 'interaction_required') {
        console.log('🔐 Requesting Fabric token via popup...');
        const fabricResponse = await this.msalService.instance.acquireTokenPopup(fabricTokenRequest);
        this.fabricToken = fabricResponse.accessToken;
        await this.authenticateWithBackend(this.fabricToken);
      } else {
        throw error;
      }
    }
  }

  private async authenticateWithBackend(fabricToken: string): Promise<void> {
    const response = await fetch('https://YOUR_BACKEND_URL/auth/client-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',  // Important! This sends cookies
      body: JSON.stringify({
        access_token: fabricToken
      })
    });

    if (!response.ok) {
      throw new Error(`Backend authentication failed: ${response.statusText}`);
    }

    console.log('✅ Backend authentication successful');
  }

  async query(question: string): Promise<any> {
    const response = await fetch('https://YOUR_BACKEND_URL/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',  // Important! This sends session cookie
      body: JSON.stringify({
        query: question
      })
    });

    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async logout(): Promise<void> {
    this.fabricToken = null;
    await this.msalService.instance.logoutPopup();
  }
}
```

**React Example:**

```typescript
// useAuth.ts
import { useMsal } from '@azure/msal-react';
import { useState } from 'react';
import { graphLoginRequest, fabricTokenRequest } from './auth-config';

export const useAuth = () => {
  const { instance } = useMsal();
  const [fabricToken, setFabricToken] = useState<string | null>(null);

  const login = async () => {
    try {
      // Step 1: Login with Graph scope
      console.log('🔐 Step 1: Authenticating with Microsoft...');
      const graphResponse = await instance.loginPopup(graphLoginRequest);
      console.log('✅ Graph authentication successful');

      // Step 2: Get Fabric token
      console.log('🔐 Step 2: Getting Fabric API token...');
      try {
        const fabricResponse = await instance.acquireTokenSilent({
          ...fabricTokenRequest,
          account: graphResponse.account
        });
        setFabricToken(fabricResponse.accessToken);
        await authenticateWithBackend(fabricResponse.accessToken);
      } catch (error: any) {
        if (error.errorCode === 'consent_required' || 
            error.errorCode === 'interaction_required') {
          const fabricResponse = await instance.acquireTokenPopup(fabricTokenRequest);
          setFabricToken(fabricResponse.accessToken);
          await authenticateWithBackend(fabricResponse.accessToken);
        } else {
          throw error;
        }
      }
    } catch (error) {
      console.error('❌ Login failed:', error);
      throw error;
    }
  };

  const authenticateWithBackend = async (token: string) => {
    const response = await fetch('https://YOUR_BACKEND_URL/auth/client-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        access_token: token
      })
    });

    if (!response.ok) {
      throw new Error(`Backend authentication failed: ${response.statusText}`);
    }
  };

  const query = async (question: string) => {
    const response = await fetch('https://YOUR_BACKEND_URL/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({ query: question })
    });

    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }

    return await response.json();
  };

  return { login, query };
};
```

**Vue Example:**

```typescript
// authService.ts
import { PublicClientApplication } from '@azure/msal-browser';
import { msalConfig, graphLoginRequest, fabricTokenRequest } from './auth-config';

const msalInstance = new PublicClientApplication(msalConfig);

export const authService = {
  fabricToken: null as string | null,

  async login() {
    try {
      // Step 1: Login with Graph scope
      console.log('🔐 Step 1: Authenticating with Microsoft...');
      const graphResponse = await msalInstance.loginPopup(graphLoginRequest);
      console.log('✅ Graph authentication successful');

      // Step 2: Get Fabric token
      console.log('🔐 Step 2: Getting Fabric API token...');
      try {
        const fabricResponse = await msalInstance.acquireTokenSilent({
          ...fabricTokenRequest,
          account: graphResponse.account
        });
        this.fabricToken = fabricResponse.accessToken;
        await this.authenticateWithBackend(this.fabricToken);
      } catch (error: any) {
        if (error.errorCode === 'consent_required' || 
            error.errorCode === 'interaction_required') {
          const fabricResponse = await msalInstance.acquireTokenPopup(fabricTokenRequest);
          this.fabricToken = fabricResponse.accessToken;
          await this.authenticateWithBackend(this.fabricToken);
        } else {
          throw error;
        }
      }
    } catch (error) {
      console.error('❌ Login failed:', error);
      throw error;
    }
  },

  async authenticateWithBackend(token: string) {
    const response = await fetch('https://YOUR_BACKEND_URL/auth/client-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        access_token: token
      })
    });

    if (!response.ok) {
      throw new Error(`Backend authentication failed: ${response.statusText}`);
    }
  },

  async query(question: string) {
    const response = await fetch('https://YOUR_BACKEND_URL/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({ query: question })
    });

    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }

    return await response.json();
  }
};
```

---

### Option B: Single Fabric Token Approach (SIMPLER)

If you only care about Fabric API access, you can skip Graph validation and use only the Fabric token.

#### 1. Backend Change Required

Update `main.py` to skip Graph validation:

```python
@app.post("/auth/client-login", response_model=AuthResponse)
async def client_login(auth_request: ClientAuthRequest, response: Response, background_tasks: BackgroundTasks):
    """Accept Fabric API token directly"""
    try:
        # Instead of validating with Graph, extract user from Fabric token
        import base64, json
        
        token_parts = auth_request.access_token.split('.')
        payload = token_parts[1] + '=' * (4 - len(token_parts[1]) % 4)
        decoded = json.loads(base64.b64decode(payload))
        
        user_data = {
            "email": decoded.get("upn") or decoded.get("unique_name"),
            "display_name": decoded.get("name", "User"),
            "id": decoded.get("oid")
        }
        
        session_id = create_session(user_data, auth_request.access_token)
        # ... rest of code
```

#### 2. Frontend Code

```typescript
async login() {
  // Get Fabric token directly
  const response = await msalInstance.loginPopup({
    scopes: ['https://api.fabric.microsoft.com/.default']
  });
  
  // Send to backend
  await fetch('https://YOUR_BACKEND_URL/auth/client-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      access_token: response.accessToken
    })
  });
}
```

---

## Azure AD App Registration Setup

Before the frontend code works, you MUST configure Azure AD:

### 1. Create App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Name: `Ingage AI Agent Frontend`
5. Supported account types: **Single tenant**
6. Redirect URI: 
   - Type: **Single-page application (SPA)**
   - URL: `https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net`
7. Click **Register**

### 2. Add Additional Redirect URIs

1. Go to **Authentication**
2. Add redirect URI: `http://localhost:4200` (for local testing)
3. **Save**

### 3. Configure API Permissions

1. Go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Delegated permissions**
5. Check: `User.Read`, `openid`, `profile`, `email`
6. Click **Add permissions**

7. Click **Add a permission** again
8. Select **APIs my organization uses**
9. Search for **Power BI Service** or **Microsoft Fabric**
10. If not found, click **Permissions I have requested** → **Add a permission** → **APIs my organization uses** → Type: `https://api.fabric.microsoft.com`
11. For scope, use: `https://api.fabric.microsoft.com/.default`

### 4. Grant Admin Consent

1. Click **Grant admin consent for [Your Org]**
2. Click **Yes**
3. Verify all permissions show green checkmarks

### 5. Copy Configuration

Copy these values for your frontend:
- **Application (client) ID** - Use this as `clientId` in MSAL config
- **Directory (tenant) ID** - Already have this: `4d4eca3f-b031-47f1-8932-59112bf47e6b`

---

## Testing Steps

### 1. Test Authentication

```typescript
// In your browser console after login:
console.log('Testing authentication...');

// Should show user email
fetch('https://YOUR_BACKEND_URL/auth/user', {
  credentials: 'include'
})
.then(r => r.json())
.then(data => console.log('User:', data));
```

### 2. Test Query

```typescript
// Test a simple query
fetch('https://YOUR_BACKEND_URL/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    query: 'total plan count'
  })
})
.then(r => r.json())
.then(data => console.log('Query result:', data));

// Should show:
// {
//   "success": true,
//   "response": "The total plan count is X",
//   "query": "total plan count",
//   "error": null
// }
```

---

## Common Issues & Fixes

### Issue 1: "User not authenticated" (401)
**Cause:** Session cookie not being sent
**Fix:** Add `credentials: 'include'` to all fetch requests

### Issue 2: "CORS error"
**Cause:** Frontend URL not in CORS allowed origins
**Fix:** Backend already configured, check browser dev tools

### Issue 3: "consent_required" error
**Cause:** User hasn't consented to Fabric API permissions
**Fix:** Use `acquireTokenPopup()` instead of `acquireTokenSilent()`

### Issue 4: Still getting 403
**Cause 1:** Token doesn't have Fabric scope
**Fix:** Check console logs - backend will print token audience and scopes

**Cause 2:** User still doesn't have Fabric workspace access
**Fix:** Verify in Fabric Portal that user has Admin/Member role

---

## Quick Checklist

- [ ] Azure AD app registration created
- [ ] Redirect URIs configured (production + localhost)
- [ ] API permissions added (Graph + Fabric)
- [ ] Admin consent granted
- [ ] Client ID copied to frontend config
- [ ] Frontend requests Fabric scope: `https://api.fabric.microsoft.com/.default`
- [ ] Backend URL updated in frontend code
- [ ] `credentials: 'include'` added to all fetch calls
- [ ] User has Fabric workspace access

---

## Summary

**The key change:**
```typescript
// OLD (WRONG)
const response = await msalInstance.loginPopup({
  scopes: ['User.Read']  // ❌ Only gives Graph access
});

// NEW (CORRECT)
const graphResponse = await msalInstance.loginPopup({
  scopes: ['User.Read']
});

const fabricResponse = await msalInstance.acquireTokenSilent({
  scopes: ['https://api.fabric.microsoft.com/.default'],  // ✅ Fabric access
  account: graphResponse.account
});

// Send fabricResponse.accessToken to backend
```

---

## Need Help?

Check the backend console logs - the updated code now prints:
- Token audience (should be `https://api.fabric.microsoft.com`)
- Token scopes (should include Fabric permissions)
- Token roles

This will help diagnose any remaining issues!
