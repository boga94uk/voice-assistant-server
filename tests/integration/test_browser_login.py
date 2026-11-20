"""
Test browser-style login endpoint (/login instead of /YOUR_SHOP_API_PATH)
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
print("  Browser-Style Login Test")
print("="*60)
print()

BASE_URL = "https://YOUR_PHONESHOP_API_HOST"

# Create a session to handle cookies
session = requests.Session()

# Test 1: Try /login endpoint with form data
print("Test 1: POST to /login (form-based)")
print("-" * 60)
try:
    response = session.post(
        f"{BASE_URL}/login",
        data={
            "username": username,
            "password": password
        },
        allow_redirects=False,  # Don't follow redirects so we can see them
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if 'Location' in response.headers:
        print(f"Redirect to: {response.headers['Location']}")
    
    if 'Set-Cookie' in response.headers:
        print(f"Sets cookies: YES")
        print(f"Cookies: {session.cookies.get_dict()}")
    
    print(f"Response Body (first 200 chars): {response.text[:200]}")
    print()
    
    if response.status_code == 302 or response.status_code == 200:
        print("✅ Login appears successful!")
        print()
        
        # Try to access an API endpoint with the session
        print("Test 2: Access API with session cookies")
        print("-" * 60)
        api_response = session.get(
            f"{BASE_URL}/YOUR_SHOP_API_PATH",
            timeout=10
        )
        print(f"API Status: {api_response.status_code}")
        print(f"API Response (first 200 chars): {api_response.text[:200]}")
        
        if api_response.status_code == 200:
            print("✅ API access works with session cookies!")
        else:
            print("❌ API access failed even with cookies")
    else:
        print(f"❌ Login failed with status {response.status_code}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()

# Test 2: Check if there's a CSRF token requirement
print("Test 3: Check for CSRF tokens")
print("-" * 60)
try:
    # First GET the login page to see if CSRF token is needed
    login_page = session.get(f"{BASE_URL}/login", timeout=10)
    print(f"Login page status: {login_page.status_code}")
    
    # Look for CSRF token in page
    if "csrf" in login_page.text.lower():
        print("⚠️  CSRF token detected in login page")
        print("   Browser-based auth requires scraping CSRF token first")
    else:
        print("ℹ️  No CSRF token found")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()
print("="*60)
print("  Summary")
print("="*60)
print()
print("If browser login works but API doesn't:")
print("→ The system uses session cookies (not JWT tokens)")
print("→ Need to:")
print("  1. Login via /login (get session cookie)")
print("  2. Store session cookie")
print("  3. Use cookie for all API requests")
print()
print("OR:")
print("→ Contact Phoneshop to get JWT API credentials")
print("→ Browser login and API login might be separate systems")
