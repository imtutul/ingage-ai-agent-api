#!/usr/bin/env python3
"""
Diagnostic script for 401 authentication error
"""

import os
import requests
import json
from datetime import datetime

def diagnose_401_error():
    """Diagnose the 401 authentication error"""
    
    print("🔍 Diagnosing 401 Authentication Error")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Step 1: Checking Environment Variables")
    env_vars = {
        "TENANT_ID": os.getenv("TENANT_ID"),
        "CLIENT_ID": os.getenv("CLIENT_ID"), 
        "CLIENT_SECRET": os.getenv("CLIENT_SECRET"),
        "DATA_AGENT_URL": os.getenv("DATA_AGENT_URL")
    }
    
    for var, value in env_vars.items():
        if value:
            if var == "CLIENT_SECRET":
                print(f"   ✅ {var}: {'*' * 8}...{value[-4:] if len(value) > 4 else '****'}")
            elif var == "DATA_AGENT_URL":
                print(f"   ✅ {var}: {value}")
            else:
                print(f"   ✅ {var}: {value[:8]}...{value[-4:] if len(value) > 8 else value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    # Check if server is running
    print(f"\n📋 Step 2: Checking Server Health")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Server is running")
            print(f"   📊 Fabric client initialized: {health_data.get('fabric_client_initialized', False)}")
            print(f"   🏢 Tenant ID: {health_data.get('tenant_id', 'Not set')}")
        else:
            print(f"   ❌ Server health check failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {e}")
        return
    
    # Check authentication status
    print(f"\n📋 Step 3: Checking Authentication Status")
    try:
        response = requests.get("http://localhost:8000/auth/status", timeout=5)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            auth_data = response.json()
            print(f"   🔐 Authenticated: {auth_data.get('authenticated', False)}")
            if auth_data.get('user'):
                user_email = auth_data['user'].get('email', 'Unknown')
                print(f"   👤 User: {user_email}")
        else:
            print(f"   ⚠️ Not authenticated: {response.text}")
    except Exception as e:
        print(f"   ❌ Auth status check failed: {e}")
    
    # Test basic connectivity to Fabric API
    print(f"\n📋 Step 4: Testing Fabric API Connectivity")
    
    if not env_vars["DATA_AGENT_URL"]:
        print("   ❌ Cannot test - DATA_AGENT_URL not set")
        return
    
    # Try to make a direct request to the Fabric API
    try:
        from azure.identity import ClientSecretCredential
        
        if env_vars["TENANT_ID"] and env_vars["CLIENT_ID"] and env_vars["CLIENT_SECRET"]:
            print("   🔑 Testing service principal authentication...")
            
            credential = ClientSecretCredential(
                tenant_id=env_vars["TENANT_ID"],
                client_id=env_vars["CLIENT_ID"],
                client_secret=env_vars["CLIENT_SECRET"]
            )
            
            token = credential.get_token("https://api.fabric.microsoft.com/.default")
            print(f"   ✅ Token obtained successfully")
            print(f"   ⏰ Expires at: {datetime.fromtimestamp(token.expires_on)}")
            
            # Test API call with token
            headers = {
                "Authorization": f"Bearer {token.token}",
                "Content-Type": "application/json"
            }
            
            # Make a simple request to the Data Agent URL
            test_url = env_vars["DATA_AGENT_URL"]
            print(f"   🌐 Testing API call to: {test_url[:50]}...")
            
            # Try a simple completion request
            test_payload = {
                "model": "not-used",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                test_url + "/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=30
            )
            
            print(f"   📡 API Response Status: {response.status_code}")
            
            if response.status_code == 401:
                print(f"   ❌ 401 Unauthorized - Token may be invalid or permissions missing")
                print(f"   📝 Response: {response.text[:200]}...")
            elif response.status_code == 200:
                print(f"   ✅ API call successful!")
            else:
                print(f"   ⚠️ Unexpected status: {response.text[:200]}...")
                
        else:
            print("   ⚠️ Service principal credentials not complete - cannot test direct API access")
            
    except Exception as e:
        print(f"   ❌ Direct API test failed: {e}")
    
    # Check token scopes and permissions
    print(f"\n📋 Step 5: Possible Issues and Solutions")
    
    print("   🔍 Common causes of 401 errors:")
    print("   1. Token expired or invalid")
    print("   2. Missing required API permissions")
    print("   3. Service principal not added to Fabric workspace")
    print("   4. Incorrect token audience/scope")
    print("   5. User not authenticated via frontend")
    
    print(f"\n📋 Step 6: Recommended Actions")
    print("   1. Check if you're authenticated:")
    print("      - If using frontend: Ensure you've clicked 'Sign In'")
    print("      - If using direct API: Check service principal setup")
    print("   2. Verify environment variables are correct")
    print("   3. Check Azure AD app registration permissions")
    print("   4. Ensure service principal has access to Fabric workspace")
    print("   5. Try running: python diagnose_permissions.py")
    
    print(f"\n✅ 401 Error Diagnosis Complete!")

if __name__ == "__main__":
    diagnose_401_error()