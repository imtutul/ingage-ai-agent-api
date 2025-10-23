#!/usr/bin/env python3
"""
FastAPI server for Fabric Data Agent Client - PRODUCTION VERSION

This FastAPI application provides REST endpoints to interact with Microsoft Fabric Data Agents.
Includes production-ready features:
- Redis session storage
- Structured logging
- Secure cookies
- Rate limiting
- Application Insights integration
"""

from dotenv import load_dotenv
load_dotenv()

import os
import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Cookie, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fabric_data_agent_client import FabricDataAgentClient

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO if os.getenv("ENVIRONMENT") != "production" else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Session configuration
SESSION_COOKIE_NAME = "fabric_session_id"
SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))

# CORS configuration
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:4200,https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net"
).split(",")

logger.info(f"Starting Fabric Data Agent API - Environment: {ENVIRONMENT}")
logger.info(f"Allowed CORS origins: {ALLOWED_ORIGINS}")

# ============================================================================
# Redis Session Storage
# ============================================================================

try:
    import redis
    
    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL")
    if REDIS_URL:
        # Use Redis URL (for development)
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    else:
        # Use individual parameters (for Azure Cache for Redis)
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
            decode_responses=True
        )
    
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis connection successful")
    USE_REDIS = True
    
except (ImportError, Exception) as e:
    logger.warning(f"⚠️ Redis not available, using in-memory sessions: {e}")
    logger.warning("⚠️ WARNING: In-memory sessions will NOT work with multiple instances!")
    redis_client = None
    USE_REDIS = False
    
    # Fallback to in-memory (NOT recommended for production)
    sessions: Dict[str, Dict[str, Any]] = {}

# ============================================================================
# Rate Limiting
# ============================================================================

limiter = Limiter(key_func=get_remote_address)

# ============================================================================
# Global Variables
# ============================================================================

fabric_client: Optional[FabricDataAgentClient] = None

# ============================================================================
# Pydantic Models
# ============================================================================

class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

class QueryRequest(BaseModel):
    """Request model for data agent queries"""
    query: str = Field(..., description="The question or query to ask the data agent", min_length=1, max_length=1000)
    include_details: bool = Field(default=False, description="Whether to include detailed run information")
    conversation_history: Optional[List[ConversationMessage]] = Field(default=None, description="Previous conversation history for context")

class QueryResponse(BaseModel):
    """Response model for simple queries"""
    success: bool = Field(..., description="Whether the query was successful")
    response: str = Field(..., description="The data agent's response")
    query: str = Field(..., description="The original query")
    error: Optional[str] = Field(None, description="Error message if query failed")

class DetailedQueryResponse(BaseModel):
    """Response model for detailed queries"""
    success: bool = Field(..., description="Whether the query was successful")
    response: str = Field(..., description="The data agent's response")
    query: str = Field(..., description="The original query")
    run_status: Optional[str] = Field(None, description="Status of the data agent run")
    steps_count: Optional[int] = Field(None, description="Number of steps in the run")
    messages_count: Optional[int] = Field(None, description="Number of messages in the run")
    sql_query: Optional[str] = Field(None, description="SQL query used")
    data_preview: Optional[List[str]] = Field(None, description="Preview of data")
    error: Optional[str] = Field(None, description="Error message if query failed")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    environment: str = Field(..., description="Environment name")
    fabric_client_initialized: bool = Field(..., description="Whether Fabric client is ready")
    redis_connected: bool = Field(..., description="Whether Redis is connected")
    tenant_id: Optional[str] = Field(None, description="Configured tenant ID (masked)")

class AuthStatusResponse(BaseModel):
    """Authentication status response"""
    authenticated: bool = Field(..., description="Whether user is authenticated")
    user: Optional[Dict[str, Any]] = Field(None, description="User information if authenticated")

class AuthResponse(BaseModel):
    """Authentication action response"""
    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Status message")
    user: Optional[Dict[str, Any]] = Field(None, description="User information if authenticated")

class UserDetailsResponse(BaseModel):
    """User details response"""
    success: bool = Field(..., description="Whether the request was successful")
    user: Optional[Dict[str, Any]] = Field(None, description="User information")
    error: Optional[str] = Field(None, description="Error message if request failed")

class ClientAuthRequest(BaseModel):
    """Request model for client-side authentication"""
    access_token: str = Field(..., description="Access token (Graph or Fabric)", min_length=1)
    fabric_token: Optional[str] = Field(None, description="Fabric API token (if separate)", min_length=1)

# ============================================================================
# Session Management Functions
# ============================================================================

