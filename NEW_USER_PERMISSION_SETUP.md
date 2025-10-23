# New User Permission Setup Guide

## Overview
This guide provides step-by-step instructions for administrators to properly configure permissions for new users to access the Ingage AI Agent application backed by Microsoft Fabric Data Agents.

---

## 📋 Prerequisites

Before setting up permissions for a new user, ensure:
- You have **Admin** or **Workspace Admin** access to the Microsoft Fabric workspace
- The user has a valid Microsoft 365/Azure AD account in your organization
- The user's email address is known
- You have access to the Azure Portal (for Azure AD App Registration configuration)

---

## 🎯 Permission Levels Overview

### Workspace Roles in Microsoft Fabric
- **Admin**: Full control - manage workspace, items, and permissions
- **Member**: Can create and edit content
- **Contributor**: Can edit content but not publish
- **Viewer**: Read-only access (recommended for most end users)

### Recommended Role for End Users
**Viewer** - This provides sufficient permissions to query the Data Agent without allowing them to modify datasets or workspace settings.

---

## 🔧 Step-by-Step Permission Setup

### Step 1: Add User to Microsoft Fabric Workspace

1. **Navigate to Microsoft Fabric Portal**
   - Go to [https://app.fabric.microsoft.com](https://app.fabric.microsoft.com)
   - Sign in with your admin account

2. **Open Your Workspace**
   - In the left sidebar, click on **Workspaces**
   - Find and click on your workspace
   - Your workspace ID is: `d09dbe6d-b3f5-4188-a375-482e01aa1213`

3. **Access Workspace Settings**
   - Click the **⚙️ Settings** icon in the top-right corner
   - Select **Manage access** from the dropdown menu

4. **Add the New User**
   - Click **+ Add people or groups** button
   - In the search box, type the user's email address or name
   - Select the user from the search results
   - Choose role: **Viewer** (or higher if needed)
   - Click **Add**

5. **Verify User Access**
   - The user should now appear in the access list
   - Confirm the role is correct
   - User will receive an email notification about workspace access

### Step 2: Grant Access to Data Agent Item (If Required)

Some organizations require explicit item-level permissions:

1. **Navigate to the Data Agent**
   - In your workspace, find the Data Agent item
   - Your Data Agent is part of the workspace items

2. **Check Item Permissions**
   - Click on the **...** (three dots) next to the Data Agent item
   - Select **Manage permissions** or **Share**
   - Verify the new user has access through workspace membership
   - If not, add them explicitly with **Viewer** permissions

### Step 3: Configure Azure AD App Registration (One-Time Setup)

This step is typically done once during initial setup, but verify it's configured:

1. **Open Azure Portal**
   - Go to [https://portal.azure.com](https://portal.azure.com)
   - Navigate to **Azure Active Directory** → **App registrations**
   - Find your app registration (used for this application)

2. **Verify API Permissions**
   The app registration must have these permissions:
   
   - **Microsoft Graph**:
     - `User.Read` (Delegated) - for user authentication
     - `User.ReadBasic.All` (Delegated) - for reading user profiles
   
   - **Power BI Service** (Fabric uses Power BI API):
     - `Dataset.Read.All` (Delegated) - for reading data
     - `Workspace.Read.All` (Delegated) - for accessing workspaces
   
   - **Microsoft Fabric** (if available):
     - `https://api.fabric.microsoft.com/Workspace.Read.All`
     - `https://api.fabric.microsoft.com/Dataset.Read.All`

3. **Grant Admin Consent**
   - In the API permissions page
   - Click **Grant admin consent for [Your Organization]**
   - Confirm the consent
   - This allows users to use the app without individual consent

4. **Verify Redirect URIs**
   - Go to **Authentication** tab
   - Ensure your frontend URLs are listed under **Redirect URIs**:
     - `http://localhost:4200` (for local development)
     - Your production frontend URL
   - Enable **Implicit grant and hybrid flows**:
     - ✅ Access tokens (for implicit flows)
     - ✅ ID tokens (for implicit and hybrid flows)

### Step 4: Test User Access

1. **Have the User Sign In**
   - User opens the application frontend
   - Clicks **Sign In** button
   - Authenticates with their Microsoft 365 credentials
   - Frontend obtains tokens via MSAL.js
   - Frontend sends tokens to backend `/auth/client-login`
   - Backend validates and creates session

2. **Verify Authentication**
   - User should see a successful sign-in message
   - No "Please sign in" or connection errors
   - User can see the query interface

3. **Test a Simple Query**
   - Have user try: "Hello, what can you help me with?"
   - This tests basic connectivity without data access
   - Should receive a response from the Data Agent

4. **Test Data Access**
   - Have user try: "How many members do we have?"
   - This tests actual data permissions
   - Should return actual data from the database
   - If this fails but basic query works → permission issue

---

## 🔍 Verification Checklist

After completing setup, verify the following:

### Workspace Access
- [ ] User appears in workspace **Manage access** list
- [ ] User role is **Viewer** or higher
- [ ] User received email notification about access

### Application Access
- [ ] User can open the application frontend
- [ ] Sign In button is visible and functional
- [ ] User can authenticate with their Microsoft 365 account
- [ ] No CORS errors in browser console

### Data Access
- [ ] User can make basic queries (non-data queries)
- [ ] User can query actual data from the database
- [ ] Responses are meaningful and not error messages
- [ ] No permission-related errors in backend logs

### Token Permissions
- [ ] Azure AD app has required API permissions
- [ ] Admin consent has been granted
- [ ] Token scopes include Fabric/Power BI API access
- [ ] Frontend requests correct scopes during authentication

---

## 🚨 Common Issues and Solutions

### Issue 1: User Sees "Connection Error"
**Symptoms:** Generic "trouble connecting to server" message

**Causes & Solutions:**
1. **User hasn't signed in**
   - Solution: Have user click "Sign In" button
   - Frontend must implement authentication flow

2. **CORS not configured**
   - Solution: Add user's frontend URL to backend CORS whitelist
   - Edit `main.py` → `CORSMiddleware` → `allow_origins`

3. **Session cookie not being sent**
   - Solution: Frontend must include `credentials: 'include'` in fetch requests
   - Or `withCredentials: true` in Axios

### Issue 2: User Authenticated but Queries Fail with 403
**Symptoms:** User signed in successfully, but data queries return "permission denied"

**Causes & Solutions:**
1. **User not in Fabric workspace**
   - Solution: Follow Step 1 above to add user to workspace
   
2. **Insufficient workspace role**
   - Solution: Change user role from Viewer to Member/Contributor
   - Or verify data sources allow Viewer access

3. **Token missing required scopes**
   - Solution: Update frontend MSAL config to request correct scopes
   ```typescript
   const loginRequest = {
     scopes: [
       "https://api.fabric.microsoft.com/.default",
       "User.Read"
     ]
   };
   ```

### Issue 3: User Can Query but Gets "Technical Issue" Errors
**Symptoms:** Authentication works, some queries work, but data queries fail

**Causes & Solutions:**
1. **Data source permissions**
   - User has workspace access but not underlying data source access
   - Solution: Grant user access to SQL database, data warehouse, or lakehouse
   - Check data source security settings in Fabric

2. **Row-level security (RLS)**
   - Data has RLS rules that prevent user from seeing data
   - Solution: Update RLS roles to include user
   - Or assign user to appropriate security role

### Issue 4: Session Expires Quickly
**Symptoms:** User authenticated but gets kicked out after short time

**Causes & Solutions:**
1. **Server restarts clear sessions**
   - Sessions are stored in memory (default)
   - Solution: Use persistent session storage (Redis, database)
   - Or implement automatic re-authentication

2. **Token expiration**
   - Fabric tokens typically expire after 1 hour
   - Solution: Implement token refresh in frontend
   - Request new tokens before expiration

---

## 🔐 Security Best Practices

### For Administrators

1. **Principle of Least Privilege**
   - Give users only the minimum required permissions
   - Use **Viewer** role unless user needs to create/edit content
   - Regularly audit user access and remove unnecessary permissions

2. **Regular Permission Reviews**
   - Quarterly review of workspace member list
   - Remove users who no longer need access
   - Update roles based on job function changes

3. **Audit Logging**
   - Enable audit logging in Microsoft Fabric
   - Monitor for suspicious query patterns
   - Review failed authentication attempts

4. **Data Classification**
   - Mark sensitive datasets appropriately
   - Implement row-level security for sensitive data
   - Use separate workspaces for different sensitivity levels

### For Developers

1. **Never Store Credentials**
   - Don't log or store user tokens
   - Don't commit credentials to source control
   - Use environment variables for secrets

2. **Validate All Tokens**
   - Backend must validate tokens before queries
   - Check token expiration
   - Verify token audience and issuer

3. **Implement Rate Limiting**
   - Prevent abuse through excessive queries
   - Set reasonable limits per user/session
   - Return clear error messages when limits exceeded

4. **Secure Session Management**
   - Use secure, httpOnly cookies for sessions
   - Implement session timeout (24 hours default)
   - Clear sessions on logout

---

## 📊 Permission Testing Script

Use this script to test if a user has proper permissions:

```bash
# Run the diagnostic script
python diagnose_permissions.py

# Or verify data access specifically
python verify_data_access.py
```

**Expected Output for Properly Configured User:**
```
✅ Authentication: Success
✅ Workspace Access: Confirmed
✅ Data Agent Access: Confirmed
✅ Basic Query: Success
✅ Data Query: Success - Retrieved actual data
```

**Output Indicating Permission Issues:**
```
✅ Authentication: Success
✅ Workspace Access: Confirmed
✅ Data Agent Access: Confirmed
✅ Basic Query: Success
❌ Data Query: 403 Forbidden - User lacks data source permissions
```

---

## 🎓 User Onboarding Flow

### For End Users - First Time Setup

1. **Receive Access Notification**
   - User receives email: "You've been added to [Workspace Name]"
   - Email contains link to Microsoft Fabric workspace

2. **Access the Application**
   - Open application URL provided by administrator
   - See welcome screen with "Sign In" button

3. **Sign In**
   - Click "Sign In" button
   - Redirected to Microsoft login page
   - Enter Microsoft 365 credentials
   - Grant consent if prompted (first time only)
   - Redirected back to application

4. **Start Using the Agent**
   - Try a test query: "Hello, what can you help me with?"
   - Verify response is received
   - Try actual data query: "How many members do we have?"
   - Explore available features

### For End Users - Troubleshooting

**If Sign In Fails:**
- Ensure you're using your work Microsoft 365 account
- Check if your account is in the organization
- Contact administrator if you see permission errors

**If Queries Fail After Sign In:**
- Try signing out and signing in again
- Clear browser cookies and cache
- Try a different browser
- Contact administrator if issue persists

**Error Messages and Meanings:**
- "Please sign in to continue" → Click Sign In button
- "You don't have permission" → Contact administrator
- "Session expired" → Sign in again
- "Technical issue" → Wait and retry, or contact support

---

## 📝 Administrator Checklist Template

Use this checklist when onboarding a new user:

```
NEW USER ONBOARDING - [User Name] ([User Email])
Date: [Date]
Administrator: [Your Name]

□ STEP 1: WORKSPACE ACCESS
  □ Added user to workspace: d09dbe6d-b3f5-4188-a375-482e01aa1213
  □ Assigned role: [ ] Viewer [ ] Contributor [ ] Member [ ] Admin
  □ User received email notification
  □ Verified user appears in access list

□ STEP 2: AZURE AD APP (One-time verification)
  □ App has required API permissions
  □ Admin consent granted
  □ Redirect URIs include frontend URLs
  □ Implicit grant enabled

□ STEP 3: TESTING
  □ User can open application
  □ User can sign in successfully
  □ User can make basic queries
  □ User can query actual data
  □ No errors in backend logs

□ STEP 4: USER COMMUNICATION
  □ Sent application URL to user
  □ Provided quick start guide
  □ Explained sign-in process
  □ Shared support contact information

NOTES:
_________________________________________________
_________________________________________________

APPROVED BY: _________________ DATE: ___________
```

---

## 🆘 Getting Help

### For Administrators
- Review backend logs: `tail -f server.log`
- Run diagnostic scripts: `python diagnose_permissions.py`
- Check Azure AD audit logs for authentication issues
- Review Fabric workspace audit logs for access issues

### For End Users
- Contact your organization's administrator
- Provide screenshot of error message
- Include timestamp of when issue occurred
- Mention what action you were trying to perform

### For Developers
- See `TROUBLESHOOTING_NEW_USERS.md` for detailed troubleshooting
- See `QUICK_FIX.md` for common fixes
- Check backend logs for specific error messages
- Use browser DevTools Network tab to inspect requests/responses

---

## 🔄 Regular Maintenance

### Monthly Tasks
- Review list of users with access
- Remove users who no longer need access
- Verify Azure AD app permissions are still valid
- Check for any security advisories from Microsoft

### Quarterly Tasks
- Full permission audit of all users
- Review and update security policies
- Test disaster recovery procedures
- Update documentation with any changes

### Annual Tasks
- Review and renew Azure AD app secrets/certificates
- Comprehensive security review
- User satisfaction survey
- Training refresh for administrators

---

## 📚 Additional Resources

### Microsoft Fabric Documentation
- [Workspace roles and permissions](https://learn.microsoft.com/en-us/fabric/get-started/roles-workspaces)
- [Share and manage access](https://learn.microsoft.com/en-us/fabric/get-started/share-items)
- [Security in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/security/security-overview)

### Azure AD Documentation
- [App registration permissions](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-configure-app-access-web-apis)
- [Admin consent workflow](https://learn.microsoft.com/en-us/azure/active-directory/manage-apps/configure-admin-consent-workflow)
- [Token validation](https://learn.microsoft.com/en-us/azure/active-directory/develop/access-tokens)

### This Application
- `TROUBLESHOOTING_NEW_USERS.md` - Detailed troubleshooting guide
- `QUICK_FIX.md` - Quick fixes for common issues
- `README.md` - Application overview and setup

---

## Summary

Setting up permissions for new users requires:

1. ✅ **Add user to Fabric workspace** with appropriate role (usually Viewer)
2. ✅ **Verify Azure AD app** has required permissions and admin consent
3. ✅ **Test user access** through sign-in and sample queries
4. ✅ **Monitor and maintain** permissions regularly

**Most common issue:** Users see "connection error" because they haven't signed in yet. Ensure your frontend has a clear "Sign In" button and authentication flow.

**Key takeaway:** Permission issues manifest as authentication errors. The application is designed to return clear, user-friendly error messages to guide users on what action to take.

---

*Last Updated: October 21, 2025*
*Version: 1.0*
