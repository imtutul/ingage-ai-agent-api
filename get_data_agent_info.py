#!/usr/bin/env python3
"""
Get detailed information about the Data Agent item
"""
import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
import requests
import json

load_dotenv()

def get_data_agent_details():
    """Get detailed information about our Data Agent"""
    
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
    TENANT_ID = os.getenv("TENANT_ID")
    
    print("🔍 Getting Data Agent Item Details")
    print("=" * 40)
    
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    
    token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
    
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }
    
    workspace_id = "d09dbe6d-b3f5-4188-a375-482e01aa1213"
    skill_id = "a2e01f9d-4d21-4d87-af2c-5f35a9edae9b"
    
    # Get the item details
    item_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{skill_id}"
    
    try:
        response = requests.get(item_url, headers=headers, timeout=10)
        print(f"📊 Item Details Response: {response.status_code}")
        
        if response.status_code == 200:
            item = response.json()
            print(f"✅ Item Details:")
            print(json.dumps(item, indent=2))
            
            # Check what type of item this is
            item_type = item.get('type')
            print(f"\n🎯 Item Type: {item_type}")
            
            # Try to get more details based on the type
            if item_type:
                type_specific_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/{item_type.lower()}s/{skill_id}"
                print(f"\n🔍 Trying type-specific endpoint: {type_specific_url}")
                
                response = requests.get(type_specific_url, headers=headers, timeout=10)
                print(f"📊 Type-specific Response: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ Type-specific details:")
                    details = response.json()
                    print(json.dumps(details, indent=2)[:1000])
                else:
                    print(f"❌ Type-specific failed: {response.text[:200]}")
                    
        else:
            print(f"❌ Cannot get item details: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

def check_fabric_api_documentation():
    """Check what AI-related endpoints are available"""
    
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
    TENANT_ID = os.getenv("TENANT_ID")
    
    print(f"\n🔍 Checking Available AI Endpoints")
    print("=" * 40)
    
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    
    token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
    
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }
    
    workspace_id = "d09dbe6d-b3f5-4188-a375-482e01aa1213"
    
    # Test different possible AI-related endpoints
    ai_endpoints = [
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataAgents",
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/aiagents", 
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/conversationalAI",
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/chatbots",
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/assistants",
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/copilots",
    ]
    
    for endpoint in ai_endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=5)
            print(f"📊 {endpoint.split('/')[-1]}: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Found working endpoint!")
                try:
                    data = response.json()
                    if 'value' in data and len(data['value']) > 0:
                        print(f"   📋 Contains {len(data['value'])} items")
                except:
                    pass
            elif response.status_code == 404:
                print(f"   ❌ Not found")
            elif response.status_code == 400:
                print(f"   ⚠️ Bad request (might not be valid endpoint)")
            else:
                print(f"   ❓ {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   💥 Error: {str(e)[:50]}")

def test_copilot_endpoints():
    """Test Copilot-specific endpoints that might work"""
    
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
    TENANT_ID = os.getenv("TENANT_ID")
    
    print(f"\n🤖 Testing Copilot/Assistant Endpoints")
    print("=" * 40)
    
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    
    token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
    
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }
    
    workspace_id = "d09dbe6d-b3f5-4188-a375-482e01aa1213"
    skill_id = "a2e01f9d-4d21-4d87-af2c-5f35a9edae9b"
    
    # Based on the original URL structure, try variations
    copilot_endpoints = [
        # Try different base paths
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/copilots/{skill_id}/chat/completions",
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/assistants/{skill_id}/chat/completions", 
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataAgents/{skill_id}/chat/completions",
        
        # Try without /chat/completions
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/copilots/{skill_id}",
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/assistants/{skill_id}",
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataAgents/{skill_id}",
    ]
    
    for endpoint in copilot_endpoints:
        print(f"\n🎯 Testing: {endpoint}")
        
        try:
            # Test GET first
            response = requests.get(endpoint, headers=headers, timeout=5)
            print(f"   📊 GET: {response.status_code}")
            
            if response.status_code in [200, 405]:  # 405 means method not allowed but endpoint exists
                print(f"   ✅ Endpoint exists! Trying POST...")
                
                # Try POST with simple data
                test_data = {
                    "messages": [{"role": "user", "content": "hello"}]
                }
                
                response = requests.post(endpoint, headers=headers, json=test_data, timeout=10)
                print(f"   📊 POST: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   🎉 SUCCESS! This endpoint works!")
                    print(f"   📄 Response: {response.text[:200]}")
                else:
                    print(f"   ❌ POST failed: {response.text[:200]}")
            else:
                print(f"   ❌ Not found: {response.text[:100] if response.text else 'No response'}")
                
        except Exception as e:
            print(f"   💥 Exception: {str(e)[:100]}")

if __name__ == "__main__":
    get_data_agent_details()
    check_fabric_api_documentation()
    test_copilot_endpoints()