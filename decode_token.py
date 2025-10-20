#!/usr/bin/env python3
"""
Quick diagnostic script to check what token your backend is receiving
Run this while your backend is running to see token details
"""

import base64
import json

def decode_token(token_string):
    """Decode a JWT token and display its contents"""
    try:
        # Split the token
        parts = token_string.split('.')
        
        if len(parts) != 3:
            print("❌ Invalid JWT format. Token should have 3 parts.")
            return
        
        # Decode header
        header_data = parts[0] + '=' * (4 - len(parts[0]) % 4)
        header = json.loads(base64.b64decode(header_data))
        
        # Decode payload
        payload_data = parts[1] + '=' * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.b64decode(payload_data))
        
        print("\n" + "="*80)
        print("🔍 TOKEN ANALYSIS RESULTS")
        print("="*80)
        
        # Check audience
        audience = payload.get('aud', 'NOT FOUND')
        print(f"\n📍 Audience: {audience}")
        
        if 'api.fabric.microsoft.com' in audience:
            print("   ❌ PROBLEM: Using Fabric API endpoint (won't have scopes!)")
            print("   💡 Should be: https://analysis.windows.net/powerbi/api")
        elif 'analysis.windows.net/powerbi/api' in audience:
            print("   ✅ CORRECT: Using Power BI Service endpoint")
        else:
            print("   ⚠️  Unexpected audience")
        
        # Check scopes
        scopes = payload.get('scp') or payload.get('scope')
        print(f"\n🔐 Scopes: {scopes if scopes else '❌ NONE - THIS IS THE PROBLEM!'}")
        
        if not scopes:
            print("   ❌ CRITICAL: Token has NO scopes!")
            print("   💡 This is why you get 403 error!")
        else:
            print(f"   ✅ Token has scopes: {scopes}")
        
        # Check roles
        roles = payload.get('roles')
        if roles:
            print(f"\n👤 Roles: {', '.join(roles)}")
        
        # User info
        user = payload.get('upn') or payload.get('unique_name') or payload.get('preferred_username')
        print(f"\n👤 User: {user}")
        print(f"📧 App ID: {payload.get('appid', 'N/A')}")
        
        # Token timing
        from datetime import datetime
        iat = datetime.fromtimestamp(payload.get('iat', 0))
        exp = datetime.fromtimestamp(payload.get('exp', 0))
        print(f"\n⏰ Issued: {iat}")
        print(f"⏰ Expires: {exp}")
        
        # Full payload
        print("\n" + "="*80)
        print("📋 FULL TOKEN PAYLOAD:")
        print("="*80)
        print(json.dumps(payload, indent=2))
        
        # Diagnosis
        print("\n" + "="*80)
        print("🎯 DIAGNOSIS:")
        print("="*80)
        
        if not scopes and 'api.fabric.microsoft.com' in audience:
            print("""
❌ ROOT CAUSE IDENTIFIED:
   - Token audience is Fabric API endpoint
   - Token has NO scopes
   - This is why Fabric API returns 403 "token does not have required scopes"

✅ FIX:
   1. Change frontend scope request from:
      'https://api.fabric.microsoft.com/.default'
      
      TO:
      'https://analysis.windows.net/powerbi/api/.default'
   
   2. Add Power BI Service API permissions in Azure AD:
      - Go to Azure Portal → App registrations
      - Find your app → API permissions
      - Add Power BI Service permissions
      - Grant admin consent
   
   3. Test in incognito mode after changes
""")
        elif scopes and 'analysis.windows.net/powerbi/api' in audience:
            print("""
✅ TOKEN LOOKS GOOD!
   - Correct audience (Power BI Service)
   - Has required scopes
   
   If still getting 403, check:
   - User has access to Fabric workspace
   - Workspace ID is correct
   - AI Skill ID is correct
""")
        else:
            print("""
⚠️  UNEXPECTED CONFIGURATION
   - Check token audience and scopes above
   - See CRITICAL_FIX_NO_SCOPES.md for guidance
""")
        
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error decoding token: {e}")
        print("Make sure you pasted a complete JWT token.")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔍 TOKEN DECODER - Fix 403 Error                        ║
╚════════════════════════════════════════════════════════════════════════════╝

This script will analyze your Fabric token to diagnose the 403 error.

HOW TO GET YOUR TOKEN:
1. In your frontend, after login, open browser DevTools (F12)
2. Go to Network tab
3. Find the POST request to /auth/client-login
4. Look at the request payload
5. Copy the 'access_token' or 'fabric_token' value
6. Paste it below when prompted

The token is a long string starting with 'eyJ...'
""")
    
    print("\nPaste your token here (press Enter twice when done):")
    print("-" * 80)
    
    token = input().strip()
    
    if not token:
        print("❌ No token provided. Exiting.")
        exit(1)
    
    decode_token(token)
    
    print("\n\nPress Enter to exit...")
    input()
