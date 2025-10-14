#!/usr/bin/env python3
"""
Fabric Data Agent Permission Verification Script
This script tests different types of queries to determine the exact permission issue.
"""
import requests
import json
import time
from datetime import datetime

def make_query(query, description, expected_result="data"):
    """Make a query and analyze the response for permission patterns"""
    print(f"\n🧪 {description}")
    print(f"   Query: {query}")
    
    try:
        response = requests.post(
            "http://127.0.0.1:3000/query",
            json={"query": query},
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            
            print(f"   ✅ HTTP Status: 200 OK")
            print(f"   📝 Response: {data.get('response', '')[:150]}...")
            
            # Analyze response patterns
            permission_indicators = {
                'rate_limit': 'error code: 429' in response_text,
                'auth_error': any(word in response_text for word in ['unauthorized', 'forbidden', 'authentication failed']),
                'permission_error': any(word in response_text for word in ['permission', 'access denied', 'not authorized']),
                'data_access_error': any(word in response_text for word in ['technical issue', 'connectivity problem', 'data warehouse', 'unable to retrieve']),
                'workspace_error': any(word in response_text for word in ['workspace', 'resource not found']),
                'success': any(word in response_text for word in ['member', 'count', 'table', 'data', 'rows']) and 'unable' not in response_text
            }
            
            # Determine issue type
            if permission_indicators['rate_limit']:
                print(f"   ⏰ RATE LIMIT: Wait and retry")
                return 'rate_limit'
            elif permission_indicators['auth_error']:
                print(f"   🔐 AUTHENTICATION ERROR: Service principal auth issue")
                return 'auth_error'
            elif permission_indicators['permission_error']:
                print(f"   🚫 PERMISSION ERROR: API permissions missing")
                return 'permission_error'
            elif permission_indicators['data_access_error']:
                print(f"   📊 DATA ACCESS ERROR: Workspace/dataset permissions missing")
                return 'data_access_error'
            elif permission_indicators['workspace_error']:
                print(f"   🏢 WORKSPACE ERROR: Service principal not in workspace")
                return 'workspace_error'
            elif permission_indicators['success']:
                print(f"   🎉 SUCCESS: Got actual data!")
                return 'success'
            else:
                print(f"   ❓ UNKNOWN: Unexpected response pattern")
                return 'unknown'
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   📝 Response: {response.text}")
            return 'http_error'
            
    except Exception as e:
        print(f"   💥 Exception: {e}")
        return 'exception'

def main():
    """Run comprehensive permission diagnostics"""
    print("🔍 Fabric Data Agent Permission Diagnostics")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Progressive test queries
    tests = [
        {
            "query": "Hello, what can you help me with?",
            "description": "Basic connectivity test (no data access needed)",
            "expected": "success"
        },
        {
            "query": "What is your purpose?",
            "description": "Agent capability test (minimal permissions)",
            "expected": "success"
        },
        {
            "query": "What data sources are available?",
            "description": "Data source discovery (workspace access required)",
            "expected": "data or permission error"
        },
        {
            "query": "Show me the tables in our database",
            "description": "Schema access test (dataset permissions required)",
            "expected": "data or permission error"
        },
        {
            "query": "How many member we have?",
            "description": "Original failing query (full data access required)",
            "expected": "data or permission error"
        },
        {
            "query": "Give me a sample of member data",
            "description": "Data retrieval test (read permissions required)",
            "expected": "data or permission error"
        }
    ]
    
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(tests)}")
        
        result = make_query(test["query"], test["description"])
        results.append({
            "test": test["description"],
            "query": test["query"],
            "result": result
        })
        
        # Don't overwhelm the API
        if i < len(tests):
            print("   ⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    # Analysis and recommendations
    print(f"\n{'='*60}")
    print("📊 DIAGNOSTIC SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r['result'] == 'success')
    data_access_errors = sum(1 for r in results if r['result'] == 'data_access_error')
    rate_limits = sum(1 for r in results if r['result'] == 'rate_limit')
    
    print(f"✅ Successful queries: {success_count}/{len(results)}")
    print(f"📊 Data access errors: {data_access_errors}/{len(results)}")
    print(f"⏰ Rate limit errors: {rate_limits}/{len(results)}")
    
    # Recommendations based on results
    print(f"\n💡 RECOMMENDATIONS:")
    
    if rate_limits > 0:
        print("🔄 Rate Limiting Detected:")
        print("   - Wait 10-15 minutes before testing again")
        print("   - Reduce query frequency")
        print("   - Implement retry logic with exponential backoff")
    
    if data_access_errors > success_count:
        print("\n🔑 Data Access Issues Detected:")
        print("   1. Add service principal to Fabric workspace:")
        print("      - Go to https://app.fabric.microsoft.com")
        print("      - Navigate to your workspace → Settings → Manage access")
        print("      - Add 'fabric-data-agent-service' with Admin role")
        print("   2. Verify dataset/lakehouse permissions")
        print("   3. Check Data Agent skill configuration")
    
    if success_count > 0:
        print(f"\n✅ Some queries working successfully!")
        print("   - Basic authentication and API access is working")
        print("   - Focus on workspace and dataset permissions")
    
    if success_count == len(results):
        print(f"\n🎉 ALL TESTS PASSED!")
        print("   - Your service principal setup is working correctly")
        print("   - Ready for production deployment")
    
    print(f"\n📋 DETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        status_emoji = {
            'success': '✅',
            'data_access_error': '📊',
            'rate_limit': '⏰',
            'permission_error': '🚫',
            'auth_error': '🔐',
            'workspace_error': '🏢',
            'http_error': '❌',
            'exception': '💥',
            'unknown': '❓'
        }.get(result['result'], '❓')
        
        print(f"   {i}. {status_emoji} {result['result'].upper()}: {result['test']}")

if __name__ == "__main__":
    main()