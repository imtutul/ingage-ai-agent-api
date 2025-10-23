# Quick Fix: New User "Connection Error"

## TL;DR - Most Likely Cause
**New users haven't authenticated yet.** The frontend shows a generic "trouble connecting" message when the backend returns authentication errors.

## Immediate Fixes Applied ✅

### 1. Better Error Messages
Changed from HTTP exceptions to user-friendly responses:

**Before:**
```python
raise HTTPException(status_code=401, detail="Not authenticated")
# Frontend shows: "I'm sorry, I'm having trouble connecting to the server"
```

**After:**
```python
return QueryResponse(
    success=False,
    response="Please sign in to continue. Click the 'Sign In' button to authenticate.",
    error="authentication_required"
)
# Frontend shows: "Please sign in to continue. Click the 'Sign In' button to authenticate."
```

### 2. Specific Error Handling
Added intelligent error detection:
- 403 → "You don't have permission. Contact your administrator."
- 401 → "Your session expired. Please sign in again."
- Timeout → "Request took too long. Try a simpler query."
- Connection → "Unable to connect. Check your connection."

## What You Need to Check

### Frontend Checklist:
```typescript
// 1. Include credentials in requests
fetch('/query', {
  credentials: 'include',  // ← Must have this!
  method: 'POST',
  body: JSON.stringify({ query })
})

// 2. Handle auth errors
if (!response.success && response.error === 'authentication_required') {
  // Show sign-in button
  redirectToLogin();
}

// 3. Display the backend's user-friendly message
displayMessage(response.response);  // Now has clear guidance
```

### Backend Checklist:
```bash
# 1. Check service is running
curl http://localhost:8000/health

# 2. Check environment variables
echo $DATA_AGENT_URL
echo $TENANT_ID

# 3. Check logs
tail -f server.log
# Look for: "⚠️ No session cookie found"
```

## Most Common Issues

| Issue | Fix |
|-------|-----|
| **No sign-in flow** | Add "Sign In" button that calls `/auth/client-login` |
| **Cookie not sent** | Add `credentials: 'include'` to fetch/axios |
| **CORS error** | Add frontend URL to `allow_origins` in `main.py` |
| **User lacks permissions** | Add user to Fabric workspace as Viewer/Contributor |
| **Session expired** | Implement auto re-authentication on 401 errors |

## Quick Test

```bash
# 1. Start backend
python start_server.py

# 2. Test without authentication (should get friendly error)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Expected response:
# {
#   "success": false,
#   "response": "Please sign in to continue. Click the 'Sign In' button to authenticate.",
#   "error": "authentication_required"
# }
```

## Next Steps

1. **Update Frontend:**
   - Display the `response` field from API (now has user-friendly messages)
   - Stop showing generic "trouble connecting" error
   - Show "Sign In" button when `error === "authentication_required"`

2. **Test Authentication Flow:**
   - User clicks "Sign In"
   - MSAL gets tokens
   - Call `/auth/client-login` with tokens
   - Verify session cookie is set
   - Try query again (should work)

3. **Monitor Logs:**
   - Watch for specific error patterns
   - Identify common permission issues
   - Add users to Fabric workspace as needed

## See Also
- `TROUBLESHOOTING_NEW_USERS.md` - Comprehensive guide
- `DEBUG_TOKEN_SCRIPT.html` - Token debugging tool
- `diagnose_permissions.py` - Permission testing script