def create_session(user_data: dict, access_token: str = None) -> str:
    """Create a new session and return session ID"""
    session_id = str(uuid.uuid4())
    now = datetime.now()
    
    session_data = {
        "authenticated": True,
        "user": user_data,
        "access_token": access_token,
        "created_at": now.isoformat(),
        "last_accessed": now.isoformat()
    }
    
    if USE_REDIS and redis_client:
        # Store in Redis with expiration
        redis_client.setex(
            f"session:{session_id}",
            SESSION_EXPIRY_HOURS * 3600,
            json.dumps(session_data)
        )
        logger.info(f"Session created in Redis: {session_id[:8]}... for user {user_data.get('email')}")
    else:
        # Fallback to in-memory
        sessions[session_id] = {
            **session_data,
            "created_at": now,
            "last_accessed": now
        }
        logger.info(f"Session created in memory: {session_id[:8]}... for user {user_data.get('email')}")
    
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session data by ID"""
    if not session_id:
        return None
    
    if USE_REDIS and redis_client:
        try:
            session_json = redis_client.get(f"session:{session_id}")
            if session_json:
                session_data = json.loads(session_json)
                # Update last accessed
                session_data["last_accessed"] = datetime.now().isoformat()
                redis_client.setex(
                    f"session:{session_id}",
                    SESSION_EXPIRY_HOURS * 3600,
                    json.dumps(session_data)
                )
                return session_data
        except Exception as e:
            logger.error(f"Error retrieving session from Redis: {e}")
            return None
    else:
        # Fallback to in-memory
        session = sessions.get(session_id)
        if session:
            # Check expiration
            expiry_time = session["created_at"] + timedelta(hours=SESSION_EXPIRY_HOURS)
            if datetime.now() > expiry_time:
                del sessions[session_id]
                return None
            session["last_accessed"] = datetime.now()
            return session
    
    return None

def delete_session(session_id: str) -> bool:
    """Delete a session"""
    if not session_id:
        return False
    
    if USE_REDIS and redis_client:
        try:
            result = redis_client.delete(f"session:{session_id}")
            logger.info(f"Session deleted from Redis: {session_id[:8]}...")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting session from Redis: {e}")
            return False
    else:
        # Fallback to in-memory
        if session_id in sessions:
            del sessions[session_id]
            logger.info(f"Session deleted from memory: {session_id[:8]}...")
            return True
        return False

def cleanup_expired_sessions():
    """Clean up expired sessions (only for in-memory)"""
    if not USE_REDIS:
        now = datetime.now()
        expired = [
            sid for sid, session in sessions.items()
            if now > session["created_at"] + timedelta(hours=SESSION_EXPIRY_HOURS)
        ]
        for sid in expired:
            del sessions[sid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global fabric_client
    
    logger.info("🚀 Initializing Fabric Data Agent Client...")
    
    try:
        tenant_id = os.getenv("TENANT_ID")
        data_agent_url = os.getenv("DATA_AGENT_URL")
        
        if not data_agent_url:
            logger.error("❌ DATA_AGENT_URL not configured")
            raise ValueError("DATA_AGENT_URL environment variable is required")
        
        fabric_client = FabricDataAgentClient(
            data_agent_url=data_agent_url,
            tenant_id=tenant_id,
            auto_authenticate=False
        )
        
        logger.info("✅ Fabric Data Agent Client initialized")
        logger.info(f"🔐 Authentication deferred - will occur on first request")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Fabric client: {e}")
        fabric_client = None
    
    yield
    
    logger.info("🛑 Shutting down Fabric Data Agent Client...")

app = FastAPI(
    title="Fabric Data Agent API",
    description="Production-ready REST API for querying Microsoft Fabric Data Agents",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not IS_PRODUCTION else None,  # Disable docs in production
    redoc_url="/redoc" if not IS_PRODUCTION else None
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Middleware
# ============================================================================

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests for tracing"""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Add to logging context
    import logging
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.correlation_id = correlation_id
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response

# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    redis_ok = False
    if USE_REDIS and redis_client:
        try:
            redis_client.ping()
            redis_ok = True
        except:
            redis_ok = False
    
    tenant_id = os.getenv("TENANT_ID", "")
    tenant_masked = tenant_id[:8] + "..." if tenant_id else "not_set"
    
    return HealthResponse(
        status="healthy" if (fabric_client and redis_ok) else "degraded",
        environment=ENVIRONMENT,
        fabric_client_initialized=fabric_client is not None,
        redis_connected=redis_ok,
        tenant_id=tenant_masked
    )

# Continue in next file...
