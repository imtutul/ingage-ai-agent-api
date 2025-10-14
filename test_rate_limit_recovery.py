#!/usr/bin/env python3
"""
Rate limit testing script - waits for rate limit to reset and tests the query
"""
import requests
import json
import time
from datetime import datetime, timezone

def check_rate_limit_status():
    """Check if we're still rate limited"""
    try:
        response = requests.post(
            "http://127.0.0.1:3000/query",
            json={"query": "What can you help me with?"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            
            # Check for rate limit error
            if 'Error code: 429' in response_text or 'RequestBlocked' in response_text:
                return False, response_text
            else:
                return True, response_text
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, str(e)

def wait_for_rate_limit_reset():
    """Wait for rate limit to reset and test"""
    reset_time_utc = datetime(2025, 10, 14, 12, 11, 5, tzinfo=timezone.utc)
    current_time = datetime.now(timezone.utc)
    
    if current_time < reset_time_utc:
        wait_seconds = (reset_time_utc - current_time).total_seconds()
        print(f"⏰ Rate limit active until {reset_time_utc.strftime('%H:%M:%S UTC')}")
        print(f"🕐 Waiting {int(wait_seconds)} seconds for reset...")
        
        # Wait with countdown
        while wait_seconds > 0:
            mins, secs = divmod(int(wait_seconds), 60)
            print(f"\r⏳ Time remaining: {mins:02d}:{secs:02d}", end="", flush=True)
            time.sleep(1)
            wait_seconds -= 1
        
        print("\n🔄 Rate limit should be reset now!")
    else:
        print("✅ Rate limit should already be reset!")

def test_queries_after_reset():
    """Test different queries after rate limit reset"""
    print("\n🧪 Testing queries after rate limit reset...")
    
    test_queries = [
        {
            "query": "What can you help me with?",
            "description": "General capability test (should work)"
        },
        {
            "query": "What data sources are available?", 
            "description": "Data source discovery test"
        },
        {
            "query": "how many member we have?",
            "description": "Original member count query"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {test['description']} ---")
        print(f"Query: {test['query']}")
        
        is_working, response = check_rate_limit_status()
        
        if is_working:
            print("✅ Success! Response:")
            print(f"   {response[:150]}...")
        else:
            print("❌ Still rate limited or error:")
            print(f"   {response[:150]}...")
            
            if '429' in response:
                print("⚠️  Still rate limited - may need to wait longer")
                break
        
        # Small delay between tests to avoid triggering rate limit again
        if i < len(test_queries):
            print("⏳ Waiting 10 seconds before next test...")
            time.sleep(10)
    
    print("\n📊 Testing complete!")

def main():
    """Main function"""
    print("🚦 Fabric Data Agent Rate Limit Recovery Tool")
    print("=" * 50)
    
    # Check current status
    print("🔍 Checking current rate limit status...")
    is_working, response = check_rate_limit_status()
    
    if is_working:
        print("✅ No rate limit detected! API is working.")
        print(f"Response: {response[:100]}...")
    else:
        print("⚠️  Rate limit detected:")
        print(f"   {response[:200]}...")
        
        # Wait for reset
        wait_for_rate_limit_reset()
        
        # Test after reset
        test_queries_after_reset()

if __name__ == "__main__":
    main()