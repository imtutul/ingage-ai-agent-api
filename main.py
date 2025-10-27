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
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Cookie, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
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

# Session storage (in production, use Redis or similar)
# Format: {session_id: {"authenticated": bool, "user": dict, "created_at": datetime, "last_accessed": datetime}}
sessions: Dict[str, Dict[str, Any]] = {}

# Session configuration
SESSION_COOKIE_NAME = "fabric_session_id"
SESSION_EXPIRY_HOURS = 24

# Pydantic models for request/response
class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

class QueryRequest(BaseModel):
    """Request model for data agent queries"""
    query: str = Field(..., description="The question or query to ask the data agent", min_length=1)
    include_details: bool = Field(default=False, description="Whether to include detailed run information")
    conversation_history: Optional[List[ConversationMessage]] = Field(default=None, description="Previous conversation history for context")

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

class AuthStatusResponse(BaseModel):
    """Authentication status response"""
    authenticated: bool = Field(..., description="Whether user is authenticated")
    user: Optional[Dict[str, Any]] = Field(None, description="User information if authenticated")
    session_id: Optional[str] = Field(None, description="Current session ID")

class AuthResponse(BaseModel):
    """Authentication action response"""
    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Status message")
    user: Optional[Dict[str, Any]] = Field(None, description="User information if authenticated")
    session_id: Optional[str] = Field(None, description="Session ID")

class UserDetailsResponse(BaseModel):
    """User details response"""
    success: bool = Field(..., description="Whether the request was successful")
    user: Optional[Dict[str, Any]] = Field(None, description="User information")
    error: Optional[str] = Field(None, description="Error message if request failed")

class ClientAuthRequest(BaseModel):
    """Request model for client-side authentication"""
    access_token: str = Field(..., description="Access token obtained from client-side authentication (Graph token for validation)", min_length=1)
    fabric_token: Optional[str] = Field(None, description="Fabric API token for querying data agents", min_length=1)

