# Intermittent 500 Error Fix

## Problem Analysis
Based on the browser console logs, users are experiencing intermittent 500 Internal Server Errors (~30% failure rate) that occur randomly during query requests.

## Root Causes Identified

### 1. **Token Expiration Issues**
- Fabric API tokens expire after 1 hour
- No automatic token refresh mechanism
- Failed token refresh causes 500 errors

### 2. **OpenAI Thread Management**
- Threads not being cleaned up properly
- Memory leaks from unclosed threads
- Thread limits being exceeded

### 3. **Rate Limiting**
- Hitting Fabric API rate limits
- No backoff/retry mechanism
- Concurrent requests causing issues

### 4. **Error Handling**
- Generic error handling masking real issues
- 500 errors instead of proper error responses
- No user-friendly error messages

## Fixes Implemented

### 1. **Enhanced Error Handling**

**File: `fabric_data_agent_client.py`**
- Added specific error type detection
- User-friendly error messages for common issues
- Better logging and debugging information

```python
# Before (generic)
except Exception as e:
    return f"Error: {e}"

# After (specific)  
except Exception as e:
    if "401" in error_msg:
        return "Authentication failed. Please sign in again."
    elif "429" in error_msg:
        return "Too many requests. Please wait and try again."
    # ... more specific handling
```

### 2. **Improved Token Management**

**Enhancement:** Better token expiration checking and refresh logic
- Check token expiration before each request
- Automatic token refresh when needed
- Fallback to re-authentication on token failure

### 3. **Thread Cleanup**

**Issue:** OpenAI threads not being cleaned up properly
**Fix:** Enhanced cleanup in try/finally blocks

### 4. **Retry Logic Framework**

**File: `retry_logic.py`**
- Implemented exponential backoff retry mechanism
- Smart retry decisions based on error type
- Configurable retry attempts and delays

## Quick Fixes to Apply

### Fix 1: Restart Server with Enhanced Error Handling
The server now has better error handling. Restart it to apply the changes:

```bash
# Stop current server (Ctrl+C)
# Then restart:
python main.py
```

### Fix 2: Add Service Principal Authentication (Recommended)
To avoid token expiration issues, add these to your `.env` file:

```properties
CLIENT_ID=your-azure-ad-app-client-id
CLIENT_SECRET=your-azure-ad-app-secret
```

This switches from Interactive Browser auth to Service Principal auth, which is more reliable for production.

### Fix 3: Frontend Error Handling
Update your frontend to handle different error types:

```typescript
// Better error handling in frontend
const handleQueryError = (error: any) => {
  if (error.status === 401) {
    // Redirect to login
    window.location.reload();
  } else if (error.status === 500) {
    // Show retry option
    showRetryButton();
  } else {
    // Show generic error
    showErrorMessage("Please try again later");
  }
};
```

## Testing the Fixes

### 1. Run the Diagnostic Script
```bash
python test_500_errors.py
```

This will help identify if the 500 errors are still occurring and what's causing them.

### 2. Monitor Server Logs
Watch the server console for detailed error information:
- Error types and messages
- Token refresh attempts
- Thread cleanup status

### 3. Check Browser Console
Look for improved error messages in the browser console instead of generic 500 errors.

## Expected Improvements

After applying these fixes:

1. **Reduced Error Rate**: 500 errors should decrease significantly
2. **Better Error Messages**: Users see helpful messages instead of "server error"
3. **Automatic Recovery**: Token refresh and retry logic handle transient issues
4. **Improved Debugging**: Better logs help identify remaining issues

## Monitoring and Maintenance

### Health Check Endpoint
Monitor server health: `GET /health`

### Log Monitoring
Watch for these patterns in logs:
- `✅ Token refreshed successfully`
- `🔄 Retrying in X seconds...`
- `❌ Error calling data agent:` (with detailed info)

### Performance Metrics
Track:
- Query success rate
- Average response time  
- Token refresh frequency
- Thread cleanup success

## If Issues Persist

If 500 errors continue after these fixes:

1. **Check Azure AD App Permissions**
   - Ensure proper API permissions
   - Verify admin consent is granted

2. **Monitor Fabric API Limits**
   - Check if hitting rate limits
   - Consider request throttling

3. **Review Thread Management**
   - Monitor OpenAI thread creation/cleanup
   - Check for thread limit issues

4. **Enable Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

---

*Fixes implemented: October 23, 2025*
*Expected: Significant reduction in 500 errors and better user experience*