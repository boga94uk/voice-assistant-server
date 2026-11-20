"""
Test Phoneshop API login to debug 401 errors.
"""
import requests
import json
import yaml

# Load credentials from devices.yaml
with open('config/devices.yaml', 'r') as f:
    config = yaml.safe_load(f)

device = config['devices']['AA:BB:CC:DD:EE:FF']
username = device['phoneshop_username']
password = device['phoneshop_password']

print("="*60)
print("  Phoneshop API Login Test")
print("="*60)
print()
print(f"Username: {username}")
print(f"Password: {'*' * len(password)}")
print()

BASE_URL = "https://YOUR_PHONESHOP_API_HOST"

# Test 1: Current implementation (JSON body)
print("Test 1: Login with JSON body (current implementation)")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/YOUR_SHOP_API_PATH",
        json={"username": username, "password": password},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text[:500]}")
    
    if response.status_code == 200:
        print("✅ SUCCESS - Login worked with JSON body!")
        data = response.json()
        print(f"Token: {data.get('token', 'N/A')[:20]}...")
        print(f"Shop ID: {data.get('user', {}).get('shopId', 'N/A')}")
    else:
        print(f"❌ FAILED - Status {response.status_code}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()

# Test 2: Try with form data instead
print("Test 2: Login with form data")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/YOUR_SHOP_API_PATH",
        data={"username": username, "password": password},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text[:500]}")
    
    if response.status_code == 200:
        print("✅ SUCCESS - Login worked with form data!")
        data = response.json()
        print(f"Token: {data.get('token', 'N/A')[:20]}...")
    else:
        print(f"❌ FAILED - Status {response.status_code}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()

# Test 3: Try with Content-Type header
print("Test 3: Login with explicit Content-Type")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/YOUR_SHOP_API_PATH",
        json={"username": username, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text[:500]}")
    
    if response.status_code == 200:
        print("✅ SUCCESS - Login worked with Content-Type header!")
        data = response.json()
        print(f"Token: {data.get('token', 'N/A')[:20]}...")
    else:
        print(f"❌ FAILED - Status {response.status_code}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()

# Test 4: Check if credentials have special characters that need escaping
print("Test 4: Credential validation")
print("-" * 60)
print(f"Username length: {len(username)}")
print(f"Password length: {len(password)}")
print(f"Username has spaces: {' ' in username}")
print(f"Password has spaces: {' ' in password}")
print(f"Username contains: {repr(username)}")
print(f"Password contains: {repr(password)}")

print()
print("="*60)
print("  Diagnosis")
print("="*60)
print()
print("If all tests fail with 401:")
print("1. Verify credentials work at https://YOUR_PHONESHOP_API_HOST")
print("2. Check if there's a different API endpoint for login")
print("3. Check if the API requires additional headers/authentication")
print("4. Contact Phoneshop support about API access")
print()
print("If one test succeeds:")
print("→ Update phoneshop_api.py to use the working method")
