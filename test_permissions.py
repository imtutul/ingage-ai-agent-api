#!/usr/bin/env python3
"""
Test script to verify service principal permissions for Fabric Data Agent
This script tests different types of queries to isolate permission issues.
"""
import requests
import json
import time

def test_query(query, description, timeout=30):
    """Test a specific query and analyze the response"""
    print(f"\n🧪 Testing: {description}")
    print(f"   Query: {query}")
    
    try:
        response = requests.post(
            "http://127.0.0.1:3000/query",
            json={"query": query},
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: Success")
            print(f"   📝 Response: {data.get('response', '')[:150]}...")
            
            # Analyze response for permission issues
            response_text = data.get('response', '').lower()
            if any(keyword in response_text for keyword in [
                'technical connection issue', 
                'permissions', 
                'access denied', 
                'unable to retrieve',
                'temporarily unavailable'
            ]):
                print(f"   ⚠️  Possible permission issue detected")
                return False
            else:
                print(f"   ✅ Response looks good - no permission issues detected")
                return True
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run comprehensive permission tests"""
    print("🔐 Fabric Data Agent Permission Testing")
    print("=" * 50)
    
    # Test queries in order of complexity
    tests = [
        {
            "query": "What can you help me with?",
            "description": "General capability test (no data access needed)",
            "critical": False
        },
        {
            "query": "What types of questions can you answer?",
            "description": "Agent functionality test (minimal access)",
            "critical": False
        },
        {
            "query": "What data sources are available?",
            "description": "Data source discovery (requires workspace access)",
            "critical": True
        },
        {
            "query": "What tables or datasets do we have?",
            "description": "Table/dataset enumeration (requires data permissions)",
            "critical": True
        },
        {
            "query": "Show me the structure of our data",
            "description": "Schema access test (requires read permissions)",
            "critical": True
        },
        {
            "query": "How many member we have",
            "description": "Original failing query (requires full data access)",
            "critical": True
        },
        {
            "query": "Give me a summary of available data",
            "description": "Data summary test (comprehensive access needed)",
            "critical": True
        }
    ]
    
    passed_tests = 0
    critical_passed = 0
    total_critical = sum(1 for test in tests if test["critical"])
    
    for i, test in enumerate(tests, 1):
        print(f"\n--- Test {i}/{len(tests)} ---")
        
        success = test_query(test["query"], test["description"])
        
        if success:
            passed_tests += 1
            if test["critical"]:
                critical_passed += 1
        
        # Add delay between tests to avoid rate limiting
        if i < len(tests):
            time.sleep(2)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total tests passed: {passed_tests}/{len(tests)}")
    print(f"Critical tests passed: {critical_passed}/{total_critical}")
    
    if passed_tests == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your service principal has proper permissions.")
        print("✅ Ready for deployment to Azure App Service.")
    elif critical_passed == total_critical:
        print("\n✅ CRITICAL TESTS PASSED!")
        print("✅ Core functionality working - minor issues may exist.")
        print("✅ Should work for deployment.")
    elif critical_passed > 0:
        print("\n⚠️  PARTIAL SUCCESS")
        print(f"✅ {critical_passed}/{total_critical} critical tests passed.")
        print("⚠️  Some permission issues detected.")
    else:
        print("\n❌ PERMISSION ISSUES DETECTED")
        print("❌ Service principal may not have proper workspace access.")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if critical_passed < total_critical:
        print("1. 🔑 Check service principal is added to Fabric workspace:")
        print("   - Go to https://app.fabric.microsoft.com")
        print("   - Navigate to your workspace → Settings → Manage access")
        print("   - Add 'fabric-data-agent-service' with Admin/Member role")
        
        print("\n2. 🛡️  Verify Azure AD API permissions:")
        print("   - Go to Azure Portal → Azure AD → App registrations")
        print("   - Find your app → API permissions")
        print("   - Ensure 'Fabric.ReadWrite.All' is granted with admin consent")
        
        print("\n3. 📊 Check data source permissions:")
        print("   - Ensure datasets/lakehouses are accessible to service principal")
        print("   - Verify Fabric Agent has access to required data sources")
    
    if passed_tests > critical_passed:
        print("4. 🔍 Some queries work - this suggests:")
        print("   - Basic permissions are OK")
        print("   - Specific data sources may need additional access")
        print("   - Check individual dataset/lakehouse permissions")
    
    print(f"\n5. 📖 For detailed troubleshooting, see:")
    print(f"   PERMISSION_TROUBLESHOOTING.md")

if __name__ == "__main__":
    main()