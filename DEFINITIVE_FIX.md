# 🚨 DEFINITIVE FIX for 403 Scopes Error

## You're Still Getting This Error

```json
{
  "errorCode": "UnknownError",
  "message": "Internal error AuthorizationFailedException.The token does not have any of the required scopes."
}
```

This means **the token you're sending to Fabric API has NO scopes at all**.

---

## 🔍 Step 1: Verify What's in Your Token (CRITICAL)

Let's check what you're actually sending. Run this in your **browser console** (F12) after you login:

```javascript
// After login completes, run this to see what token you got
console.log('=== CHECKING TOKEN ===');

// If you can access the token from your code, paste it here:
// const token = fabricResponse.accessToken;  // Get from your code

// Or manually paste the token you're sending:
const token = 'PASTE_YOUR_FABRIC_TOKEN_HERE';

// Decode and display
try {
  const parts = token.split('.');
  const header = JSON.parse(atob(parts[0]));
  const payload = JSON.parse(atob(parts[1]));
  
  console.log('=== TOKEN HEADER ===');
  console.log('Algorithm:', header.alg);
  console.log('Type:', header.typ);
  
  console.log('\n=== TOKEN PAYLOAD ===');
  console.log('Audience (aud):', payload.aud);
  console.log('Issuer (iss):', payload.iss);
  console.log('App ID (appid):', payload.appid);
  console.log('Scopes (scp):', payload.scp);
  console.log('Roles (roles):', payload.roles);
  console.log('User:', payload.upn || payload.unique_name);
  console.log('Expires:', new Date(payload.exp * 1000).toLocaleString());
  
  console.log('\n=== FULL PAYLOAD ===');
  console.log(JSON.stringify(payload, null, 2));
  
} catch (e) {
  console.error('Failed to decode token:', e);
}
```

**SHARE THE OUTPUT WITH ME!** This will tell us exactly what's wrong.

---

## 🎯 Step 2: The Problem

Based on the persistent error, here's what's likely happening:

### Your frontend is requesting:
```typescript
scopes: ['https://api.fabric.microsoft.com/.default']
```

### But the token you're getting has:
- **Audience:** `https://api.fabric.microsoft.com` ✅
- **Scopes:** `undefined` or empty ❌

This happens because:
1. Your Azure AD app doesn't have Fabric API permissions configured
2. OR you're not requesting the scopes correctly
3. OR you need to use Power BI Service scopes instead

---

## 🛠️ Step 3: The Complete Fix

### Option A: Use Power BI Service Scopes (RECOMMENDED)

Microsoft Fabric uses **Power BI Service** as its underlying API.

#### Update Your Frontend Code

**Find this in your frontend:**
```typescript
scopes: ['https://api.fabric.microsoft.com/.default']
```

**Replace with:**
```typescript
scopes: ['https://analysis.windows.net/powerbi/api/.default']
```

**Complete example:**
```typescript
async login() {
  try {
    // Step 1: Graph authentication
    const graphResponse = await this.msalInstance.loginPopup({
      scopes: ['User.Read']
    });

    // Step 2: Power BI/Fabric token
    let fabricToken;
    try {
      const fabricResponse = await this.msalInstance.acquireTokenSilent({
        scopes: ['https://analysis.windows.net/powerbi/api/.default'], // ← Changed!
        account: graphResponse.account
      });
      fabricToken = fabricResponse.accessToken;
    } catch (err: any) {
      if (err.errorCode === 'consent_required' || 
          err.errorCode === 'interaction_required') {
        const fabricResponse = await this.msalInstance.acquireTokenPopup({
          scopes: ['https://analysis.windows.net/powerbi/api/.default'], // ← Changed!
          account: graphResponse.account
        });
        fabricToken = fabricResponse.accessToken;
      } else {
        throw err;
      }
    }

    // Step 3: Send to backend
    await fetch('http://localhost:8000/auth/client-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ access_token: fabricToken })
    });
    
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}
```

---

### Option B: Add Power BI API Permissions in Azure AD

Your Azure AD app needs Power BI Service permissions.

#### Go to Azure Portal

