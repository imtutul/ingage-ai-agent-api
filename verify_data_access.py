#!/usr/bin/env python3
"""
Fabric Data Access Verification Script
This script helps identify the specific permission issue preventing data access.
"""
import requests
import json
import time

def test_fabric_query(query, description):
    """Test a query and provide detailed analysis"""
    print(f"\n🧪 {description}")
    print(f"   Query: {query}")
    
    try:
        response = requests.post(
            "http://127.0.0.1:3001/query",
            json={"query": query},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            
            print(f"   ✅ HTTP 200 OK")
            print(f"   📝 Response: {data.get('response', '')}")
            
            # Detailed analysis
            if 'technical issue' in response_text and 'data warehouse' in response_text:
                print(f"   🔍 Analysis: DATA SOURCE PERMISSION ISSUE")
                print(f"       - Service principal can authenticate")
                print(f"       - Service principal can access the agent")
                print(f"       - Service principal CANNOT access data sources")
                return "data_source_blocked"
            elif 'unable to retrieve' in response_text:
                print(f"   🔍 Analysis: SPECIFIC TABLE/QUERY ISSUE")
                print(f"       - May be table-specific permissions")
                print(f"       - Or query-specific limitations")
                return "query_specific_issue"
            elif any(word in response_text for word in ['member', 'count', 'data', 'table', 'rows']) and 'unable' not in response_text:
                print(f"   🎉 Analysis: SUCCESS - Got actual data!")
                return "success"
            elif 'help' in response_text or 'assist' in response_text:
                print(f"   ✅ Analysis: AGENT RESPONDING - Basic access working")
                return "agent_accessible"
            else:
                print(f"   ❓ Analysis: UNKNOWN RESPONSE PATTERN")
                return "unknown"
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
            return "http_error"
            
    except Exception as e:
        print(f"   💥 Error: {e}")
        return "connection_error"

def main():
    """Run systematic permission verification"""
    print("🔍 Fabric Data Access Permission Verification")
    print("=" * 60)
    
    # Progressive test queries to isolate the exact issue
    tests = [
        {
            "query": "Hello, can you hear me?",
            "description": "Basic connectivity test",
        },
        {
            "query": "What is your purpose and what can you help me with?",
            "description": "Agent capability verification",
        },
        {
            "query": "What data sources do you have access to?",
            "description": "Data source discovery",
        },
        {
            "query": "Can you see any tables in our system?",
            "description": "Table visibility test",
        },
        {
            "query": "Show me the structure of our database",
            "description": "Schema access test",
        },
        {
            "query": "What tables contain member information?",
            "description": "Member table discovery",
        },
        {
            "query": "Can you access the Dim_Member table?",
            "description": "Specific table access test",
        },
        {
            "query": "How many rows are in our database?",
            "description": "General count query",
        },
        {
            "query": "How many member we have?",
            "description": "Original failing query",
        }
    ]
    
    results = {}
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}/{len(tests)}")
        
        result = test_fabric_query(test["query"], test["description"])
        results[test["description"]] = {
            "query": test["query"],
            "result": result
        }
        
        # Brief pause between tests
        if i < len(tests):
            time.sleep(2)
    
    # Analysis and recommendations
    print(f"\n{'=' * 60}")
    print("📊 PERMISSION ANALYSIS SUMMARY")
    print(f"{'=' * 60}")
    
    success_count = sum(1 for r in results.values() if r['result'] == 'success')
    agent_accessible = sum(1 for r in results.values() if r['result'] == 'agent_accessible')
    data_blocked = sum(1 for r in results.values() if r['result'] == 'data_source_blocked')
    
    print(f"✅ Successful data queries: {success_count}")
    print(f"🤖 Agent accessible (basic): {agent_accessible}")
    print(f"🚫 Data source blocked: {data_blocked}")
    
    # Detailed diagnosis
    print(f"\n🔍 DIAGNOSIS:")
    
    if success_count > 0:
        print("🎉 GREAT NEWS: Some data queries are working!")
        print("   - Service principal authentication: ✅ Working")
        print("   - Workspace permissions: ✅ Working")
        print("   - Data source access: ✅ Working")
        print("   - Issue may be query-specific or table-specific")
    elif agent_accessible > 0 and data_blocked > 0:
        print("🔧 PERMISSION ISSUE IDENTIFIED:")
        print("   - Service principal authentication: ✅ Working")
        print("   - Agent accessibility: ✅ Working")
        print("   - Data source access: ❌ BLOCKED")
        print("\n💡 REQUIRED ACTIONS:")
        print("   1. Check individual dataset permissions in Fabric workspace")
        print("   2. Add service principal to each dataset/lakehouse/warehouse")
        print("   3. Verify Data Agent has access to required data sources")
        print("   4. Check if Dim_Member table exists and is accessible")
    elif agent_accessible > 0:
        print("🤔 PARTIAL ACCESS:")
        print("   - Basic agent access working")
        print("   - May need specific data source permissions")
    else:
        print("❌ FUNDAMENTAL ISSUE:")
        print("   - May have authentication or configuration problems")
        print("   - Check service principal setup")
    
    # Specific recommendations based on patterns
    print(f"\n📋 SPECIFIC NEXT STEPS:")
    
    if data_blocked > success_count:
        print("🎯 PRIMARY ISSUE: Data Source Permissions")
        print("   1. In Fabric workspace, check these items:")
        print("      • Datasets (look for Dim_Member or similar)")
        print("      • Lakehouses (check if member data is here)")
        print("      • Warehouses (SQL-based data sources)")
        print("      • SQL endpoints")
        print("   2. For each data source:")
        print("      • Open the data source")
        print("      • Go to Settings → Security or Manage permissions")
        print("      • Add 'fabric-data-agent-service' with Read permissions")
        print("   3. Alternative: Check Data Agent configuration")
        print("      • Ensure Data Agent skill has proper data source connections")
        print("      • Verify the agent isn't using delegated permissions")
    
    if success_count == 0 and agent_accessible == 0:
        print("🎯 PRIMARY ISSUE: Basic Access")
        print("   1. Verify service principal is in workspace as Admin")
        print("   2. Check Azure AD API permissions and admin consent")
        print("   3. Test Data Agent with your user account directly")
    
    print(f"\n🔗 USEFUL LINKS:")
    print("   • Fabric workspace: https://app.fabric.microsoft.com")
    print("   • Azure AD: https://portal.azure.com")
    print("   • Your workspace ID: d09dbe6d-b3f5-4188-a375-482e01aa1213")
    
    print(f"\n📞 IF STILL STUCK:")
    print("   Consider creating a new service principal with different permissions")
    print("   Or test with Managed Identity when deploying to Azure App Service")

if __name__ == "__main__":
    main()