# Fabric API Error Handling Documentation

## Overview
This document describes the comprehensive error handling implemented in the Fabric Data Agent API, including error categories, frontend integration, and best practices.

## Error Categories

All Fabric-specific errors are prefixed with `FABRIC_` for easy categorization. The API returns consistent error responses with both user-friendly messages and technical details.

### Authentication Errors

#### `FABRIC_AUTH_ERROR`
- **Cause**: Authentication token is invalid or missing
- **User Message**: "Authentication failed. Your session may have expired. Please sign in again."
- **HTTP Status Codes**: 401
- **Frontend Action**: Redirect to login page

#### `FABRIC_TOKEN_EXPIRED`
- **Cause**: Authentication token has expired
- **User Message**: "Your authentication token has expired. Please sign in again."
- **Frontend Action**: Clear session and redirect to login

#### `FABRIC_PERMISSION_ERROR`
- **Cause**: User doesn't have permission to access the Fabric Data Agent
- **User Message**: "You don't have permission to access this Fabric Data Agent. Contact your administrator."
- **HTTP Status Codes**: 403
- **Frontend Action**: Show permission denied message

### Service Errors

#### `FABRIC_SERVER_ERROR`
- **Cause**: Fabric service is experiencing issues (5xx errors)
- **User Message**: "The Fabric service is experiencing issues. Please try again later."
- **HTTP Status Codes**: 500, 502, 503, 504
- **Frontend Action**: Show retry button, log error for monitoring

#### `FABRIC_NOT_FOUND`
- **Cause**: Fabric Data Agent endpoint not found
- **User Message**: "The Fabric Data Agent endpoint was not found. Please verify the configuration."
- **HTTP Status Codes**: 404
- **Frontend Action**: Contact administrator

### Rate Limiting

#### `FABRIC_RATE_LIMIT`
- **Cause**: Too many requests sent to Fabric API
- **User Message**: "Too many requests. Please wait a moment and try again."
- **HTTP Status Codes**: 429
- **Frontend Action**: Implement exponential backoff, show "Please wait" message

### Network Errors

#### `FABRIC_TIMEOUT`
- **Cause**: Query took too long to process
- **User Message**: "The query is taking too long to process. Try a simpler question or try again later."
- **Frontend Action**: Suggest simpler query, show retry button

#### `FABRIC_CONNECTION_ERROR`
- **Cause**: Unable to connect to Fabric service
- **User Message**: "Unable to connect to the Fabric service. Please check your connection and try again."
- **Frontend Action**: Check network status, show retry button

### General Errors

#### `FABRIC_ERROR`
- **Cause**: General Fabric API error not matching other categories
- **User Message**: Specific error message from Fabric API
- **Frontend Action**: Display error message, provide retry option

#### `UNKNOWN_ERROR`
- **Cause**: Unexpected error not categorized
- **User Message**: "An unexpected error occurred. Please try again later."
- **Frontend Action**: Log error, show generic error message

## Response Structure

All API responses follow a consistent structure:

### Success Response
```json
{
  "success": true,
  "response": "The answer to your query...",
  "query": "Your original question"
}
```

### Error Response
```json
{
  "success": false,
  "response": "User-friendly error message",
  "query": "Your original question",
  "error": "ERROR_CATEGORY: Technical error details"
}
```

### Detailed Query Response (Success)
```json
{
  "success": true,
  "response": "The answer to your query...",
  "query": "Your original question",
  "run_status": "completed",
  "steps_count": 3,
  "messages_count": 4,
  "sql_query": "SELECT * FROM ...",
  "data_preview": ["row1", "row2", "..."]
}
```

### Detailed Query Response (Error)
```json
{
  "success": false,
  "response": "User-friendly error message",
  "query": "Your original question",
  "error": "ERROR_CATEGORY: Technical error details",
  "run_status": null,
  "steps_count": null,
  "messages_count": null,
  "sql_query": null,
  "data_preview": null
}
```

## Frontend Integration Guide

### Basic Error Handling

```javascript
async function queryFabricAgent(query) {
  try {
    const response = await fetch('/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ query })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      handleError(data);
      return;
    }
    
    // Display successful response
    displayResponse(data.response);
    
  } catch (error) {
    console.error('Network error:', error);
    showErrorMessage('Unable to connect. Please check your internet connection.');
  }
}
```

### Categorized Error Handling

