#!/usr/bin/env python3
"""
Complete Phoneshop API Test & Documentation Generator

Tests ALL GET endpoints + critical PUT endpoints for ticket management.
Saves complete request/response examples to api_documentation.json for LLM reference.

Usage:
    python test_api.py YOUR_PHONESHOP_USERNAME YOUR_PHONESHOP_PASSWORD

Output:
    - Console: Real-time test results
    - api_documentation.json: Complete API documentation with examples

Note: PUT endpoints modify tickets 1226 and 1227 (adds notes, changes status, etc.)
"""
import requests
import json
import sys

BASE_URL = "https://YOUR_PHONESHOP_API_HOST"

def login(username, password):
    """Login and get auth token"""
    print(f"\n🔐 Logging in as {username}...")
    try:
        response = requests.post(
            f"{BASE_URL}/YOUR_SHOP_API_PATH",
            params={"username": username, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.headers.get('Authorization')
            if token:
                print(f"✅ Login successful! Got token: {token[:50]}...")
                return token
            else:
                print("❌ Login successful but no token in response")
                return None
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Login exception: {e}")
        return None

def test_api(endpoint, token, method="GET", params=None, json_data=None):
    """Test an API endpoint with token auth"""
    url = f"{BASE_URL}/{endpoint}"
    
    print(f"\n{'='*80}")
    print(f"Testing: {method} {endpoint}")
    print(f"URL: {url}")
    if params:
        print(f"Params: {params}")
    if json_data:
        print(f"Body: {json_data}")
    print('='*80)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, params=params, json=json_data, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, params=params, json=json_data, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, params=params, json=json_data, timeout=10)
        else:
            print(f"Unsupported method: {method}")
            return None
        
        print(f"Status: {response.status_code}")
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": response.status_code,
            "params": params,
            "body": json_data,
            "response": None,
            "error": None
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\nResponse JSON ({len(json.dumps(data))} chars):")
                print(json.dumps(data, indent=2)[:2000])  # First 2000 chars
                if len(json.dumps(data)) > 2000:
                    print(f"\n... (truncated, total {len(json.dumps(data))} chars)")
                result["response"] = data
                return result
            except:
                print(f"Response text: {response.text[:500]}")
                result["response"] = response.text[:500]
                return result
        else:
            error_msg = response.text[:500] if response.text else "No error message"
            print(f"Error: {error_msg}")
            result["error"] = error_msg
            return result
            
    except Exception as e:
        print(f"Exception: {e}")
        return {
            "endpoint": endpoint,
            "method": method,
            "status": None,
            "params": params,
            "body": json_data,
            "response": None,
            "error": str(e)
        }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_api.py <username> <password> [ticket_id]")
        print("\nExample:")
        print("  python test_api.py worker1 pass123")
        print("  python test_api.py worker1 pass123 1234")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    ticket_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"Testing Phoneshop API as user: {username}")
    
    # Login first to get token
    token = login(username, password)
    if not token:
        print("\n❌ Failed to login. Cannot continue.")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("⚠️  WARNING: This will test PUT endpoints on tickets 1226 and 1227")
    print("   PUT operations will:")
    print("   - Change ticket status (start, complete, freeze, cancel)")
    print("   - Add notes and prices")
    print("   - Create invoices")
    print("   - Mark devices as collected")
    print("="*80)
    confirm = input("\nContinue with testing? (yes/no): ")
    if confirm.lower() != "yes":
        print("Aborted.")
        sys.exit(0)
    
    # ALL GET endpoints from documentation.json (excluding client/customer-facing ones)
    get_endpoints = [
        # Ticket GET endpoints (worker-facing only)
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all active/pending tickets"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all tickets (paginated)"),
        ("GET", "YOUR_SHOP_API_PATH", {"id": 1226}, None, "Get ticket by ID"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get used ticket tasks (autocomplete)"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get worker report"),
        
        # Chat GET endpoints (worker-facing only)
        ("GET", "YOUR_SHOP_API_PATH", {"ticketId": 1226}, None, "Get all chat messages for ticket"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get missed messages count"),
        
        # User GET endpoints (worker/admin only, NO client details)
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all users"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get users paginated"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all workers"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all users (simple)"),
        
        # Inventory GET endpoints (ALL)
        ("GET", "YOUR_SHOP_API_PATH", {"id": 462}, None, "Get inventory item by ID"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get shop inventory (paginated)"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get short inventory list"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all device models"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all brands with models"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all device locations"),
        
        # Shop GET endpoints (ALL)
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get my shop info"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get shop settings"),
        ("GET", "YOUR_SHOP_API_PATH", {"shopId": 52}, None, "Get shop image"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all worker shops"),
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all shops (admin)"),
        ("GET", "YOUR_SHOP_API_PATH", {"shopId": 52}, None, "Get shop by ID (admin)"),
        
        # Logs GET endpoint
        ("GET", "YOUR_SHOP_API_PATH", None, None, "Get all logs"),
    ]
    
    # PUT endpoints for ticket management (worker-facing only, NO client operations)
    put_endpoints = [
        # Ticket status changes (worker operations only)
        ("PUT", "YOUR_SHOP_API_PATH", {"id": 1226}, None, "Start working on ticket"),
        ("PUT", "YOUR_SHOP_API_PATH", {"id": 1226, "success": True}, None, "Complete ticket (success)"),
        ("PUT", "YOUR_SHOP_API_PATH", {"id": 1226}, None, "Mark device collected & create invoice"),
        ("PUT", "YOUR_SHOP_API_PATH", {"id": 1226}, None, "Create deposit invoice"),
        ("PUT", "YOUR_SHOP_API_PATH", {"id": 1226}, None, "Print ticket labels"),
        
        # Ticket update (notes, price, location - common LLM operations)
        ("PUT", "YOUR_SHOP_API_PATH", None, {
            "id": 1226,
            "deviceModel": "Lumia",
            "deviceBrand": "Nokia",
            "deviceLocation": "IN_THE_BACK",
            "problemExplanation": "back camera repair",
            "notes": "Test note added by API test script",
            "totalPrice": 50.0,
            "deposit": 10.0
        }, "Update ticket (notes, price, deposit, location)"),
        
        # Inventory item operations (updating quantity/requirements)
        ("PATCH", "YOUR_SHOP_API_PATH", {"id": 462, "count": 1, "isNeeded": True}, None, "Update required item count"),
    ]
    
    # POST endpoints for parts/inventory usage (NO brand/model creation)
    post_endpoints = [
        # Using parts on ticket
        ("POST", "YOUR_SHOP_API_PATH", None, {
            "ticketId": 1226,
            "itemId": 462,
            "quantity": 1
        }, "Use inventory part on ticket"),
    ]
    
    # Document/Printing endpoints (return PDF files)
    print_endpoints = [
        # Ticket & repair documents
        ("POST", "YOUR_SHOP_API_PATH", {"ticketId": 1226}, None, "Print ticket label (PDF)"),
        ("POST", "YOUR_SHOP_API_PATH", {"ticketId": 1226}, None, "Print repair tag (PDF)"),
        
        # Invoice documents
        ("GET", "YOUR_SHOP_API_PATH", {"ticketId": 1226}, None, "Print deposit invoice (PDF)"),
        
        # Tags (user card, price tags)
        ("POST", "YOUR_SHOP_API_PATH", {"itemId": 462}, None, "Print price tag for item (PDF)"),
    ]
    
    # Combine all endpoints
    endpoints = get_endpoints + put_endpoints + post_endpoints + print_endpoints
    
    print(f"\n\nTesting {len(endpoints)} endpoints...")
    print("=" * 80)
    
    all_results = []
    
    for method, endpoint, params, body, description in endpoints:
        print(f"\n📍 {description}")
        result = test_api(endpoint, token, method, params, body)
        if result:
            result["description"] = description
            all_results.append(result)
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    get_count = sum(1 for r in all_results if r["method"] == "GET" and r["status"] == 200)
    put_count = sum(1 for r in all_results if r["method"] == "PUT" and r["status"] == 200)
    post_count = sum(1 for r in all_results if r["method"] == "POST" and r["status"] == 200)
    patch_count = sum(1 for r in all_results if r["method"] == "PATCH" and r["status"] == 200)
    failed_count = sum(1 for r in all_results if r["status"] != 200)
    
    print(f"\nGET endpoints successful: {get_count}/{len(get_endpoints)}")
    print(f"PUT endpoints successful: {put_count}/{len(put_endpoints)}")
    print(f"POST endpoints successful: {post_count}/{len(post_endpoints) + len(print_endpoints)}")
    print(f"  - Parts/Inventory: {sum(1 for r in all_results if r['endpoint'] == 'YOUR_SHOP_API_PATH' and r['status'] == 200)}/{len(post_endpoints)}")
    print(f"  - Printing/Documents: {sum(1 for r in all_results if 'document/print' in r['endpoint'] and r['status'] == 200)}/{len(print_endpoints)}")
    print(f"PATCH endpoints successful: {patch_count}/{sum(1 for m, e, p, b, d in endpoints if m == 'PATCH')}")
    print(f"Failed: {failed_count}")
    
    print("\nDetailed results:")
    for result in all_results:
        status_icon = "✅" if result["status"] == 200 else "❌"
        endpoint_str = f"{result['method']} {result['endpoint']}"
        print(f"{status_icon} {endpoint_str:50} → {result['status']}")
    
    # Save to JSON file
    output_file = "api_documentation.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_date": "2025-11-07",
            "base_url": BASE_URL,
            "username": username,
            "total_endpoints": len(endpoints),
            "successful": get_count + put_count + post_count + patch_count,
            "failed": failed_count,
            "get_endpoints": len(get_endpoints),
            "put_endpoints": len(put_endpoints),
            "post_endpoints": len(post_endpoints),
            "print_endpoints": len(print_endpoints),
            "patch_endpoints": sum(1 for m, e, p, b, d in endpoints if m == 'PATCH'),
            "notes": {
                "excluded": "Client/customer-facing endpoints excluded for privacy",
                "safe_operations": "Only worker-facing GET/PUT/POST/PATCH tested",
                "no_brand_creation": "Brand/model creation endpoints excluded",
                "printing": "PDF document generation endpoints included (tickets, invoices, tags)"
            },
            "results": all_results
        }, f, indent=2)
    
    print(f"\n✅ Full documentation saved to: {output_file}")
    print(f"   Total: {len(all_results)} endpoints tested")
    print(f"   File size: {len(json.dumps(all_results, indent=2))} bytes")
    print("\nThis file contains complete request/response examples for the LLM!\n")
