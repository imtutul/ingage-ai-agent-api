#!/usr/bin/env python3
"""
Test script to verify that conversation history responses are not duplicated
"""

import requests
import json

def test_conversation_response_fix():
    """Test that responses don't include conversation history"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Conversation History Response Fix")
    print("=" * 60)
    
    # First, make an initial query to establish some history
    print("\n📋 Step 1: Making initial query")
    initial_query = {
        "query": "Show me top 3 members with open care gaps"
    }
    
    try:
        response1 = requests.post(f"{base_url}/query", json=initial_query, timeout=60)
        print(f"   Status Code: {response1.status_code}")
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"   ✅ Success: {data1.get('success', False)}")
            initial_response = data1.get('response', '')
            print(f"   📝 Response Length: {len(initial_response)} characters")
            print(f"   📝 Response Preview: {initial_response[:150]}...")
            
            # Now make a follow-up query with conversation history
            print(f"\n📋 Step 2: Making follow-up query WITH conversation history")
            
            conversation_history = [
                {
                    "role": "user",
                    "content": "Show me top 3 members with open care gaps"
                },
                {
                    "role": "assistant",
                    "content": initial_response
                }
            ]
            
            followup_query = {
                "query": "Tell me more about the first member",
                "conversation_history": conversation_history
            }
            
            response2 = requests.post(f"{base_url}/query", json=followup_query, timeout=60)
            print(f"   Status Code: {response2.status_code}")
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"   ✅ Success: {data2.get('success', False)}")
                followup_response = data2.get('response', '')
                print(f"   📝 Response Length: {len(followup_response)} characters")
                print(f"   📝 Response Preview: {followup_response[:150]}...")
                
                # Check if the response contains the previous response (which would be bad)
                if initial_response.strip() in followup_response:
                    print(f"   ❌ PROBLEM: Follow-up response contains previous response!")
                    print(f"   🔍 This indicates conversation history is being included in the response.")
                else:
                    print(f"   ✅ GOOD: Follow-up response is unique and doesn't contain previous response")
                
                # Check for repeated content patterns
                lines = followup_response.split('\n')
                unique_lines = set(lines)
                if len(lines) > len(unique_lines) * 1.5:  # Allow some reasonable repetition
                    print(f"   ⚠️ WARNING: Response may contain repeated content")
                    print(f"   📊 Total lines: {len(lines)}, Unique lines: {len(unique_lines)}")
                else:
                    print(f"   ✅ GOOD: No excessive repetition detected")
                
            else:
                print(f"   ❌ Follow-up query failed: {response2.text}")
                
        else:
            print(f"   ❌ Initial query failed: {response1.text}")
            return
            
    except Exception as e:
        print(f"   💥 Exception: {e}")
        return
    
    print(f"\n📋 Step 3: Testing detailed query endpoint")
    
    try:
        detailed_query = {
            "query": "What are the care gaps for the second member?",
            "conversation_history": conversation_history
        }
        
        response3 = requests.post(f"{base_url}/query/detailed", json=detailed_query, timeout=60)
        print(f"   Status Code: {response3.status_code}")
        
        if response3.status_code == 200:
            data3 = response3.json()
            print(f"   ✅ Success: {data3.get('success', False)}")
            detailed_response = data3.get('response', '')
            print(f"   📝 Response Length: {len(detailed_response)} characters")
            print(f"   📝 Response Preview: {detailed_response[:150]}...")
            
            # Check for conversation history contamination
            if initial_response.strip() in detailed_response:
                print(f"   ❌ PROBLEM: Detailed response contains conversation history!")
            else:
                print(f"   ✅ GOOD: Detailed response is clean")
                
        else:
            print(f"   ❌ Detailed query failed: {response3.text}")
            
    except Exception as e:
        print(f"   💥 Exception during detailed query: {e}")
    
    print(f"\n✅ Conversation history response fix testing completed!")

if __name__ == "__main__":
    test_conversation_response_fix()