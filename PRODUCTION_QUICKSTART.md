# 🎯 Production Deployment - Quick Start Guide

## You asked: "I want to make my code ready for production"

Here's everything you need to know in one place.

---

## ⚡ TL;DR - What You Need to Do

1. **Install new dependencies** (5 minutes)
2. **Set up Redis in Azure** (30 minutes)
3. **Configure Azure App Service** (15 minutes)
4. **Deploy updated code** (20 minutes)
5. **Test and verify** (15 minutes)

**Total time: ~1.5-2 hours**

---

## 📦 What I've Created for You

### Production-Ready Files
1. **`main_production.py`** - Production version of your API with:
   - ✅ Redis session storage (works with multiple instances)
   - ✅ Structured logging (better debugging)
   - ✅ Secure cookies (HTTPS only in production)
   - ✅ Rate limiting (prevent abuse)
   - ✅ Proper error handling
   - ✅ Health checks
   - ✅ CORS from environment variables

2. **`requirements.txt`** - Updated with production dependencies:
   - `redis` - For session storage
   - `slowapi` - For rate limiting
   - `hiredis` - Faster Redis performance

3. **`setup_production.ps1`** - Automated setup script

### Documentation
1. **`PRODUCTION_READINESS.md`** - Complete checklist of production requirements
2. **`PRODUCTION_IMPLEMENTATION.md`** - Detailed implementation guide
3. **`AZURE_DEPLOYMENT.md`** - Step-by-step Azure deployment guide
4. **`FIX_SUMMARY.md`** - Summary of authentication fixes

---

## 🚀 Quick Start - Follow These Steps

### Step 1: Install Dependencies (5 minutes)

```powershell
# Run the setup script
.\setup_production.ps1

# Or manually:
pip install -r requirements.txt
```

### Step 2: Set Up Azure Redis (30 minutes)

```bash
# Create Redis cache
az redis create \
  --resource-group ingage-ai-rg \
  --name ingage-ai-redis \
  --location canadacentral \
  --sku Basic \
  --vm-size c0

# Get connection details
az redis show --name ingage-ai-redis --resource-group ingage-ai-rg
az redis list-keys --name ingage-ai-redis --resource-group ingage-ai-rg
```

**Cost**: ~$16/month

**Alternative for testing**: Use local Redis:
```powershell
docker run -d -p 6379:6379 redis:latest
$env:REDIS_URL="redis://localhost:6379/0"
```

### Step 3: Configure Azure App Service (15 minutes)

Go to Azure Portal → Your App Service → Configuration → Application settings

Add these:
```
REDIS_HOST = your-redis.redis.cache.windows.net
REDIS_PORT = 6380
REDIS_PASSWORD = <your-redis-primary-key>
REDIS_SSL = true
ENVIRONMENT = production
SESSION_EXPIRY_HOURS = 24
ALLOWED_ORIGINS = https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net
```

Keep existing:
```
TENANT_ID = 4d4eca3f-b031-47f1-8932-59112bf47e6b
DATA_AGENT_URL = https://api.fabric.microsoft.com/v1/workspaces/...
```

### Step 4: Deploy (20 minutes)

#### Option A: Replace and Deploy

```powershell
# Backup current version
copy main.py main_development.py

# Use production version
copy main_production.py main.py

# Commit and push
git add .
git commit -m "Production-ready deployment"
git push
```

#### Option B: Deploy Directly

```bash
cd "E:\Drive D\Personnal Source Code\Ingage AI Agent\ingage-ai-agent-api"
az webapp up --name ingage-ai-agent-api-c6f9htcfd3baa2b4 --resource-group ingage-ai-rg
```

### Step 5: Verify (15 minutes)

#### Test Health
```bash
curl https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net/health
```

Expected:
```json
{
  "status": "healthy",
  "environment": "production",
  "redis_connected": true,
  "fabric_client_initialized": true
}
```

#### Test from Frontend
1. Login with Microsoft
2. Send a query: "total plan count"
3. Should work! 🎉

#### Check Logs
```bash
az webapp log tail --name ingage-ai-agent-api-c6f9htcfd3baa2b4 --resource-group ingage-ai-rg
```

Should see:
```
✅ Redis connection successful
✅ Fabric Data Agent Client initialized
🔐 Client-side authentication successful
```

---

## 📊 What's Different in Production?

### Before (Development)
```python
# Sessions stored in memory
sessions = {}

# Prints instead of logging
print("User authenticated")

# Insecure cookies
response.set_cookie(key="session", value=session_id)

# No rate limiting
```

### After (Production)
```python
# Sessions stored in Redis (works with multiple instances)
redis_client.setex(f"session:{session_id}", ...)

# Structured logging with levels
logger.info("User authenticated: %s", user_email)

# Secure cookies
response.set_cookie(
    key="session",
    value=session_id,
    secure=True,  # HTTPS only
    httponly=True,  # No JavaScript access
    samesite="lax"  # CSRF protection
)

# Rate limiting (10 requests per minute)
@limiter.limit("10/minute")
async def query(...):
```

