# 🔧 Fix for "Token does not have required scopes" Error (403)

## The Error

```json
{
  "success": true,
  "response": "Error: Error code: 403 - {...'message': 'The token does not have any of the required scopes.'...}",
  "query": "total plan count",
  "error": null
}
```

## What This Means

- ✅ Authentication successful
- ✅ Token sent to backend
- ✅ Session created
- ❌ **Token doesn't have permission to access Fabric AI Skill**

---

## The Problem: Incorrect Scopes

Your frontend is requesting:
```typescript
scopes: ['https://api.fabric.microsoft.com/.default']
```

But Fabric API might require more specific scopes.

---

## Solution 1: Request Specific Fabric Scopes (RECOMMENDED)

### Update Your Frontend Code

Change from `.default` to specific scopes:

```typescript
async login() {
  try {
    // Step 1: Graph login
    const graphResponse = await this.msalInstance.loginPopup({
      scopes: ['User.Read']
    });

    // Step 2: Fabric token with SPECIFIC scopes
    let fabricToken;
    try {
      const fabricResponse = await this.msalInstance.acquireTokenSilent({
        scopes: [
          'https://api.fabric.microsoft.com/Workspace.Read.All',
          'https://api.fabric.microsoft.com/Workspace.ReadWrite.All',
          'https://api.fabric.microsoft.com/Item.Read.All',
          'https://api.fabric.microsoft.com/Item.ReadWrite.All'
        ],
        account: graphResponse.account
      });
      fabricToken = fabricResponse.accessToken;
    } catch (err: any) {
      if (err.errorCode === 'consent_required' || 
          err.errorCode === 'interaction_required') {
        const fabricResponse = await this.msalInstance.acquireTokenPopup({
          scopes: [
            'https://api.fabric.microsoft.com/Workspace.Read.All',
            'https://api.fabric.microsoft.com/Workspace.ReadWrite.All',
            'https://api.fabric.microsoft.com/Item.Read.All',
            'https://api.fabric.microsoft.com/Item.ReadWrite.All'
          ],
          account: graphResponse.account
        });
        fabricToken = fabricResponse.accessToken;
      } else {
        throw err;
      }
    }

    // Step 3: Send to backend
    await this.authenticateWithBackend(fabricToken);
    
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}
```

---

## Solution 2: Add API Permissions in Azure AD (CRITICAL)

Your Azure AD app registration might not have the correct permissions!

### Step 1: Go to Azure Portal

1. Navigate to **Azure Active Directory** → **App registrations**
2. Find your app: `fabric-data-agent-service` or your client app
3. Click on it

### Step 2: Add API Permissions

1. Click **API permissions** in left menu
2. Click **Add a permission**
3. Select **APIs my organization uses**
4. Search for **Microsoft Fabric** or **Power BI Service**
5. Select it

### Step 3: Add These Delegated Permissions

Check these permissions:
- ✅ `Workspace.Read.All`
- ✅ `Workspace.ReadWrite.All`
- ✅ `Item.Read.All`
- ✅ `Item.ReadWrite.All`
- ✅ `Dataflow.Read.All` (if needed)
- ✅ `Dataset.Read.All` (if needed)

### Step 4: Grant Admin Consent

1. Click **Grant admin consent for [Your Organization]**
2. Click **Yes**
3. Wait for green checkmarks to appear

### Step 5: Test Again

Try login and query again - should work now! ✅

---

## Solution 3: Check User Has Access to AI Skill

Even with correct scopes, the **user must have permission** in Fabric workspace.

### Verify in Fabric Portal

1. Go to https://app.fabric.microsoft.com
2. Navigate to workspace: `d09dbe6d-b3f5-4188-a375-482e01aa1213`
3. Find AI Skill: `731c5acd-dbd7-4881-94f4-13ecf0d39c49`
4. Click **Manage access**
5. Verify `ahaque@insightintechnology.com` has **Admin** or **Member** role

### If User Not Listed

1. Click **Add people**
2. Search for: `ahaque@insightintechnology.com`
3. Select role: **Admin** (for testing)
4. Click **Add**
5. Wait 1-2 minutes for permissions to propagate

---

