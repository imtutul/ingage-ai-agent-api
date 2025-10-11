# Fabric Data Agent FastAPI Server

A REST API server that provides endpoints to interact with Microsoft Fabric Data Agents from external applications.

## Features

- 🔌 **Simple Query Endpoint**: Get quick responses from your data agent
- 📊 **Detailed Query Endpoint**: Get responses with run details, SQL queries, and data previews
- 🔍 **Health Check**: Monitor server and client status
- 🔒 **Azure Authentication**: Secure access using Azure AD
- 📚 **Interactive Documentation**: Auto-generated API docs with Swagger UI

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure your values:

```bash
copy .env.example .env
```

Edit `.env` and set your actual values:

```env
TENANT_ID=your-azure-tenant-id
DATA_AGENT_URL=your-fabric-data-agent-url
```

### 3. Start the Server

#### Option A: Using the startup script (recommended)
```bash
python start_server.py
```

#### Option B: Using uvicorn directly
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option C: Using Python directly
```bash
python main.py
```

### 4. Access the API

- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Health Check
```http
GET /health
```

Returns server status and Fabric client initialization status.

### Simple Query
```http
POST /query
Content-Type: application/json

{
  "query": "What data is available in the lakehouse?"
}
```

Returns a simple response from the data agent.

### Detailed Query
```http
POST /query/detailed
Content-Type: application/json

{
  "query": "Show me the top 5 records from any table",
  "include_details": true
}
```

Returns response with additional details:
- Run status and step count
- SQL queries used
- Data previews
- Message count

## Example Usage

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Simple query
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What tables are available?"}'

# Detailed query
curl -X POST "http://localhost:8000/query/detailed" \
     -H "Content-Type: application/json" \
     -d '{"query": "Show me data from the sales table"}'
```

### Using Python Requests

```python
import requests

# Simple query
response = requests.post(
    "http://localhost:8000/query",
    json={"query": "What data is available?"}
)
data = response.json()
print(data["response"])

# Detailed query
response = requests.post(
    "http://localhost:8000/query/detailed", 
    json={"query": "Show me the latest records"}
)
data = response.json()
print(f"SQL: {data['sql_query']}")
print(f"Data: {data['data_preview']}")
```

### Using the Test Client

Run the included test client to verify everything works:

```bash
python test_client.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TENANT_ID` | Yes | Your Azure AD tenant ID |
| `DATA_AGENT_URL` | Yes | Your Fabric Data Agent endpoint URL |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 8000) |
| `RELOAD` | No | Enable auto-reload (default: true) |
| `LOG_LEVEL` | No | Logging level (default: info) |

## Getting Your Configuration Values

### Tenant ID
1. Go to Azure Portal → Azure Active Directory → Properties
2. Copy the "Tenant ID" (Directory ID)

### Data Agent URL
1. Go to Microsoft Fabric → Your workspace → Data Science → AI Skills
2. Find your data agent and get the API endpoint
3. Format: `https://api.fabric.microsoft.com/v1/workspaces/{workspace-id}/aiskills/{skill-id}/aiassistant/openai`

## Authentication

The server uses Azure Interactive Browser Credential for authentication. When you first start the server:

1. It will attempt to authenticate with Azure AD
2. A browser window will open for you to sign in
3. Once authenticated, the token will be cached for subsequent requests

Make sure your Azure account has access to the Fabric Data Agent you're trying to use.

## Error Handling

The API includes comprehensive error handling:

- **503 Service Unavailable**: Fabric client not initialized
- **400 Bad Request**: Invalid query format
- **500 Internal Server Error**: Authentication or data agent errors

All error responses include descriptive error messages to help with troubleshooting.

## Development

### Running in Development Mode

```bash
python start_server.py
```

This enables:
- Auto-reload on code changes
- Detailed logging
- CORS enabled for all origins

### Production Deployment

For production, consider:

1. Setting `RELOAD=false`
2. Configuring specific CORS origins
3. Using a production ASGI server like Gunicorn
4. Setting up proper logging and monitoring
5. Using environment-specific configuration

```bash
# Example production command
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Troubleshooting

### Common Issues

1. **"Fabric Data Agent client not initialized"**
   - Check your `.env` file configuration
   - Verify TENANT_ID and DATA_AGENT_URL are correct
   - Ensure you have access to the Fabric workspace

2. **Authentication failures**
   - Verify your Azure account has the necessary permissions
   - Check that the tenant ID is correct
   - Try clearing browser cache if authentication seems stuck

3. **Import errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're using the correct Python environment

4. **Port already in use**
   - Change the port: `PORT=8001 python start_server.py`
   - Or stop the conflicting process

### Logs

Check the server logs for detailed error information. The server logs include:
- Authentication status
- Query processing details
- Error messages with stack traces

## License

This project is licensed under the MIT License - see the LICENSE file for details.