#!/usr/bin/env python3
"""
Test script to verify conversation history functionality
"""

import requests
import json

def test_conversation_history():
    """Test the conversation history feature"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Conversation History Feature")
    print("=" * 50)
    
    # Sample conversation history from the user's request
    sample_conversation = [
        {
            "role": "user",
            "content": "show me top 5 members with open gaps"
        },
        {
            "role": "assistant", 
            "content": "Here are the top 5 members with the highest number of open HEDIS care gaps (where a care gap is defined as a HEDIS measure with ComplianceFlag = 'N'):\n\n| Member ID      | First Name | Last Name | Date of Birth | Open Care Gaps |\n|----------------|------------|-----------|---------------|----------------|\n| 33331857       | Darryl     | Doe       | 1951-06-04    | 12             |\n| 37277786       | Jannie     | Doe       | 1951-06-05    | 11             |\n| C4085507101    | A          | Doe       | 1954-04-18    | 10             |\n| 37401443       | Ryan       | Doe       | 1968-01-24    | 10             |\n| 37189239       | Edgar      | Doe       | 1957-10-26    | 10             |\n\nWould you like a sample of their specific open gaps or additional details for these members?"
        },
        {
            "role": "user",
            "content": "tell me about the first member?"
        },
        {
            "role": "assistant",
            "content": "The first member in the dataset is Carlos Doe. Here are some details:\n\n- Date of Birth: April 17, 1945\n- Gender: Male\n- City: Oviedo\n- State: FL\n- Zip Code: 99501\n\nIf you need more information or details about this member's care history, let me know!"
        }
    ]
    
    # Test 1: Query without conversation history
    print("\n📋 Test 1: Query without conversation history")
    test_query_1 = {
        "query": "Hello, what can you help me with?"
    }
    
    try:
        response = requests.post(f"{base_url}/query", json=test_query_1, timeout=30)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('success', False)}")
            print(f"   📝 Response: {data.get('response', '')[:100]}...")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   💥 Exception: {e}")
    
    # Test 2: Query with conversation history
    print("\n📋 Test 2: Query with conversation history")
    test_query_2 = {
        "query": "What about the second member?",
        "conversation_history": sample_conversation
    }
    
    try:
        response = requests.post(f"{base_url}/query", json=test_query_2, timeout=60)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('success', False)}")
            print(f"   📝 Response: {data.get('response', '')[:200]}...")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   💥 Exception: {e}")
    
    # Test 3: Detailed query with conversation history
    print("\n📋 Test 3: Detailed query with conversation history")
    test_query_3 = {
        "query": "What are the specific care gaps for the second member?",
        "conversation_history": sample_conversation
    }
    
    try:
        response = requests.post(f"{base_url}/query/detailed", json=test_query_3, timeout=60)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('success', False)}")
            print(f"   📝 Response: {data.get('response', '')[:200]}...")
            print(f"   📊 Run Status: {data.get('run_status', 'N/A')}")
            print(f"   🔍 SQL Query: {data.get('sql_query', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   💥 Exception: {e}")
    
    print("\n✅ Conversation history testing completed!")

if __name__ == "__main__":
    test_conversation_history()