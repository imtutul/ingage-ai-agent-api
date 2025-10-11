#!/usr/bin/env python3
"""
FastAPI server for Fabric Data Agent Client

This FastAPI application provides REST endpoints to interact with Microsoft Fabric Data Agents.
It handles user queries and returns structured responses from the data agent.
"""

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file if present
import os
import asyncio
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from fabric_data_agent_client import FabricDataAgentClient

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Global client instance
fabric_client: Optional[FabricDataAgentClient] = None

# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for data agent queries"""
    query: str = Field(..., description="The question or query to ask the data agent", min_length=1)
    include_details: bool = Field(default=False, description="Whether to include detailed run information")

class QueryResponse(BaseModel):
    """Response model for simple queries"""
    success: bool = Field(..., description="Whether the query was successful")
    response: str = Field(..., description="The data agent's response")
    query: str = Field(..., description="The original query")
    error: Optional[str] = Field(None, description="Error message if query failed")

class DetailedQueryResponse(BaseModel):
    """Response model for detailed queries with run information"""
    success: bool = Field(..., description="Whether the query was successful")
    response: str = Field(..., description="The data agent's response")
    query: str = Field(..., description="The original query")
    run_status: Optional[str] = Field(None, description="Status of the data agent run")
    steps_count: Optional[int] = Field(None, description="Number of steps in the run")
    messages_count: Optional[int] = Field(None, description="Number of messages in the run")
    sql_query: Optional[str] = Field(None, description="SQL query used for data retrieval")
    data_preview: Optional[List[str]] = Field(None, description="Preview of retrieved data")
    error: Optional[str] = Field(None, description="Error message if query failed")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    fabric_client_initialized: bool = Field(..., description="Whether Fabric client is ready")
    tenant_id: Optional[str] = Field(None, description="Configured tenant ID")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global fabric_client
    
    # Startup: Initialize Fabric client
    print("🚀 Initializing Fabric Data Agent Client...")
    
    tenant_id = os.getenv("TENANT_ID")
    data_agent_url = os.getenv("DATA_AGENT_URL")
    
    # if not tenant_id or not data_agent_url:
    #     print("❌ Error: TENANT_ID and DATA_AGENT_URL must be set in environment variables")
    #     raise RuntimeError("Missing required environment variables")
    
    # # Check for placeholder values
    # if tenant_id == "4d4eca3f-b031-47f1-8932-59112bf47e6b" or "4d4eca3f-b031-47f1-8932-59112bf47e6b" in tenant_id.lower():
    #     print("❌ Error: Please set your actual TENANT_ID in the .env file")
    #     raise RuntimeError("TENANT_ID contains placeholder value")
    
    # if "https://api.fabric.microsoft.com/v1/workspaces/d09dbe6d-b3f5-4188-a375-482e01aa1213/aiskills/a2e01f9d-4d21-4d87-af2c-5f35a9edae9b/aiassistant/openai" in data_agent_url.lower():
    #     print("❌ Error: Please set your actual DATA_AGENT_URL in the .env file")
    #     raise RuntimeError("DATA_AGENT_URL contains placeholder value")
    
    try:
        fabric_client = FabricDataAgentClient(
            tenant_id=tenant_id,
            data_agent_url=data_agent_url
        )
        print("✅ Fabric Data Agent Client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Fabric client: {e}")
        raise RuntimeError(f"Failed to initialize Fabric client: {e}")
    
    yield
    
    # Cleanup
    print("🧹 Cleaning up resources...")
    fabric_client = None

# Create FastAPI app
app = FastAPI(
    title="Fabric Data Agent API",
    description="REST API for querying Microsoft Fabric Data Agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if fabric_client else "unhealthy",
        fabric_client_initialized=fabric_client is not None,
        tenant_id=os.getenv("TENANT_ID", "not_set")[:8] + "..." if os.getenv("TENANT_ID") else None
    )

@app.post("/query", response_model=QueryResponse)
async def simple_query(request: QueryRequest):
    """
    Simple query endpoint that returns just the data agent's response
    """
    if not fabric_client:
        raise HTTPException(status_code=503, detail="Fabric Data Agent client not initialized")
    
    try:
        print(f"📝 Processing query: {request.query}")
        response = fabric_client.ask(request.query)
        
        return QueryResponse(
            success=True,
            response=response,
            query=request.query
        )
    
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return QueryResponse(
            success=False,
            response="",
            query=request.query,
            error=str(e)
        )

@app.post("/query/detailed", response_model=DetailedQueryResponse)
async def detailed_query(request: QueryRequest):
    """
    Detailed query endpoint that returns response plus run details, SQL queries, and data previews
    """
    if not fabric_client:
        raise HTTPException(status_code=503, detail="Fabric Data Agent client not initialized")
    
    try:
        print(f"📝 Processing detailed query: {request.query}")
        run_details = fabric_client.get_run_details(request.query)
        
        if "error" in run_details:
            return DetailedQueryResponse(
                success=False,
                response="",
                query=request.query,
                error=run_details["error"]
            )
        
        # Extract the assistant's response
        response_text = ""
        messages = run_details.get('messages', {}).get('data', [])
        assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
        
        if assistant_messages:
            latest_message = assistant_messages[-1]
            content = latest_message.get('content', [])
            if content and len(content) > 0:
                # Handle different content types
                if hasattr(content[0], 'text'):
                    response_text = content[0].text.value
                elif isinstance(content[0], dict) and 'text' in content[0]:
                    if isinstance(content[0]['text'], dict) and 'value' in content[0]['text']:
                        response_text = content[0]['text']['value']
                    else:
                        response_text = content[0]['text']
                else:
                    response_text = str(content[0])
        
        # Extract data preview
        data_preview = None
        if "sql_data_previews" in run_details and run_details["sql_data_previews"]:
            data_retrieval_index = run_details.get("data_retrieval_query_index", 1) - 1
            if 0 <= data_retrieval_index < len(run_details["sql_data_previews"]):
                preview = run_details["sql_data_previews"][data_retrieval_index]
                if preview:
                    # Handle raw markdown tables
                    if len(preview) == 1 and '\n' in preview[0] and '|' in preview[0]:
                        data_preview = preview[0].split('\n')
                    else:
                        data_preview = preview[:10]  # Limit to first 10 lines
        
        return DetailedQueryResponse(
            success=True,
            response=response_text,
            query=request.query,
            run_status=run_details.get('run_status'),
            steps_count=len(run_details.get('run_steps', {}).get('data', [])),
            messages_count=len(messages),
            sql_query=run_details.get('data_retrieval_query'),
            data_preview=data_preview
        )
    
    except Exception as e:
        print(f"❌ Detailed query failed: {e}")
        return DetailedQueryResponse(
            success=False,
            response="",
            query=request.query,
            error=str(e)
        )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Fabric Data Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "simple_query": "/query",
            "detailed_query": "/query/detailed",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

if __name__ == "__main__":
    # For development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )