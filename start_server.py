#!/usr/bin/env python3
"""
Startup script for the Fabric Data Agent FastAPI server
"""

import uvicorn
import os
import sys
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file if present

def main():
    """Start the FastAPI server"""
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"🚀 Starting Fabric Data Agent API server...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    print(f"📝 Log level: {log_level}")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️ Warning: .env file not found. Make sure environment variables are set.")
        print("💡 Copy .env.example to .env and configure your values.")
    
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n⏹️ Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()