---

## ⚠️ Critical Differences

| Feature | Development | Production |
|---------|-------------|------------|
| **Sessions** | In-memory (single instance only) | Redis (multiple instances) |
| **Logging** | `print()` statements | Structured logging with levels |
| **Cookies** | Insecure | Secure, HttpOnly, SameSite |
| **CORS** | Hardcoded URLs | Environment variables |
| **Rate Limiting** | None | 10 requests/minute per IP |
| **Error Details** | Full stack traces | Sanitized errors |
| **Docs** | `/docs` enabled | Disabled for security |

---

## 🔒 Security Improvements

✅ **Session Security**
- Sessions stored in Redis with TTL (24 hours)
- Secure cookies (HTTPS only)
- HttpOnly (XSS protection)
- SameSite (CSRF protection)

✅ **Input Validation**
- Query length limited to 1000 characters
- Token format validation
- SQL injection prevention

✅ **Rate Limiting**
- 10 queries per minute per IP
- Prevents abuse and DDoS

✅ **Secrets Management**
- All secrets in Azure Configuration
- No hardcoded credentials
- Environment-based configuration

✅ **CORS**
- Specific origins only (no `*`)
- Credentials required
- From environment variables

---

## 📈 Scalability Improvements

✅ **Multi-Instance Support**
- Redis sessions work across all instances
- No sticky sessions needed
- Horizontal scaling ready

✅ **Connection Pooling**
- HTTP client reuses connections
- Reduces latency
- Better performance

✅ **Caching**
- Redis can cache frequent queries
- Reduces Fabric API calls
- Lower costs

---

## 🛠️ Troubleshooting

### Issue: "Redis connection failed"

**Solution**:
```bash
# Verify Redis is running
az redis show --name ingage-ai-redis --resource-group ingage-ai-rg --query provisioningState

# Check settings in App Service
az webapp config appsettings list --name ingage-ai-agent-api-c6f9htcfd3baa2b4 --resource-group ingage-ai-rg --query "[?name=='REDIS_HOST']"
```

### Issue: "Session not found"

**Causes**:
1. Redis not connected
2. Wrong Redis password
3. SSL not enabled

**Solution**:
```bash
# Verify all Redis settings
az webapp config appsettings list --name ingage-ai-agent-api-c6f9htcfd3baa2b4 --resource-group ingage-ai-rg --query "[?contains(name, 'REDIS')]"
```

### Issue: "Too many requests (429)"

**This is normal!** Rate limiting is working.

**To adjust**:
Edit `main_production.py`:
```python
@limiter.limit("20/minute")  # Increase from 10 to 20
async def simple_query(...):
```

---

## 💰 Cost Breakdown

### Current Setup
- App Service (B1): **~$13/month**
- Redis (C0 Basic): **~$16/month**
- **Total: ~$29/month**

### With Application Insights (Optional)
- Application Insights: **~$5-10/month**
- **Total: ~$34-39/month**

### Cost Optimization
- Use Free tier Redis for development
- Scale down App Service to Free tier when not in use
- Share Redis across multiple apps

---

## ✅ Production Checklist

### Must Have Before Going Live
- [ ] Redis configured and connected
- [ ] All secrets in Azure Configuration (not in code)
- [ ] Secure cookies enabled
- [ ] CORS configured with specific origins
- [ ] Health check passing
- [ ] Rate limiting enabled
- [ ] Structured logging enabled

### Strongly Recommended
- [ ] Application Insights configured
- [ ] Alerts set up for errors/downtime
- [ ] Staging environment created
- [ ] Backup/rollback plan tested

### Nice to Have
- [ ] CI/CD pipeline
- [ ] Automated testing
- [ ] Load testing completed
- [ ] Documentation updated

---

## 📚 Reference Documents

For more details, see:

1. **`PRODUCTION_READINESS.md`** - Full checklist
2. **`PRODUCTION_IMPLEMENTATION.md`** - Implementation details
3. **`AZURE_DEPLOYMENT.md`** - Complete deployment guide
4. **`main_production.py`** - Production code

---

## 🎉 Summary

**Your code is now production-ready with:**

✅ Redis session storage (multi-instance support)
✅ Structured logging (better debugging)
✅ Secure cookies (HTTPS, HttpOnly, SameSite)
✅ Rate limiting (prevent abuse)
✅ Environment-based configuration (no hardcoded secrets)
✅ Comprehensive error handling
✅ Health monitoring
✅ CORS security

**Next steps:**
1. Run `setup_production.ps1` to install dependencies
2. Follow `AZURE_DEPLOYMENT.md` to deploy
3. Test and verify

**Time to production: 1.5-2 hours**

Good luck! 🚀
