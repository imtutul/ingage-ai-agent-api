# Fabric Data Agent API Server

A comprehensive FastAPI server for Microsoft Fabric Data Agents with Azure AI Search integration, supporting multiple authentication methods and deployment options.

## 🚀 Overview

This project provides a production-ready REST API server that enables external applications to interact with Microsoft Fabric Data Agents and Azure AI Search services. It supports both local development and cloud deployment with comprehensive authentication options.

## ✨ Features

### Core Functionality
- 🔗 **Fabric Data Agent Integration** - Query your Fabric data agents via REST API
- 🔍 **Azure AI Search Integration** - Full-text and semantic search capabilities  
- 🌐 **FastAPI Server** - High-performance async API with automatic documentation
- 🔄 **Health Monitoring** - Built-in health checks and status endpoints

### Authentication Options
- �️ **Interactive Browser** - For local development and testing
- 🔐 **Service Principal** - For production Azure App Service deployment
- 🆔 **Managed Identity** - For Azure-native resource authentication
- 🎫 **Token Refresh** - Automatic token management and renewal

### Deployment Options
- 🌐 **Azure App Service** - Full web application hosting
- ⚡ **Azure Functions** - Serverless compute with individual functions
- 🏠 **Local Development** - Uvicorn server for testing

### Search Capabilities
- 📄 **Full-text Search** - Traditional keyword-based search
- � **Semantic Search** - AI-powered contextual search
- 💡 **Search Suggestions** - Auto-complete and query suggestions
- 🏷️ **Faceted Search** - Category-based filtering

## 📋 Requirements

- Python 3.7+
- Azure tenant with Fabric Data Agent access
- Azure AD App Registration (for service principal auth)
- Optional: Azure AI Search service

## 🔧 Quick Setup

### 1. Automated Azure AD Setup (Recommended)

Run the PowerShell setup script to automatically create your Azure AD App Registration:

```powershell
# Run the automated setup script
.\setup-azure-ad.ps1

# Follow the prompts to create Azure AD App Registration
# This will generate a .env.generated file with your credentials
```

### 2. Manual Setup

If you prefer manual setup, follow the detailed guide:

```bash
# See detailed instructions
cat SERVICE_PRINCIPAL_SETUP.md
```

### 3. Environment Configuration

```bash
# Copy the generated environment file
cp .env.generated .env

# Update with your Fabric workspace details
# Edit DATA_AGENT_URL with your actual workspace and skill IDs
```

## ⚙️ Installation

1. Clone this repository:

```bash
git clone <repository-url>
cd ingage-ai-agent-api
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## 🔑 Authentication Setup

### For Azure App Service Deployment (Production)

You need to set up service principal authentication to avoid the 503 errors in Azure App Service:

## 🔑 Authentication Setup

### For Azure App Service Deployment (Production)

You need to set up service principal authentication to avoid the 503 errors in Azure App Service:

**Option 1: Use the Automated Setup Script**
```powershell
# This creates Azure AD App Registration and generates .env file
.\setup-azure-ad.ps1
```

**Option 2: Manual Setup**
```bash
# Follow the detailed step-by-step guide
cat SERVICE_PRINCIPAL_SETUP.md
```

**Option 3: Quick Manual Configuration**
```env
# Create .env file with these values
TENANT_ID=your-azure-tenant-id
CLIENT_ID=your-azure-app-registration-client-id  
CLIENT_SECRET=your-azure-app-registration-secret
DATA_AGENT_URL=https://api.fabric.microsoft.com/v1/workspaces/YOUR_WORKSPACE_ID/aiskills/YOUR_SKILL_ID/aiassistant/openai
```

### For Local Development

```env
# For local testing, you can use interactive authentication
TENANT_ID=your-azure-tenant-id
DATA_AGENT_URL=your-fabric-data-agent-url
# CLIENT_ID and CLIENT_SECRET are optional for local development
```

### For Azure AI Search (Optional)

```env
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-admin-key
AZURE_SEARCH_INDEX=your-search-index-name
```

## 🧪 Testing Your Setup

Test your authentication configuration before deploying:

```bash
# Run the comprehensive test suite
python test_service_principal.py
```

This will verify:
- ✅ Environment variables are set correctly
- ✅ Azure credentials work
- ✅ Token acquisition succeeds  
- ✅ Fabric client initializes
- ✅ Fabric queries work

## 🚀 Running the Server

### Local Development

```bash
# Start the development server
python start_server.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Production (Azure App Service)