```javascript
function handleError(errorData) {
  const { error, response } = errorData;
  
  // Parse error category
  const errorCategory = error.split(':')[0];
  
  switch (errorCategory) {
    case 'FABRIC_AUTH_ERROR':
    case 'FABRIC_TOKEN_EXPIRED':
      // Redirect to login
      clearSession();
      window.location.href = '/login';
      break;
      
    case 'FABRIC_PERMISSION_ERROR':
      // Show permission error
      showErrorModal({
        title: 'Access Denied',
        message: response,
        actions: [
          { label: 'Contact Support', onClick: () => contactSupport() },
          { label: 'Close', onClick: () => closeModal() }
        ]
      });
      break;
      
    case 'FABRIC_RATE_LIMIT':
      // Implement backoff
      showErrorMessage(response);
      setTimeout(() => {
        // Allow retry after delay
        enableQueryButton();
      }, 5000);
      break;
      
    case 'FABRIC_TIMEOUT':
      // Show retry with suggestion
      showErrorModal({
        title: 'Query Timeout',
        message: response,
        actions: [
          { label: 'Try Simpler Query', onClick: () => showQuerySuggestions() },
          { label: 'Retry', onClick: () => retryQuery() }
        ]
      });
      break;
      
    case 'FABRIC_SERVER_ERROR':
    case 'FABRIC_CONNECTION_ERROR':
      // Show retry option
      showErrorMessage(response, {
        retry: true,
        onRetry: () => retryQuery()
      });
      break;
      
    default:
      // Generic error handling
      showErrorMessage(response || 'An error occurred. Please try again.');
      logError(error); // Log to monitoring service
  }
}
```

### Error Recovery Strategies

```javascript
// Exponential backoff for rate limiting
async function queryWithBackoff(query, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await queryFabricAgent(query);
      return result;
    } catch (error) {
      if (error.category === 'FABRIC_RATE_LIMIT' && i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s
        console.log(`Rate limited. Retrying in ${delay}ms...`);
        await sleep(delay);
        continue;
      }
      throw error;
    }
  }
}

// Timeout handling with fallback
async function queryWithTimeout(query, timeout = 30000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch('/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ query }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return await response.json();
    
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('FABRIC_TIMEOUT: Request timed out');
    }
    throw error;
  }
}
```

### User Experience Best Practices

1. **Always show user-friendly messages**: Use the `response` field from error responses
2. **Provide actionable next steps**: Include retry buttons, suggestions, or contact info
3. **Log technical details**: Send the `error` field to your monitoring service
4. **Handle authentication gracefully**: Redirect to login without losing user context
5. **Implement progressive retry**: Use exponential backoff for transient errors
6. **Show loading states**: Display progress indicators during API calls
7. **Cache successful responses**: Reduce API calls and improve UX

## Server-Side Logging

All errors are logged with comprehensive context:

```
❌ Query failed for user@example.com:
   Type: Exception
   Message: FABRIC_TIMEOUT: The query is taking too long to process
   Query: What are the sales by region?
   Category: FABRIC_TIMEOUT
   User Message: The query is taking too long to process. Try a simpler question or try again later.
🔍 Full error traceback:
   [Stack trace...]
```

## Testing

Run the test suite to validate error handling:

```bash
# Start the API server
python main.py

# In another terminal, run tests
python test_error_handling.py
```

## Monitoring Recommendations

1. **Track error categories**: Monitor frequency of each `FABRIC_*` error type
2. **Alert on authentication errors**: High rate may indicate auth service issues
3. **Monitor timeout rates**: High timeouts may indicate query complexity issues
4. **Track rate limit errors**: May need to increase quotas or implement caching
5. **Log full error context**: Include user, query, timestamp for debugging

## Common Issues and Solutions

### Issue: Frequent `FABRIC_AUTH_ERROR`
- **Solution**: Check token expiry settings, ensure frontend refreshes tokens

### Issue: Many `FABRIC_TIMEOUT` errors
- **Solution**: Optimize queries, implement query complexity limits, increase timeout

### Issue: `FABRIC_RATE_LIMIT` errors
- **Solution**: Implement frontend caching, request quota increase, add backoff logic

### Issue: `FABRIC_CONNECTION_ERROR`
- **Solution**: Check network configuration, verify Fabric endpoint accessibility

## API Changes Summary

### Modified Files

1. **`fabric_data_agent_client.py`**
   - Changed error handling in `_ask_with_retry()` method
   - Now raises exceptions with `FABRIC_*` prefixes instead of returning error strings
   - Added comprehensive error categorization based on HTTP status codes and error messages
   - Added full traceback logging for debugging

2. **`main.py`**
   - Enhanced `/query` endpoint with comprehensive try-catch
   - Enhanced `/query/detailed` endpoint with comprehensive try-catch
   - Added error category parsing for `FABRIC_*` errors
   - Added user-friendly message generation for all error types
   - Added success/failure logging with user context
   - Re-raises HTTPException for middleware compatibility

### Backward Compatibility

- All existing API endpoints maintain the same request/response structure
- Error responses always include `success: false` flag
- No breaking changes to existing integrations
- Enhanced error details are additive (optional for clients)

## Deployment Checklist

- [ ] Review error messages for sensitive information
- [ ] Configure monitoring for error categories
- [ ] Set up alerts for high error rates
- [ ] Test all error scenarios in staging
- [ ] Update frontend error handling
- [ ] Document error handling for team
- [ ] Deploy to production
- [ ] Monitor error rates post-deployment