1. https://portal.azure.com
2. **Azure Active Directory** → **App registrations**
3. Find your app (the Client ID you're using in frontend)
4. Click **API permissions**

#### Add Power BI Permissions

1. Click **+ Add a permission**
2. Click **APIs my organization uses** tab
3. Search for: **Power BI Service**
4. Click on it
5. Select **Delegated permissions**
6. Check these minimum permissions:
   - ✅ `Dataset.Read.All`
   - ✅ `Dataset.ReadWrite.All`
   - ✅ `Workspace.Read.All`
   - ✅ `Workspace.ReadWrite.All`

7. Click **Add permissions**
8. Click **Grant admin consent for [Your Org]**
9. Click **Yes**
10. Verify all permissions show **green checkmarks** ✅

---

## 🧪 Step 4: Test the Fix

### Clear Everything
```javascript
// In browser console
localStorage.clear();
sessionStorage.clear();
// Or use Incognito/Private mode
```

### Login Again

1. Close all browser windows
2. Open in **Incognito/Private mode**
3. Navigate to your app
4. Click "Sign In with Microsoft"
5. **You should see a NEW consent popup** asking for Power BI permissions
6. **Accept it**
7. Try query: "total plan count"
8. **Should work!** ✅

---

## 📊 Expected Results

### Before Fix (Current):
```json
{
  "success": true,
  "response": "Error: Error code: 403 - ...token does not have required scopes...",
  "error": null
}
```

### After Fix:
```json
{
  "success": true,
  "response": "The total plan count is 42",
  "query": "total plan count",
  "error": null
}
```

---

## 🔍 Debugging Checklist

If it still doesn't work after the fix:

### 1. Check Token Audience
Run the token decoder script (Step 1) and verify:
- **Audience should be:** `https://analysis.windows.net/powerbi/api` ✅
- **Scopes should include:** Workspace or Dataset permissions ✅

### 2. Check Azure AD Permissions
In Azure Portal:
- Power BI Service API permissions added ✅
- Admin consent granted (green checkmarks) ✅

### 3. Check Fabric Workspace Access
In Fabric Portal (https://app.fabric.microsoft.com):
- User `ahaque@insightintechnology.com` is Admin/Member ✅
- User has access to workspace `d09dbe6d-b3f5-4188-a375-482e01aa1213` ✅
- User has access to AI Skill `731c5acd-dbd7-4881-94f4-13ecf0d39c49` ✅

---

## 🚀 Quick Summary

**The fix is simple:**

1. **Change frontend scopes from:**
   ```typescript
   'https://api.fabric.microsoft.com/.default'
   ```
   
2. **To:**
   ```typescript
   'https://analysis.windows.net/powerbi/api/.default'
   ```

3. **Add Power BI Service permissions in Azure AD**

4. **Grant admin consent**

5. **Test in incognito mode**

---

## ⚠️ Common Mistakes

### ❌ Wrong: Using Fabric API endpoint
```typescript
scopes: ['https://api.fabric.microsoft.com/.default']
// This doesn't include the scopes!
```

### ✅ Right: Using Power BI Service endpoint
```typescript
scopes: ['https://analysis.windows.net/powerbi/api/.default']
// This includes all necessary scopes!
```

---

## 🆘 Still Not Working?

**Share these 3 things with me:**

1. **Output from token decoder** (Step 1 script)
   - What's the audience?
   - What scopes does it show?

2. **Screenshot of Azure AD API permissions page**
   - What permissions are configured?
   - Are they granted (green checkmarks)?

3. **What scope are you requesting in frontend?**
   - Share the exact line of code

I'll give you the exact fix based on this info! 🎯

---

## 💡 Why This Happens

Microsoft Fabric is built on Power BI infrastructure, so:
- Fabric Data Agent API endpoint: `https://api.fabric.microsoft.com`
- But authentication uses: `https://analysis.windows.net/powerbi/api`
- Scopes come from: **Power BI Service**

You were requesting token for Fabric endpoint, but it doesn't return scopes.
You need to request token for Power BI endpoint, which returns proper scopes!

---

## ✅ Action Items (Do These Now)

1. [ ] Run token decoder script (copy output)
2. [ ] Change frontend scope to Power BI endpoint
3. [ ] Add Power BI permissions in Azure AD
4. [ ] Grant admin consent
5. [ ] Test in incognito mode
6. [ ] Share results

**This WILL fix it!** 🚀