# Helper functions for session management
def create_session(user_data: dict, access_token: str = None) -> str:
    """Create a new session and return session ID"""
    session_id = str(uuid.uuid4())
    now = datetime.now()
    sessions[session_id] = {
        "authenticated": True,
        "user": user_data,
        "access_token": access_token,  # Store token for API calls
        "created_at": now,
        "last_accessed": now
    }
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session data by ID, returns None if expired or not found"""
    if not session_id or session_id not in sessions:
        return None
    
    session = sessions[session_id]
    
    # Check if session expired
    expiry_time = session["created_at"] + timedelta(hours=SESSION_EXPIRY_HOURS)
    if datetime.now() > expiry_time:
        # Session expired, clean it up
        del sessions[session_id]
        return None
    
    # Update last accessed time
    session["last_accessed"] = datetime.now()
    return session

def delete_session(session_id: str):
    """Delete a session"""
    if session_id in sessions:
        del sessions[session_id]

def cleanup_expired_sessions():
    """Remove expired sessions"""
    now = datetime.now()
    expired_sessions = []
    
    for session_id, session in sessions.items():
        expiry_time = session["created_at"] + timedelta(hours=SESSION_EXPIRY_HOURS)
        if now > expiry_time:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del sessions[session_id]
    
    if expired_sessions:
        print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")

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
        # Get optional service principal credentials
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        
        # Initialize client WITHOUT automatic authentication
        # Authentication will happen on-demand when a user makes their first request
        fabric_client = FabricDataAgentClient(
            data_agent_url=data_agent_url,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            auto_authenticate=False  # Don't authenticate during startup
        )
        print("✅ Fabric Data Agent Client initialized successfully (authentication deferred)")
        print("🔐 Authentication will occur when first user makes a request")
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
    allow_origins=[
        "http://localhost:4200",
        "https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net"
    ],  # Configure this appropriately for production
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

@app.get("/auth/success", response_class=HTMLResponse)
async def auth_success_page():
    """
    Success page shown after server-side authentication.
    This provides better UX than the default Azure redirect page.
    """
    frontend_url = os.getenv("INGAGE_AI_AGENT_URL", "https://ingage-agent-ui-aqcxg2hhdxa2gcfr.canadacentral-01.azurewebsites.net")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Successful</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }}
            .success-icon {{
                font-size: 64px;
                color: #28a745;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
            }}
            p {{
                color: #666;
                margin-bottom: 20px;
                line-height: 1.6;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                transition: background 0.3s;
            }}
            .button:hover {{
                background: #5568d3;
            }}
            .info {{
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
                font-size: 14px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✓</div>
            <h1>Authentication Successful!</h1>
            <p>You have been successfully authenticated. You can now close this window and return to your application.</p>
            <a href="{frontend_url}" class="button">Return to Application</a>
            <div class="info">
                <strong>Note:</strong> For production deployments, we recommend using client-side authentication (MSAL.js) instead of server-side authentication for better user experience and scalability.
            </div>
        </div>
        
        <script>
            // Auto-close this window after 3 seconds if opened as popup
            if (window.opener) {{
                setTimeout(() => {{
                    window.close();
                }}, 3000);
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/auth/login", response_model=AuthResponse)
async def login(response: Response, background_tasks: BackgroundTasks):
    """
    User delegation authentication endpoint.
    Triggers interactive browser authentication and creates a session.
    
    NOTE: This method is NOT recommended for production as it requires a browser 
    on the server. Use /auth/client-login instead for production deployments.
    """
    if not fabric_client:
        raise HTTPException(status_code=503, detail="Fabric Data Agent client not initialized")
    
    try:
        print("🔐 Starting user delegation authentication...")
        print("⚠️  Note: Browser will open at localhost:8400 (Azure's default redirect)")
        print("⚠️  For production, use client-side authentication instead")
        
        # Trigger authentication (will open browser for user to sign in)
        fabric_client.ensure_authenticated()
        
        # Get user details
        user_data = fabric_client.get_current_user()
        
        # Create session
        session_id = create_session(user_data)
        
        # Set session cookie
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=SESSION_EXPIRY_HOURS * 3600,
            samesite="lax"
        )
        
        # Schedule cleanup of expired sessions
        background_tasks.add_task(cleanup_expired_sessions)
        
        print(f"✅ User authenticated: {user_data.get('email')}")
        print(f"💡 Tip: User can now close the localhost:8400 window and return to your app")
        
        return AuthResponse(
            success=True,
            message="Authentication successful. You can close the authentication window and return to your application.",
            user=user_data,
            session_id=session_id
        )
    
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@app.post("/auth/client-login", response_model=AuthResponse)
async def client_login(auth_request: ClientAuthRequest, response: Response, background_tasks: BackgroundTasks):
    """
    Client-side authentication endpoint.
    Accepts tokens obtained from frontend authentication (MSAL.js, etc.) and creates a session.
    
    Can accept either:
    - access_token only (Graph token) - will try to use for both validation and Fabric queries
    - access_token (Graph) + fabric_token - recommended approach
    
    This is the RECOMMENDED approach for production web applications.
    """
    if not fabric_client:
        raise HTTPException(status_code=503, detail="Fabric Data Agent client not initialized")
    
    try:
        print("🔐 Client-side authentication - validating token...")
        print(f"🔍 Graph token preview: {auth_request.access_token[:50]}...")
        if auth_request.fabric_token:
            print(f"🔍 Fabric token preview: {auth_request.fabric_token[:50]}...")
        
        # Create a temporary client instance with the provided token
        import requests
        import base64
        import json
        
        # Determine which token to use for what
        graph_token = auth_request.access_token
        fabric_token = auth_request.fabric_token or auth_request.access_token
        
        # Decode tokens to check scopes (for debugging)
        try:
            token_parts = fabric_token.split('.')
            if len(token_parts) >= 2:
                # Add padding if needed
                payload = token_parts[1]
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.b64decode(payload)
                token_data = json.loads(decoded)
                print(f"🔍 Fabric token audience: {token_data.get('aud')}")
                print(f"🔍 Fabric token scopes: {token_data.get('scp', 'N/A')}")
                print(f"🔍 Fabric token roles: {token_data.get('roles', 'N/A')}")
        except Exception as decode_error:
            print(f"⚠️ Could not decode Fabric token for debugging: {decode_error}")
        
        # Validate Graph token by trying to get user info
        headers = {
            "Authorization": f"Bearer {graph_token}",
            "Content-Type": "application/json"
        }
        
        graph_response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers,
            timeout=10
        )
        
        if graph_response.status_code != 200:
            # If Graph validation fails, try to extract user from Fabric token
            print(f"⚠️ Graph validation failed ({graph_response.status_code}), extracting user from Fabric token...")
            try:
                token_parts = fabric_token.split('.')
                if len(token_parts) >= 2:
                    payload = token_parts[1] + '=' * (4 - len(token_parts[1]) % 4)
                    decoded = base64.b64decode(payload)
                    token_data = json.loads(decoded)
                    user_data = {
                        "email": token_data.get("upn") or token_data.get("unique_name") or token_data.get("preferred_username"),
                        "display_name": token_data.get("name", "User"),
                        "given_name": token_data.get("given_name"),
                        "surname": token_data.get("family_name"),
                        "id": token_data.get("oid")
                    }
                    print(f"✅ Extracted user from token: {user_data.get('email')}")
                else:
                    raise ValueError("Invalid token format")
            except Exception as e:
                raise HTTPException(
                    status_code=401,
                    detail=f"Token validation failed: {str(e)}"
                )
        else:
            # Extract user data from Graph API
            user_info = graph_response.json()
            user_data = {
                "email": user_info.get("mail") or user_info.get("userPrincipalName"),
                "display_name": user_info.get("displayName"),
                "given_name": user_info.get("givenName"),
                "surname": user_info.get("surname"),
                "job_title": user_info.get("jobTitle"),
                "office_location": user_info.get("officeLocation"),
                "id": user_info.get("id")
            }
        
        # Create session with Fabric token
        session_id = create_session(user_data, fabric_token)
        
        # Set session cookie
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=SESSION_EXPIRY_HOURS * 3600,
            samesite="lax"
        )
        
        # Schedule cleanup of expired sessions
        background_tasks.add_task(cleanup_expired_sessions)
        
        print(f"✅ Client-side authentication successful: {user_data.get('email')}")
        
        return AuthResponse(
            success=True,
            message="Client-side authentication successful",
            user=user_data,
            session_id=session_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Client-side authentication failed: {e}")
        raise HTTPException(status_code=401, detail=f"Client-side authentication failed: {str(e)}")

@app.get("/auth/status", response_model=AuthStatusResponse)
async def auth_status(session_id: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME)):
    """
    Check authentication status.
    Returns current user information if authenticated.
    """
    if not session_id:
        return AuthStatusResponse(
            authenticated=False,
            user=None,
            session_id=None
        )
    
    session = get_session(session_id)
    
    if not session:
        return AuthStatusResponse(
            authenticated=False,
            user=None,
            session_id=None
        )
    
    return AuthStatusResponse(
        authenticated=session["authenticated"],
        user=session["user"],
        session_id=session_id
    )

@app.post("/auth/logout", response_model=AuthResponse)
async def logout(response: Response, session_id: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME)):
    """
    Sign out the current user.
    Clears the session, removes the session cookie, and clears all authentication credentials.
    Next login will require browser authentication again.
    """
    if session_id:
        delete_session(session_id)
    
    # Clear the session cookie
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    
    # Logout from fabric client (clears tokens and credentials - forces re-auth on next login)
    if fabric_client:
        fabric_client.logout()
    
    print("✅ User logged out - all credentials cleared")
    
    return AuthResponse(
        success=True,
        message="Logged out successfully. Browser authentication will be required on next login.",
        user=None,
        session_id=None
    )

@app.get("/auth/user", response_model=UserDetailsResponse)
async def get_user_details(session_id: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME)):
    """
    Get detailed information about the current authenticated user.
    Fetches fresh data from Microsoft Graph API.
    """
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    if not fabric_client:
        raise HTTPException(status_code=503, detail="Fabric Data Agent client not initialized")
    
    try:
        # Get fresh user data from Microsoft Graph
        user_data = fabric_client.get_current_user()
        
        # Update session with fresh data
        session["user"] = user_data
        
        return UserDetailsResponse(
            success=True,
            user=user_data,
            error=None
        )
    
    except Exception as e:
        print(f"❌ Failed to get user details: {e}")
        return UserDetailsResponse(
            success=False,
            user=None,
            error=str(e)
        )

# ============================================================================
# Query Endpoints
# ============================================================================

@app.post("/query", response_model=QueryResponse)
async def simple_query(request: QueryRequest, session_id: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME)):
    """
    Simple query endpoint that returns just the data agent's response.
    Requires authentication.
    """
    
    print(f"📝 Processing session_id: {session_id}")
    
    # Check authentication
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please login again.")
    
    if not fabric_client:
        raise HTTPException(status_code=503, detail="Fabric Data Agent client not initialized")
    
    try:
        user_email = session["user"].get("email", "unknown")
        print(f"📝 Processing query from {user_email}: {request.query}")
        
        # Convert conversation history to dictionary format if provided
        conversation_history = None
        if request.conversation_history:
            raw_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
            
            # Limit conversation history to prevent 500 errors from oversized payloads
            max_history_pairs = 6  # Last 6 exchanges (12 messages total)
            if len(raw_history) > max_history_pairs * 2:
                # Keep the most recent exchanges
                conversation_history = raw_history[-(max_history_pairs * 2):]
                print(f"📚 Conversation history trimmed from {len(raw_history)} to {len(conversation_history)} messages")
            else:
                conversation_history = raw_history
                
            # Also check total content length to prevent token limit issues
            total_content_length = sum(len(msg["content"]) for msg in conversation_history)
            max_content_length = 8000  # Conservative limit
            
            if total_content_length > max_content_length:
                # Further trim by removing older messages
                while conversation_history and total_content_length > max_content_length:
                    # Remove the oldest pair (user + assistant)
                    if len(conversation_history) >= 2:
                        removed_user = conversation_history.pop(0)
                        removed_assistant = conversation_history.pop(0) if conversation_history else None
                        total_content_length -= len(removed_user["content"])
                        if removed_assistant:
                            total_content_length -= len(removed_assistant["content"])
                    else:
                        break
                print(f"📚 Conversation history further trimmed due to content length ({total_content_length:,} chars)")
            
            print(f"📚 Including {len(conversation_history)} messages from conversation history ({total_content_length:,} chars)")
        
        # If session has an access token (client-side auth), use it
        if session.get("access_token"):
            # Create a temporary client with the user's token
            user_client = FabricDataAgentClient(
                data_agent_url=fabric_client.data_agent_url,
                tenant_id=fabric_client.tenant_id,
                auto_authenticate=False,
                access_token=session["access_token"]
            )
            response = user_client.ask(request.query, conversation_history=conversation_history)
        else:
            # Use server-side authentication
            response = fabric_client.ask(request.query, conversation_history=conversation_history)
        
        print(f"✅ Query successful for {user_email}")
        return QueryResponse(
            success=True,
            response=response,
            query=request.query
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (auth errors, etc.)
        raise
    
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Safely get user info for logging
        user_email = "unknown"
        try:
            if session and "user" in session:
                user_email = session["user"].get("email", "unknown")
        except:
            pass
        
        print(f"❌ Query failed for {user_email}:")
        print(f"   Type: {error_type}")
        print(f"   Message: {error_msg}")
        print(f"   Query: {request.query}")
        
        # Log full traceback for debugging
        import traceback
        print(f"🔍 Full error traceback:")
        traceback.print_exc()
        
        # Parse Fabric-specific errors (prefixed with FABRIC_)
        user_message = ""
        error_category = "UNKNOWN"
        
        if error_msg.startswith("FABRIC_"):
            # Extract category and message
            parts = error_msg.split(":", 1)
            if len(parts) == 2:
                error_category = parts[0]
                user_message = parts[1].strip()
            else:
                user_message = error_msg
        else:
            # Handle other error types
            if "HTTPException" in error_type:
                error_category = "HTTP_ERROR"
                user_message = "There was an issue processing your request. Please try again."
            elif "timeout" in error_msg.lower() or "TimeoutError" in error_type:
                error_category = "TIMEOUT"
                user_message = "Your request timed out. The query may be too complex. Please try a simpler question or try again later."
            elif "connection" in error_msg.lower() or "ConnectionError" in error_type:
                error_category = "CONNECTION_ERROR"
                user_message = "Unable to connect to the service. Please check your connection and try again."
            elif "ValidationError" in error_type:
                error_category = "VALIDATION_ERROR"
                user_message = f"Invalid request: {error_msg}"
            else:
                error_category = "UNKNOWN_ERROR"
                user_message = "An unexpected error occurred. Please try again later."
        
        print(f"   Category: {error_category}")
        print(f"   User Message: {user_message}")
        
        return QueryResponse(
            success=False,
            response=user_message,
            query=request.query,
            error=f"{error_category}: {error_msg}"
        )

@app.post("/query/detailed", response_model=DetailedQueryResponse)
async def detailed_query(request: QueryRequest, session_id: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME)):
    """
    Detailed query endpoint that returns response plus run details, SQL queries, and data previews.
    Requires authentication.
    """
    # Check authentication
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please login again.")
    
    if not fabric_client:
        raise HTTPException(status_code=503, detail="Fabric Data Agent client not initialized")
    
    try:
        user_email = session["user"].get("email", "unknown")
        print(f"📝 Processing detailed query from {user_email}: {request.query}")
        
        # Convert conversation history to dictionary format if provided
        conversation_history = None
        if request.conversation_history:
            # Implement conversation length management to prevent 500 errors
            history = request.conversation_history
            
            # Limit to last 6 exchanges (12 messages) to prevent token overflow
            if len(history) > 12:
                history = history[-12:]
                print(f"⚠️ Conversation history trimmed to last 12 messages ({len(history)} from {len(request.conversation_history)})")
            
            # Check total character count and trim if necessary
            total_chars = sum(len(msg.content) for msg in history)
            if total_chars > 8000:
                # Remove oldest messages until under limit
                while history and sum(len(msg.content) for msg in history) > 8000:
                    history.pop(0)
                print(f"⚠️ Conversation history trimmed by character count to {len(history)} messages")
            
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in history
            ]
            print(f"📚 Including {len(conversation_history)} messages from conversation history (total chars: {sum(len(msg['content']) for msg in conversation_history)})")
        
        # If session has an access token (client-side auth), use it
        if session.get("access_token"):
            # Create a temporary client with the user's token
            user_client = FabricDataAgentClient(
                data_agent_url=fabric_client.data_agent_url,
                tenant_id=fabric_client.tenant_id,
                auto_authenticate=False,
                access_token=session["access_token"]
            )
            run_details = user_client.get_run_details(request.query, conversation_history=conversation_history)
        else:
            # Use server-side authentication
            run_details = fabric_client.get_run_details(request.query, conversation_history=conversation_history)
        
        if "error" in run_details:
            print(f"❌ Detailed query returned error: {run_details['error']}")
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
        
        print(f"✅ Detailed query successful for {user_email}")
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
    
    except HTTPException:
        # Re-raise HTTP exceptions (auth errors, etc.)
        raise
    
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Safely get user info for logging
        user_email = "unknown"
        try:
            if session and "user" in session:
                user_email = session["user"].get("email", "unknown")
        except:
            pass
        
        print(f"❌ Detailed query failed for {user_email}:")
        print(f"   Type: {error_type}")
        print(f"   Message: {error_msg}")
        print(f"   Query: {request.query}")
        
        # Log full traceback for debugging
        import traceback
        print(f"🔍 Full error traceback:")
        traceback.print_exc()
        
        # Parse Fabric-specific errors (prefixed with FABRIC_)
        user_message = ""
        error_category = "UNKNOWN"
        
        if error_msg.startswith("FABRIC_"):
            # Extract category and message
            parts = error_msg.split(":", 1)
            if len(parts) == 2:
                error_category = parts[0]
                user_message = parts[1].strip()
            else:
                user_message = error_msg
        else:
            # Handle other error types
            if "HTTPException" in error_type:
                error_category = "HTTP_ERROR"
                user_message = "There was an issue processing your request. Please try again."
            elif "timeout" in error_msg.lower() or "TimeoutError" in error_type:
                error_category = "TIMEOUT"
                user_message = "Your request timed out. The query may be too complex. Please try a simpler question or try again later."
            elif "connection" in error_msg.lower() or "ConnectionError" in error_type:
                error_category = "CONNECTION_ERROR"
                user_message = "Unable to connect to the service. Please check your connection and try again."
            elif "ValidationError" in error_type:
                error_category = "VALIDATION_ERROR"
                user_message = f"Invalid request: {error_msg}"
            else:
                error_category = "UNKNOWN_ERROR"
                user_message = "An unexpected error occurred. Please try again later."
        
        print(f"   Category: {error_category}")
        print(f"   User Message: {user_message}")
        
        return DetailedQueryResponse(
            success=False,
            response=user_message,
            query=request.query,
            error=f"{error_category}: {error_msg}"
        )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Fabric Data Agent API",
        "version": "2.0.0",
        "description": "REST API with user delegation authentication for Microsoft Fabric Data Agents",
        "endpoints": {
            "health": "/health",
            "authentication": {
                "login": "/auth/login",
                "status": "/auth/status",
                "logout": "/auth/logout",
                "user_details": "/auth/user"
            },
            "queries": {
                "simple_query": "/query",
                "detailed_query": "/query/detailed"
            },
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc"
            }
        },
        "authentication": {
            "type": "User Delegation (Interactive Browser)",
            "session_expiry_hours": SESSION_EXPIRY_HOURS,
            "required_for": ["All query endpoints"]
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