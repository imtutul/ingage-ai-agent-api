#!/usr/bin/env python3
"""
Test client for the Fabric Data Agent FastAPI server

This script demonstrates how to interact with the FastAPI endpoints.
"""

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file if present
import requests
import json
import sys
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check: {data['status']}")
        print(f"📊 Fabric client initialized: {data['fabric_client_initialized']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_simple_query(query: str):
    """Test the simple query endpoint"""
    print(f"\n📝 Testing simple query: '{query}'")
    try:
        payload = {"query": query}
        response = requests.post(f"{BASE_URL}/query", json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data["success"]:
            print(f"✅ Query successful!")
            print(f"💬 Response: {data['response'][:200]}{'...' if len(data['response']) > 200 else ''}")
        else:
            print(f"❌ Query failed: {data.get('error', 'Unknown error')}")
        
        return data
    except Exception as e:
        print(f"❌ Simple query failed: {e}")
        return None

def test_detailed_query(query: str):
    """Test the detailed query endpoint"""
    print(f"\n📊 Testing detailed query: '{query}'")
    try:
        payload = {"query": query, "include_details": True}
        response = requests.post(f"{BASE_URL}/query/detailed", json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data["success"]:
            print(f"✅ Detailed query successful!")
            print(f"💬 Response: {data['response'][:200]}{'...' if len(data['response']) > 200 else ''}")
            print(f"📊 Run status: {data.get('run_status', 'N/A')}")
            print(f"🔢 Steps: {data.get('steps_count', 'N/A')}")
            print(f"💌 Messages: {data.get('messages_count', 'N/A')}")
            
            if data.get('sql_query'):
                print(f"🗃️ SQL Query: {data['sql_query'][:100]}{'...' if len(data['sql_query']) > 100 else ''}")
            
            if data.get('data_preview'):
                print(f"📋 Data preview ({len(data['data_preview'])} lines):")
                for i, line in enumerate(data['data_preview'][:3]):
                    print(f"   {i+1}: {line[:80]}{'...' if len(line) > 80 else ''}")
        else:
            print(f"❌ Detailed query failed: {data.get('error', 'Unknown error')}")
        
        return data
    except Exception as e:
        print(f"❌ Detailed query failed: {e}")
        return None

def main():
    """Run the test suite"""
    print("🧪 Fabric Data Agent API Test Client")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("❌ Server not healthy. Make sure the server is running.")
        sys.exit(1)
    
    # Sample queries
    queries = [
        "What data is available in the lakehouse?",
        "Show me information about the tables",
        "Get the top 5 records from any available table"
    ]
    
    # Test simple queries
    print("\n" + "="*50)
    print("Testing Simple Queries")
    print("="*50)
    
    for query in queries:
        result = test_simple_query(query)
        if result:
            print(f"📝 Full response saved to query_response_{len(query)}.json")
            with open(f"query_response_{len(query)}.json", "w") as f:
                json.dump(result, f, indent=2)
    
    # Test detailed queries
    print("\n" + "="*50)
    print("Testing Detailed Queries")
    print("="*50)
    
    for query in queries[:2]:  # Test fewer detailed queries
        result = test_detailed_query(query)
        if result:
            print(f"📊 Full detailed response saved to detailed_response_{len(query)}.json")
            with open(f"detailed_response_{len(query)}.json", "w") as f:
                json.dump(result, f, indent=2)
    
    print("\n✅ Test suite completed!")

if __name__ == "__main__":
    main()