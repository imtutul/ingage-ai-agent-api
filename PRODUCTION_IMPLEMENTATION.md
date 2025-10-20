# 🔧 Production Implementation Guide - Priority 1 Items

## This guide implements the CRITICAL changes needed for production

---

## 1. Redis Session Storage

### Why This is Critical
Your current in-memory sessions (`sessions: Dict[str, Dict[str, Any]] = {}`) will NOT work in production because:
- Azure App Service runs multiple instances
- Sessions stored in one instance won't be available in another
- Users will randomly lose their session

### Installation

Add to `requirements.txt`:
```
redis>=5.0.0
hiredis>=2.2.3  # Optional: faster Redis protocol parser
```

### Configuration

Add to `.env` or Azure App Service Configuration:
```env
REDIS_HOST=your-redis.redis.cache.windows.net
REDIS_PORT=6380
REDIS_PASSWORD=your-redis-key
REDIS_SSL=true

# Or for local development:
REDIS_URL=redis://localhost:6379/0
```

### Implementation

See the updated `main.py` - I'll create this next.

---

## 2. Structured Logging

### Why This is Critical
`print()` statements don't work well in production:
- No log levels (can't filter INFO vs ERROR)
- No timestamps
- No correlation IDs
- Can't search/analyze logs

### Implementation

Replace all `print()` with proper `logging`:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use it:
logger.info("User authenticated: %s", user_email)
logger.error("Query failed: %s", error, exc_info=True)
```

---

## 3. Secure Cookies

### Why This is Critical
Production cookies MUST be secure:
- `secure=True` - Only sent over HTTPS
- `httponly=True` - Can't be accessed by JavaScript (prevents XSS)
- `samesite` - Prevents CSRF attacks

### Implementation

```python
# Detect environment
is_production = os.getenv("ENVIRONMENT", "development") == "production"

# Set cookie
response.set_cookie(
    key=SESSION_COOKIE_NAME,
    value=session_id,
    httponly=True,
    secure=is_production,  # True in production
    samesite="lax",
    max_age=SESSION_EXPIRY_HOURS * 3600,
    domain=None  # Let browser determine
)
```

---

## 4. Environment Variables in Azure

### Why This is Critical
Never commit secrets to code:
- Anyone with repo access can see them
- Exposed in GitHub/version control
- Hard to rotate/update

### Azure App Service Configuration

1. Go to Azure Portal
2. Your App Service → Configuration → Application settings
3. Add these:

```
Name: TENANT_ID
Value: 4d4eca3f-b031-47f1-8932-59112bf47e6b

Name: DATA_AGENT_URL
Value: https://api.fabric.microsoft.com/v1/workspaces/...

Name: REDIS_HOST
Value: your-redis.redis.cache.windows.net

Name: REDIS_PASSWORD
Value: your-redis-key

Name: ENVIRONMENT
Value: production

Name: ALLOWED_ORIGINS
Value: https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net

Name: SECRET_KEY
Value: your-secret-key-for-session-signing
```

4. Click **Save**

### Remove .env from Production

Add to `.gitignore`:
```
.env
.env.production
*.env
```

---

## 5. Rate Limiting

### Why This is Critical
Protect your API from:
- Abuse
- DDoS attacks
- Accidental infinite loops
- Excessive costs (Fabric API charges)

### Installation

```
slowapi>=0.1.8
```

### Implementation

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@app.post("/query")
@limiter.limit("10/minute")  # 10 queries per minute per IP
async def simple_query(...):
    ...
```

---

## Complete Implementation

I'll create an updated `main.py` with all Priority 1 changes in the next file.

---

## Testing in Production

### 1. Test Redis Connection
```bash
curl https://your-app.azurewebsites.net/health
```

Should show:
```json
{
  "status": "healthy",
  "redis_connected": true,
  "fabric_client_initialized": true
}
```

### 2. Test Authentication
```bash
# Login
curl -X POST https://your-app.azurewebsites.net/auth/client-login \
  -H "Content-Type: application/json" \
  -d '{"access_token": "YOUR_TOKEN"}' \
  -c cookies.txt

# Test query (uses session from cookies.txt)
curl -X POST https://your-app.azurewebsites.net/query \
  -H "Content-Type: application/json" \
  -d '{"query": "total plan count"}' \
  -b cookies.txt
```

### 3. Test Rate Limiting
```bash
# Run this 11 times quickly
for i in {1..11}; do
  curl -X POST https://your-app.azurewebsites.net/query \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}' \
    -b cookies.txt
done
```

11th request should return `429 Too Many Requests`

---

## Deployment Steps

### 1. Update Code
```bash
# Pull latest changes
git pull

# Install new dependencies
pip install -r requirements.txt
```

### 2. Set Environment Variables in Azure
(See section above)

### 3. Deploy
```bash
# If using Azure CLI
az webapp up --name ingage-ai-agent-api

# Or use GitHub Actions / Azure DevOps
```

### 4. Verify
```bash
# Check health
curl https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net/health

# Check logs in Azure Portal
# App Service → Log stream
```

---

## Rollback Plan

If something goes wrong:

1. **Azure Portal** → Your App Service → **Deployment Center**
2. Click **Redeploy** on previous successful deployment
3. Or revert git commit and redeploy

---

## Monitoring

### Check Logs
```bash
# Azure CLI
az webapp log tail --name ingage-ai-agent-api --resource-group your-rg

# Or in Azure Portal:
# App Service → Log stream
```

### Check Metrics
```bash
# Azure Portal
# App Service → Metrics
# Monitor:
# - Response time
# - Request count
# - Error rate
# - Memory usage
```

---

## Next Steps

1. ✅ Review the updated `main_production.py` (creating next)
2. ✅ Set up Azure Cache for Redis
3. ✅ Configure environment variables in Azure
4. ✅ Deploy and test
5. ✅ Set up Application Insights (Priority 2)

**Estimated time to implement:** 4-5 hours