```bash
# The server will automatically use Gunicorn in production
# Configure these environment variables in Azure App Service:
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
DATA_AGENT_URL=your-fabric-url
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
# Returns server status and client initialization status
```

### Fabric Data Agent Queries
```bash
# Simple query
POST /query
{
  "query": "What data is available in our sales database?"
}

# Detailed query with run information
POST /query/detailed  
{
  "query": "Show me the top 10 customers by revenue",
  "timeout": 60
}
```

### Azure AI Search
```bash
# Simple search
POST /search
{
  "query": "customer data",
  "top": 10
}

# Semantic search
POST /search/semantic
{
  "query": "find information about customer satisfaction",
  "top": 5
}

# Search suggestions
GET /search/suggest?query=cust&top=5

# Search autocomplete
GET /search/autocomplete?query=customer&top=8
```

## 🌐 API Documentation

When the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐳 Deployment Options

### Option 1: Azure App Service (Recommended)

```bash
# Deploy using Azure CLI
az webapp up --name your-app-name --resource-group your-rg --runtime PYTHON:3.11

# Configure environment variables
az webapp config appsettings set --resource-group your-rg --name your-app-name --settings \
  TENANT_ID="your-tenant-id" \
  CLIENT_ID="your-client-id" \
  CLIENT_SECRET="your-client-secret" \
  DATA_AGENT_URL="your-fabric-url"
```

### Option 2: Azure Functions (Serverless)

```bash
# Deploy the Functions version
cd azure_functions
func azure functionapp publish your-function-app-name
```

## 📁 Project Structure

```
ingage-ai-agent-api/
├── main.py                          # FastAPI application
├── fabric_data_agent_client.py      # Enhanced Fabric client with auth options
├── azure_search_client.py           # Azure AI Search integration
├── start_server.py                  # Development server launcher
├── test_service_principal.py        # Authentication testing script
├── setup-azure-ad.ps1              # Automated Azure AD setup
├── SERVICE_PRINCIPAL_SETUP.md       # Detailed setup guide
├── requirements.txt                 # Python dependencies
├── .env                            # Environment configuration
├── azure_functions/                # Azure Functions version
│   ├── health/                     # Health check function
│   ├── fabric_query/              # Fabric query function  
│   ├── search/                    # Search function
│   └── shared_clients.py          # Shared client management
└── docs/                          # Additional documentation
```

### Option 2: .env File

Create a `.env` file in the project directory:

```env
TENANT_ID=<your-azure-tenant-id>
DATA_AGENT_URL=<your-fabric-data-agent-url>
```

### Option 3: Direct Configuration

Edit the values directly in your script:

```python
TENANT_ID = "<your-azure-tenant-id>"
DATA_AGENT_URL = "<your-fabric-data-agent-url>"
```

## Usage

### Basic Usage

```python
from fabric_data_agent_client import FabricDataAgentClient

# Initialize the client (will open browser for authentication)
client = FabricDataAgentClient(
    tenant_id="your-tenant-id",
    data_agent_url="your-data-agent-url"
)

# Ask a simple question
response = client.ask("What data is available in the lakehouse?")
print(response)
```

### Getting Detailed Run Information with SQL Query Extraction