## Solution 4: Use Power BI Service Scopes (Alternative)

Fabric API sometimes uses Power BI scopes. Try this:

```typescript
// Instead of Fabric scopes, use Power BI scopes
scopes: [
  'https://analysis.windows.net/powerbi/api/Dataset.Read.All',
  'https://analysis.windows.net/powerbi/api/Workspace.Read.All'
]
```

Or simply:
```typescript
scopes: ['https://analysis.windows.net/powerbi/api/.default']
```

---

## Debugging: Check Token Scopes

Let's verify what scopes your token actually has.

### In Browser Console (F12)

After getting the Fabric token, decode it:

```javascript
// Get your access token (from your auth code)
const token = 'YOUR_FABRIC_TOKEN_HERE';

// Decode it
const parts = token.split('.');
const payload = JSON.parse(atob(parts[1]));

console.log('Token Audience:', payload.aud);
console.log('Token Scopes:', payload.scp);
console.log('Token Roles:', payload.roles);
```

**Expected:**
```
Token Audience: https://api.fabric.microsoft.com
Token Scopes: Workspace.Read.All Workspace.ReadWrite.All ...
```

**If you see:**
```
Token Scopes: undefined
```

Then the scopes weren't included in the token request!

---

## Backend Debugging

Let's check what the backend sees when it receives the token.

### Update Backend to Log Token Details

The current `main.py` already has debugging code. Check the backend logs when you make a query:

```bash
# In your backend terminal, you should see:
🔍 Token audience: https://api.fabric.microsoft.com
🔍 Token scopes: Workspace.Read.All ...
```

If you see:
```bash
🔍 Token scopes: N/A
```

Then the token doesn't have the required scopes!

---

## Complete Fix Checklist

### 1. Azure AD App Registration
- [ ] Add Microsoft Fabric / Power BI API permissions
- [ ] Include: `Workspace.Read.All`, `Workspace.ReadWrite.All`, `Item.Read.All`, `Item.ReadWrite.All`
- [ ] Grant admin consent
- [ ] Verify green checkmarks appear

### 2. Frontend Code
- [ ] Update scopes in `acquireTokenSilent()` and `acquireTokenPopup()`
- [ ] Use specific scopes (not just `.default`)
- [ ] Handle consent_required error

### 3. Fabric Workspace Permissions
- [ ] User has Admin or Member role in workspace
- [ ] User has access to the specific AI Skill
- [ ] Wait 1-2 minutes after granting access

### 4. Test
- [ ] Clear browser cache
- [ ] Login again
- [ ] Accept consent popup (if shown)
- [ ] Try query: "total plan count"
- [ ] Should get real data! ✅

---

## Quick Fix (Try This First)

### Option A: Use .default with Admin Consent

1. **Azure AD**: Grant admin consent for Fabric API
2. **Frontend**: Keep using `.default` scope
3. **Test**: Should work if admin consent granted

### Option B: Use Specific Scopes

1. **Frontend**: Change to specific scopes (see Solution 1)
2. **Test**: User will see consent popup with specific permissions
3. **Accept**: Consent popup
4. **Test**: Should work!

---

## Expected vs Actual

### What Should Happen:
```
User queries "total plan count"
→ Backend uses Fabric token
→ Calls Fabric API
→ Returns: "The total plan count is 42"
```

### What's Happening Now:
```
User queries "total plan count"
→ Backend uses Fabric token
→ Calls Fabric API
→ Fabric API says: "Token doesn't have required scopes"
→ Returns: 403 error
```

---

## Most Likely Cause

Your Azure AD app registration **doesn't have Fabric API permissions added**.

### Fix It Now:

1. **Azure Portal** → **Azure Active Directory** → **App registrations**
2. **Find your app** (Client ID from your frontend config)
3. **API permissions** → **Add a permission** → **Microsoft Fabric** or **Power BI Service**
4. **Add permissions** → **Grant admin consent**
5. **Test again**

This should fix it! 🚀

---

## Still Not Working?

Share:
1. What scopes you're requesting in frontend
2. What permissions are in your Azure AD app registration
3. Backend logs when you make a query (should show token scopes)

I'll help you debug further!
