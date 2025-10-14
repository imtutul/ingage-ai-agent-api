#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI server is working with service principal authentication
"""
import requests
import json
import time

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        print("🔍 Testing health endpoint...")
        response = requests.get("http://127.0.0.1:3000/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful!")
            print(f"   Status: {data.get('status')}")
            print(f"   Fabric Client Initialized: {data.get('fabric_client_initialized')}")
            print(f"   Tenant ID: {data.get('tenant_id')}")
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

def test_query_endpoint():
    """Test the query endpoint"""
    try:
        print("\n💬 Testing query endpoint...")
        query_data = {
            "query": "What data sources are available?"
        }
        
        response = requests.post(
            "http://127.0.0.1:3000/query", 
            json=query_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Query successful!")
            print(f"   Success: {data.get('success')}")
            print(f"   Response preview: {str(data.get('response', ''))[:200]}...")
            return True
        else:
            print(f"❌ Query failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing query endpoint: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Fabric Data Agent API Server")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    
    if health_ok:
        # Test query endpoint
        query_ok = test_query_endpoint()
        
        if query_ok:
            print("\n🎉 All tests passed! Your API server is working correctly.")
        else:
            print("\n⚠️  Health check passed but query failed. Check server logs.")
    else:
        print("\n❌ Health check failed. Server may not be running or configured correctly.")

if __name__ == "__main__":
    main()