```python
# Get detailed run information including steps and SQL queries for lakehouse data sources
run_details = client.get_run_details("What are the top 5 records from any table?")

print(f"Run Status: {run_details['run_status']}")
print(f"Steps Count: {len(run_details['run_steps']['data'])}")

# Check if SQL queries were extracted (indicates lakehouse data source)
if "sql_queries" in run_details and run_details["sql_queries"]:
    print("Lakehouse Data Source Detected!")
    
    # Show which query retrieved the data and preview the results
    if "data_retrieval_query" in run_details:
        print(f"Data Retrieved By: {run_details['data_retrieval_query']}")
        
        # Show data preview
        if "sql_data_previews" in run_details:
            preview = run_details["sql_data_previews"][0]  # First preview
            if preview:
                print("Data Preview:")
                for line in preview[:5]:
                    print(f"  {line}")
    
    # Optional: Show all SQL queries executed
    # for i, query in enumerate(run_details['sql_queries'], 1):
    #     print(f"  {i}. {query}")
```

### Running the Examples

The project includes example scripts you can run:

```bash
# Run the main example
python fabric_data_agent_client.py

# Run the simple usage example
python example_usage.py
```

## API Reference

### FabricDataAgentClient

#### `__init__(tenant_id: str, data_agent_url: str)`

Initialize the client with your Azure tenant ID and Fabric Data Agent URL.

#### `ask(question: str, timeout: int = 120) -> str`

Ask a question to the data agent.

- **question**: The question to ask
- **timeout**: Maximum time to wait for response in seconds
- **Returns**: The response from the data agent

#### `get_run_details(question: str) -> dict`

Ask a question and return detailed run information including steps, SQL queries, and data previews if lakehouse data source is used.

- **question**: The question to ask
- **Returns**: Detailed response including:
  - `run_steps`: Execution steps and metadata  
  - `sql_queries`: List of SQL queries executed (if lakehouse data source)
  - `sql_data_previews`: Preview of data returned by queries
  - `data_retrieval_query`: The specific SQL query that retrieved the main data
  - `data_retrieval_query_index`: Index of the data retrieval query in the queries list

## Authentication Flow

1. When you initialize the client, it will automatically open your default browser
2. Sign in with your Microsoft account that has access to the Fabric environment
3. Grant permissions when prompted
4. The client will automatically obtain and manage the authentication token
5. Tokens are automatically refreshed before expiration

## Error Handling

The client includes comprehensive error handling for common scenarios:

- Invalid configuration (missing tenant ID or data agent URL)
- Authentication failures
- Network timeouts
- API errors
- Token expiration and refresh issues

All errors are logged with helpful messages and troubleshooting tips.

## Troubleshooting

### Common Issues

#### Authentication Fails

- Ensure your Azure account has access to the Fabric environment
- Check that your tenant ID is correct
- Verify you have permissions to access the specific data agent

#### Data Agent Not Responding

- Verify the data agent URL is correct and published
- Check if the data agent is running and accessible
- Ensure your Azure account has permissions to call the data agent

#### Dependency Issues

- Make sure all required packages are installed: `pip install -r requirements.txt`
- Update to the latest versions if you encounter compatibility issues

#### Timeout Issues

- Increase the timeout parameter for complex queries
- Check if your data agent has sufficient resources allocated

### Getting Help

1. Check the error messages - they include specific troubleshooting tips
2. Verify your configuration values are correct
3. Ensure you have the necessary Azure permissions
4. Test with simple queries first before trying complex ones

## Dependencies

- **azure-identity**: Handles Azure AD authentication
- **openai**: Provides the API client for interacting with the data agent
- **python-dotenv**: Optional, for loading environment variables from .env files

## Security Notes

- Authentication tokens are handled securely and automatically refreshed
- No credentials are stored persistently
- Interactive browser authentication ensures secure login
- Bearer tokens are used for API authentication
- Resources are properly cleaned up after each request

## License

This project is provided as-is for educational and development purposes. Please ensure you comply with Microsoft's terms of service when using Fabric Data Agents.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this client.

## Changelog

### v1.0.0

- Initial release
- Interactive browser authentication
- Basic question/answer functionality
- Detailed run information
- Automatic token refresh
- Resource cleanup
- Comprehensive error handling
