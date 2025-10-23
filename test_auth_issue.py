#!/usr/bin/env python3
"""
Test script to demonstrate the 401 authentication issue and solution
"""

import requests
import json

def test_authentication_issue():
    """Test the authentication issue and show the solution"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing 401 Authentication Issue")
    print("=" * 50)
    
    # Step 1: Check server health
    print("\n📋 Step 1: Check server health")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Server is running")
            print(f"   🔧 Fabric client initialized: {health['fabric_client_initialized']}")
            print(f"   🏢 Tenant ID: {health.get('tenant_id', 'Not available')}")
        else:
            print(f"   ❌ Health check failed: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {e}")
        return
    
    # Step 2: Check authentication status (should show not authenticated)
    print(f"\n📋 Step 2: Check authentication status")
    try:
        response = requests.get(f"{base_url}/auth/status", timeout=5)
        print(f"   Status: {response.status_code}")
        auth_data = response.json()
        print(f"   🔐 Authenticated: {auth_data.get('authenticated', False)}")
        if not auth_data.get('authenticated'):
            print(f"   ⚠️ User is not authenticated - this is the problem!")
    except Exception as e:
        print(f"   ❌ Auth status check failed: {e}")
    
    # Step 3: Try to make a query (this will fail with 401)
    print(f"\n📋 Step 3: Try to make a query without authentication")
    query_data = {
        "query": "show me top 5 members with open gaps"
    }
    
    try:
        response = requests.post(f"{base_url}/query", json=query_data, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"   ❌ 401 Unauthorized - This is expected!")
            print(f"   📝 Response: {response.text}")
        elif response.status_code == 200:
            result = response.json()
            print(f"   ✅ Query successful: {result.get('success')}")
            print(f"   📝 Response: {result.get('response', '')[:100]}...")
        else:
            print(f"   ⚠️ Unexpected status: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
    
    # Step 4: Explain the solutions
    print(f"\n📋 Step 4: Solutions to fix the 401 error")
    print(f"")
    print(f"   🎯 The 401 error occurs because you're not authenticated.")
    print(f"   📱 This API requires user authentication before making queries.")
    print(f"")
    print(f"   💡 Solution Options:")
    print(f"")
    print(f"   1. 🌐 Frontend Authentication (Recommended):")
    print(f"      - Use the web frontend to sign in via Microsoft 365")
    print(f"      - Frontend handles MSAL.js authentication")
    print(f"      - Sends tokens to /auth/client-login endpoint")
    print(f"      - Creates authenticated session")
    print(f"")
    print(f"   2. 🔧 Service Principal Setup (Production):")
    print(f"      - Add CLIENT_ID and CLIENT_SECRET to .env file")
    print(f"      - Use Azure AD App Registration credentials")
    print(f"      - Server will use service principal authentication")
    print(f"")
    print(f"   3. 🖥️ Interactive Browser (Development):")
    print(f"      - Use direct client authentication")
    print(f"      - Call /auth/login endpoint (not implemented in current version)")
    print(f"")
    print(f"   📋 Current Setup Analysis:")
    print(f"   - TENANT_ID: ✅ Set")
    print(f"   - DATA_AGENT_URL: ✅ Set") 
    print(f"   - CLIENT_ID: ❌ Missing (causes Interactive Browser mode)")
    print(f"   - CLIENT_SECRET: ❌ Missing (causes Interactive Browser mode)")
    print(f"   - Authentication Mode: Interactive Browser (requires frontend)")
    print(f"")
    print(f"   🎯 Quick Fix:")
    print(f"   - Open the web frontend")
    print(f"   - Click 'Sign In' button")
    print(f"   - Authenticate with Microsoft 365")
    print(f"   - Then API calls will work")

if __name__ == "__main__":
    test_authentication_issue()