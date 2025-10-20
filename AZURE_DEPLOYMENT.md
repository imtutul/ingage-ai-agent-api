# 🚀 Azure Production Deployment Guide

## Complete step-by-step guide to deploy your Fabric Data Agent API to Azure

---

## Prerequisites

- [ ] Azure subscription
- [ ] Azure CLI installed (`az --version`)
- [ ] Git repository set up
- [ ] Code tested locally

---

## Part 1: Set Up Azure Cache for Redis (30 minutes)

### Step 1: Create Redis Cache

```bash
# Set variables
RESOURCE_GROUP="ingage-ai-rg"
REDIS_NAME="ingage-ai-redis"
LOCATION="canadacentral"

# Create Redis cache (Basic C0 - smallest, ~$16/month)
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0
```

This takes ~10-15 minutes. While it's creating, continue to Step 2.

### Step 2: Get Redis Connection Info (after creation completes)

```bash
# Get Redis hostname
REDIS_HOST=$(az redis show \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query hostName -o tsv)

# Get Redis primary key
REDIS_KEY=$(az redis list-keys \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query primaryKey -o tsv)

echo "Redis Host: $REDIS_HOST"
echo "Redis Key: $REDIS_KEY"
```

Save these values - you'll need them later!

---

## Part 2: Configure App Service (15 minutes)

### Step 1: Update App Service Configuration

```bash
# Set variables
APP_NAME="ingage-ai-agent-api-c6f9htcfd3baa2b4"

# Configure Redis
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    REDIS_HOST="$REDIS_HOST" \
    REDIS_PORT="6380" \
    REDIS_PASSWORD="$REDIS_KEY" \
    REDIS_SSL="true"

# Configure environment
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    ENVIRONMENT="production" \
    SESSION_EXPIRY_HOURS="24"

# Configure CORS
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    ALLOWED_ORIGINS="https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net"

# Your existing settings (keep these)
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    TENANT_ID="4d4eca3f-b031-47f1-8932-59112bf47e6b" \
    DATA_AGENT_URL="https://api.fabric.microsoft.com/v1/workspaces/d09dbe6d-b3f5-4188-a375-482e01aa1213/aiskills/731c5acd-dbd7-4881-94f4-13ecf0d39c49/aiassistant/openai"
```

### Step 2: Verify Configuration

```bash
# List all settings
az webapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table
```

---

## Part 3: Deploy Code (20 minutes)

### Option A: Deploy from GitHub (Recommended)

```bash
# Link to GitHub repo
az webapp deployment source config \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --repo-url https://github.com/imtutul/fabric_data_agent_client \
  --branch main \
  --manual-integration

# Trigger deployment
az webapp deployment source sync \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### Option B: Deploy from Local

```bash
# Navigate to project directory
cd "E:\Drive D\Personnal Source Code\Ingage AI Agent\ingage-ai-agent-api"

# Replace main.py with production version
copy main_production.py main.py

# Deploy using az webapp up
az webapp up \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --runtime "PYTHON:3.11" \
  --sku B1
```

### Step 3: Install Dependencies

The App Service will automatically:
1. Detect `requirements.txt`
2. Install all dependencies
3. Start the application

Monitor in Azure Portal → App Service → Deployment Center

---

## Part 4: Verification & Testing (15 minutes)

### Step 1: Check Health Endpoint

```bash
# Check health
curl https://ingage-ai-agent-api-c6f9htcfd3baa2b4.canadacentral-01.azurewebsites.net/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production",
  "fabric_client_initialized": true,
  "redis_connected": true,
  "tenant_id": "4d4eca3f..."
}
```

### Step 2: Test Authentication

From your frontend, try to login. Check logs:

```bash
# View live logs
az webapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP
```

Should see:
```
✅ Redis connection successful
✅ Fabric Data Agent Client initialized
🔐 Client-side authentication - validating token...
✅ Client-side authentication successful: user@email.com
```

### Step 3: Test Query

From your frontend, try a query like "total plan count".

Should see in logs:
```
📝 Processing query from user@email.com: total plan count
✅ Query successful
```

---

## Part 5: Monitor & Troubleshoot (Ongoing)

### View Logs

```bash
# Live log stream
az webapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

