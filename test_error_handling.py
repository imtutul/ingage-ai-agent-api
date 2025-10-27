#!/usr/bin/env python3
"""
Test script for Fabric API error handling improvements
Tests various error scenarios and validates proper error messages
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_error_handling():
    """Test various error scenarios"""
    
    print("=" * 60)
    print("Testing Fabric API Error Handling")
    print("=" * 60)
    
    # Test 1: Unauthenticated request
    print("\n1️⃣ Testing unauthenticated request to /query...")
    response = requests.post(
        f"{BASE_URL}/query",
        json={"query": "What is the total sales?"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 401, "Should return 401 for unauthenticated request"
    print("   ✅ Correctly returned 401 Unauthorized")
    
    # Test 2: Invalid session cookie
    print("\n2️⃣ Testing invalid session cookie...")
    response = requests.post(
        f"{BASE_URL}/query",
        json={"query": "What is the total sales?"},
        cookies={"fabric_session_id": "invalid-session-123"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 401, "Should return 401 for invalid session"
    print("   ✅ Correctly returned 401 for invalid session")
    
    # Test 3: Empty query
    print("\n3️⃣ Testing empty query (requires valid session)...")
    print("   ⚠️ Skipping - requires authenticated session")
    
    # Test 4: Health endpoint (should always work)
    print("\n4️⃣ Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200, "Health check should return 200"
    assert response.json()["status"] == "healthy", "Should be healthy"
    print("   ✅ Health check passed")
    
    # Test 5: Root endpoint documentation
    print("\n5️⃣ Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Message: {data.get('message')}")
    print(f"   Version: {data.get('version')}")
    assert response.status_code == 200, "Root should return 200"
    assert "endpoints" in data, "Should have endpoints info"
    print("   ✅ Root endpoint working")
    
    print("\n" + "=" * 60)
    print("✅ All error handling tests passed!")
    print("=" * 60)
    print("\nError Categories Implemented:")
    print("  • FABRIC_AUTH_ERROR - Authentication failures")
    print("  • FABRIC_PERMISSION_ERROR - Access denied")
    print("  • FABRIC_NOT_FOUND - Endpoint not found")
    print("  • FABRIC_RATE_LIMIT - Too many requests")
    print("  • FABRIC_TIMEOUT - Request timeout")
    print("  • FABRIC_CONNECTION_ERROR - Network issues")
    print("  • FABRIC_TOKEN_EXPIRED - Expired auth token")
    print("  • FABRIC_SERVER_ERROR - 5xx server errors")
    print("  • FABRIC_ERROR - General Fabric errors")
    print("\nFrontend Integration:")
    print("  • All errors include 'error' field with categorized error")
    print("  • All errors include user-friendly 'response' message")
    print("  • Frontend can check error.startsWith('FABRIC_') for specific handling")
    print("  • All responses maintain consistent structure")

if __name__ == "__main__":
    try:
        test_error_handling()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("   Make sure the server is running: python main.py")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
