#!/bin/bash

# Azure Functions Deployment Script
# Run this script to deploy your Function App to Azure

set -e

# Configuration
RESOURCE_GROUP="your-resource-group"
FUNCTION_APP_NAME="your-function-app-name" 
LOCATION="East US"
STORAGE_ACCOUNT="yourstorageaccount"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Azure Functions deployment...${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Login check
echo -e "${YELLOW}📋 Checking Azure CLI login...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}🔐 Please login to Azure...${NC}"
    az login
fi

# Create resource group if it doesn't exist
echo -e "${YELLOW}📦 Creating resource group if needed...${NC}"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

# Create storage account
echo -e "${YELLOW}💾 Creating storage account...${NC}"
az storage account create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$STORAGE_ACCOUNT" \
    --location "$LOCATION" \
    --sku Standard_LRS

# Create Function App
echo -e "${YELLOW}⚡ Creating Function App...${NC}"
az functionapp create \
    --resource-group "$RESOURCE_GROUP" \
    --consumption-plan-location "$LOCATION" \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --name "$FUNCTION_APP_NAME" \
    --storage-account "$STORAGE_ACCOUNT"

# Configure app settings
echo -e "${YELLOW}⚙️  Configuring application settings...${NC}"
echo "Please configure these settings in Azure Portal or using Azure CLI:"
echo "- TENANT_ID"
echo "- DATA_AGENT_URL" 
echo "- CLIENT_ID"
echo "- CLIENT_SECRET"
echo "- AZURE_SEARCH_ENDPOINT"
echo "- AZURE_SEARCH_INDEX_NAME"
echo "- AZURE_SEARCH_API_KEY"

# Deploy function code
echo -e "${YELLOW}📦 Deploying function code...${NC}"
func azure functionapp publish "$FUNCTION_APP_NAME" --python

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo -e "${GREEN}🌐 Function App URL: https://${FUNCTION_APP_NAME}.azurewebsites.net${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Configure environment variables in Azure Portal"
echo "2. Test the health endpoint: https://${FUNCTION_APP_NAME}.azurewebsites.net/api/health"
echo "3. Monitor logs in Azure Portal or using 'func azure functionapp logstream ${FUNCTION_APP_NAME}'"
