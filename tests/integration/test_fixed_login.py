"""
Test the fixed login implementation (matching MarcoAssistant)
"""
import requests
import yaml

# Load credentials
with open('config/devices.yaml', 'r') as f:
    config = yaml.safe_load(f)

device = config['devices']['AA:BB:CC:DD:EE:FF']
username = device['phoneshop_username']
password = device['phoneshop_password']

print("="*60)
print("  Fixed Login Test (MarcoAssistant Method)")
print("="*60)
print()

BASE_URL = "https://YOUR_PHONESHOP_API_HOST"

print(f"Username: {username}")
print(f"Password: {'*' * len(password)}")
print()

# Test the fixed method
print("Testing: POST /YOUR_SHOP_API_PATH with query params")
print("-" * 60)
try:
    params = {"username": username, "password": password}
    response = requests.post(
        f"{BASE_URL}/YOUR_SHOP_API_PATH",
        params=params,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS - Login worked!")
        print()
        
        # Check for token in Authorization header
        token = response.headers.get("Authorization")
        if token:
            print(f"✅ Token found in Authorization header")
            print(f"   Token (first 30 chars): {token[:30]}...")
        else:
            print("❌ No Authorization header found")
            print(f"   Available headers: {list(response.headers.keys())}")
        
        print()
        
        # Check response body
        try:
            data = response.json()
            print(f"✅ Response JSON parsed successfully")
            print(f"   Shop ID: {data.get('shopId')}")
            print(f"   User data keys: {list(data.keys())}")
        except:
            print("❌ Failed to parse JSON response")
            print(f"   Response body: {response.text[:200]}")
        
        print()
        
        # Test API call with token
        if token:
            print("Testing API call with token...")
            print("-" * 60)
            
            api_response = requests.get(
                f"{BASE_URL}/YOUR_SHOP_API_PATH",
                headers={"Authorization": token},
                timeout=10
            )
            
            print(f"API Status: {api_response.status_code}")
            
            if api_response.status_code == 200:
                print("✅ API call successful with token!")
                print(f"   Response (first 100 chars): {api_response.text[:100]}")
            else:
                print(f"❌ API call failed: {api_response.status_code}")
                print(f"   Response: {api_response.text[:200]}")
    else:
        print(f"❌ Login failed with status {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()
print("="*60)
print("  Result")
print("="*60)
print()
print("If this test succeeds, the server will now work correctly!")
print("Restart the server to apply the fix: start_server.bat")
