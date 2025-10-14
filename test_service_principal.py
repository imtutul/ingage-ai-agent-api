#!/usr/bin/env python3
"""
Test script to validate service principal authentication with Fabric Data Agent
Run this script after setting up your Azure AD App Registration to verify authentication works.
"""
import os
import sys
from pathlib import Path

# Add the current directory to the Python path so we can import our modules
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from fabric_data_agent_client import FabricDataAgentClient
    from azure.identity import ClientSecretCredential
    import asyncio
    import logging
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install required packages:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if all required environment variables are set."""
    required_vars = ['TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET', 'DATA_AGENT_URL']
    missing_vars = []
    
    print("🔍 Checking environment variables...")
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"   ❌ {var}: Not set")
        elif var == 'CLIENT_SECRET':
            print(f"   ✅ {var}: {'*' * min(len(value), 20)} (hidden)")
        else:
            print(f"   ✅ {var}: {value}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with the correct values.")
        return False
    
    print("✅ All required environment variables are set!")
    return True

def test_credential_creation():
    """Test creating Azure credentials."""
    print("\n🔑 Testing credential creation...")
    try:
        tenant_id = os.getenv('TENANT_ID')
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        print("✅ Azure credentials created successfully!")
        return credential
    except Exception as e:
        print(f"❌ Failed to create credentials: {e}")
        return None

async def test_token_acquisition(credential):
    """Test acquiring an access token."""
    print("\n🎫 Testing token acquisition...")
    try:
        # Try to get a token for Microsoft Graph (basic test)
        token = credential.get_token("https://graph.microsoft.com/.default")
        if token and token.token:
            print("✅ Successfully acquired access token!")
            print(f"   Token expires: {token.expires_on}")
            return True
        else:
            print("❌ Failed to acquire token - empty response")
            return False
    except Exception as e:
        print(f"❌ Failed to acquire token: {e}")
        return False

async def test_fabric_client_initialization():
    """Test initializing the Fabric Data Agent client."""
    print("\n🏭 Testing Fabric Data Agent client initialization...")
    try:
        tenant_id = os.getenv('TENANT_ID')
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        data_agent_url = os.getenv('DATA_AGENT_URL')
        
        client = FabricDataAgentClient(
            data_agent_url=data_agent_url,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        print("✅ Fabric Data Agent client initialized successfully!")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize Fabric client: {e}")
        return None

async def test_fabric_query(client):
    """Test making a query to the Fabric Data Agent."""
    print("\n💬 Testing Fabric Data Agent query...")
    try:
        test_query = "What data sources are available?"
        print(f"   Query: {test_query}")
        
        response = client.ask(test_query)
        
        if response:
            print("✅ Query executed successfully!")
            print(f"   Response preview: {str(response)[:200]}...")
            return True
        else:
            print("❌ Query returned empty response")
            return False
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🧪 Fabric Data Agent Service Principal Authentication Test")
    print("=" * 60)
    
    success_count = 0
    total_tests = 5
    
    # Test 1: Environment variables
    if check_environment_variables():
        success_count += 1
    else:
        print("\n❌ Cannot continue without proper environment configuration.")
        return
    
    # Test 2: Credential creation
    credential = test_credential_creation()
    if credential:
        success_count += 1
    else:
        print("\n❌ Cannot continue without valid credentials.")
        return
    
    # Test 3: Token acquisition
    if await test_token_acquisition(credential):
        success_count += 1
    else:
        print("\n⚠️  Token acquisition failed - check your Azure AD configuration.")
    
    # Test 4: Fabric client initialization
    fabric_client = await test_fabric_client_initialization()
    if fabric_client:
        success_count += 1
        
        # Test 5: Fabric query
        if await test_fabric_query(fabric_client):
            success_count += 1
    
    # Summary
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Your service principal authentication is configured correctly.")
        print("You can now deploy to Azure App Service with confidence.")
    elif success_count >= 3:
        print("⚠️  Most tests passed. Check the failed tests and Azure AD configuration.")
        print("You may still be able to deploy, but some functionality might not work.")
    else:
        print("❌ Multiple tests failed. Please review your configuration before deploying.")
        print("Check the SERVICE_PRINCIPAL_SETUP.md guide for detailed instructions.")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if success_count < 3:
        print("   1. Verify your Azure AD App Registration exists")
        print("   2. Check that CLIENT_ID and CLIENT_SECRET are correct")
        print("   3. Ensure the service principal has proper permissions")
        print("   4. Verify the DATA_AGENT_URL is correct")
    elif success_count < 5:
        print("   1. Add the service principal to your Fabric workspace")
        print("   2. Grant necessary API permissions in Azure AD")
        print("   3. Ensure admin consent has been granted")
    else:
        print("   1. Deploy to Azure App Service")
        print("   2. Configure the same environment variables in App Service")
        print("   3. Test the deployed endpoints")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)