# Download logs
az webapp log download \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --log-file app_logs.zip
```

### Check Metrics

```bash
# View metrics in Azure Portal
# Go to: App Service → Metrics
# Monitor:
# - Response time
# - Request count
# - Errors
# - Memory/CPU usage
```

### Common Issues

#### Issue: "Redis connection failed"

```bash
# Check Redis status
az redis show \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query provisioningState

# Should show: "Succeeded"

# Test Redis connectivity
az redis ping \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP
```

#### Issue: "Session not found"

Check that:
1. Redis is running
2. `REDIS_HOST`, `REDIS_PASSWORD` are set correctly
3. `REDIS_SSL=true` is set

```bash
# Verify settings
az webapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='REDIS_HOST' || name=='REDIS_PASSWORD' || name=='REDIS_SSL']"
```

#### Issue: "CORS error"

```bash
# Verify ALLOWED_ORIGINS
az webapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='ALLOWED_ORIGINS']"

# Update if needed
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    ALLOWED_ORIGINS="https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net"
```

---

## Part 6: Enable Application Insights (Optional but Recommended)

### Step 1: Create Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app ingage-ai-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --application-type web

# Get instrumentation key
APPINSIGHTS_KEY=$(az monitor app-insights component show \
  --app ingage-ai-insights \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey -o tsv)

echo "Application Insights Key: $APPINSIGHTS_KEY"
```

### Step 2: Configure App Service

```bash
# Link Application Insights
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    APPINSIGHTS_INSTRUMENTATIONKEY="$APPINSIGHTS_KEY" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=$APPINSIGHTS_KEY"
```

### Step 3: Install opencensus-ext-azure

Add to `requirements.txt`:
```
opencensus-ext-azure>=1.1.9
opencensus-ext-flask>=0.8.1
```

Redeploy the application.

---

## Cost Estimation

### Monthly Costs (Canada Central region)

| Service | SKU | Cost/Month (USD) |
|---------|-----|------------------|
| App Service | B1 (Basic) | ~$13 |
| Azure Cache for Redis | C0 (Basic) | ~$16 |
| Application Insights | Pay-as-you-go | ~$5-10 (low traffic) |
| **Total** | | **~$34-39/month** |

### Cost Optimization

To reduce costs:

1. **Redis**: Use shared Redis if you have other apps
2. **App Service**: Scale down to Free/Shared tier during development
3. **Application Insights**: Set sampling to reduce data ingestion

---

## Security Checklist

- [ ] All secrets in Azure Configuration (not in code)
- [ ] HTTPS enabled (default for Azure App Service)
- [ ] Redis SSL enabled
- [ ] CORS configured with specific origins (not `*`)
- [ ] Secure cookies enabled (`secure=True`)
- [ ] Rate limiting enabled
- [ ] Application Insights connected
- [ ] Regular security updates

---

## Rollback Plan

If deployment fails:

### Option 1: Redeploy Previous Version

```bash
# In Azure Portal:
# App Service → Deployment Center → Logs
# Find last successful deployment
# Click "Redeploy"
```

### Option 2: Revert Code

```bash
# Revert git commit
git revert HEAD
git push

# Azure will auto-deploy if CI/CD is set up
```

---

## Next Steps

1. ✅ Set up Application Insights (Part 6)
2. ✅ Configure alerts for errors/downtime
3. ✅ Set up automated backups
4. ✅ Create staging environment
5. ✅ Set up CI/CD pipeline

---

## Summary

**Total Time:** ~1.5-2 hours

**What You've Done:**
- ✅ Set up Redis for distributed sessions
- ✅ Configured production environment
- ✅ Deployed production-ready code
- ✅ Verified everything works
- ✅ Set up monitoring

**Your API is now production-ready!** 🎉
