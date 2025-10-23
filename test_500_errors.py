#!/usr/bin/env python3
"""
Diagnostic script for intermittent 500 errors
"""

import requests
import json
import time
from datetime import datetime

def test_intermittent_errors():
    """Test for intermittent 500 errors and identify patterns"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Intermittent 500 Errors")
    print("=" * 60)
    
    # First, check if we can reproduce the issue
    print("\n📋 Step 1: Authentication Status Check")
    try:
        auth_response = requests.get(f"{base_url}/auth/status", timeout=5)
        print(f"   Auth Status: {auth_response.status_code}")
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            print(f"   🔐 Authenticated: {auth_data.get('authenticated', False)}")
            if auth_data.get('authenticated'):
                print(f"   👤 User: {auth_data.get('user', {}).get('email', 'Unknown')}")
            else:
                print("   ⚠️ User not authenticated - cannot test query errors")
                return
        else:
            print(f"   ❌ Cannot check auth status: {auth_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Auth check failed: {e}")
        return
    
    # Test multiple queries to see if we can reproduce the issue
    print(f"\n📋 Step 2: Testing Multiple Queries (Looking for 500 errors)")
    
    test_queries = [
        "What data is available?",
        "Show me member statistics", 
        "How many members do we have?",
        "What are the main tables?",
        "Show me top 5 members with open gaps"
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/query",
                json={"query": query},
                timeout=60,
                cookies=auth_response.cookies  # Use auth cookies if available
            )
            duration = time.time() - start_time
            
            print(f"      Status: {response.status_code} (took {duration:.2f}s)")
            
            if response.status_code == 500:
                print(f"      ❌ 500 ERROR REPRODUCED!")
                print(f"      📝 Error details: {response.text[:200]}...")
                results.append({"query": query, "status": 500, "error": response.text, "duration": duration})
            elif response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                response_text = data.get('response', '')
                print(f"      ✅ Success: {success}")
                print(f"      📝 Response: {response_text[:100]}...")
                results.append({"query": query, "status": 200, "success": success, "duration": duration})
            else:
                print(f"      ⚠️ Unexpected status: {response.text[:100]}...")
                results.append({"query": query, "status": response.status_code, "error": response.text, "duration": duration})
                
        except Exception as e:
            print(f"      💥 Exception: {e}")
            results.append({"query": query, "status": "exception", "error": str(e), "duration": 0})
        
        # Small delay between requests
        time.sleep(2)
    
    # Analyze results
    print(f"\n📋 Step 3: Results Analysis")
    successes = [r for r in results if r.get('status') == 200 and r.get('success')]
    errors_500 = [r for r in results if r.get('status') == 500]
    other_errors = [r for r in results if r.get('status') not in [200, 500]]
    
    print(f"   ✅ Successful queries: {len(successes)}/{len(results)}")
    print(f"   ❌ 500 errors: {len(errors_500)}/{len(results)}")
    print(f"   ⚠️ Other errors: {len(other_errors)}/{len(results)}")
    
    if errors_500:
        print(f"\n   🔍 500 Error Analysis:")
        for error in errors_500:
            print(f"      - Query: '{error['query']}'")
            print(f"        Duration: {error.get('duration', 0):.2f}s")
            print(f"        Error: {error['error'][:150]}...")
    
    # Test server health during the issue
    print(f"\n📋 Step 4: Server Health Check")
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Health Status: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   🏥 Status: {health_data.get('status', 'unknown')}")
            print(f"   🔧 Fabric client: {health_data.get('fabric_client_initialized', False)}")
        else:
            print(f"   ❌ Health check failed: {health_response.text}")
    except Exception as e:
        print(f"   💥 Health check exception: {e}")
    
    # Recommendations based on results
    print(f"\n📋 Step 5: Diagnostic Recommendations")
    
    error_rate = len(errors_500) / len(results) * 100
    print(f"   📊 Error rate: {error_rate:.1f}%")
    
    if error_rate > 0:
        print(f"\n   🎯 Likely causes based on error pattern:")
        print(f"   1. Token expiration/refresh issues")
        print(f"   2. Fabric API rate limiting") 
        print(f"   3. OpenAI thread cleanup problems")
        print(f"   4. Memory/resource exhaustion")
        print(f"   5. Concurrency issues in the backend")
        
        print(f"\n   💡 Recommended fixes:")
        print(f"   1. Add better error handling and retry logic")
        print(f"   2. Implement token refresh mechanism")
        print(f"   3. Add rate limiting and request queuing")
        print(f"   4. Improve thread cleanup and resource management")
        print(f"   5. Add detailed logging to identify exact failure points")
    else:
        print(f"   ✅ No 500 errors reproduced in this test")
        print(f"   🔍 The issue may be:")
        print(f"   - Timing-dependent (load, specific queries)")
        print(f"   - Session-dependent (long-running sessions)")
        print(f"   - Browser-specific (CORS, cookies)")

if __name__ == "__main__":
    test_intermittent_errors()