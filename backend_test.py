#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Dazeen E-commerce
Tests all endpoints: seed, products, auth, cart, wishlist, orders
"""

import requests
import json
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://dazeen-mobile.preview.emergentagent.com/api"

# Test data storage
test_data = {
    "auth_token": None,
    "user_id": None,
    "product_ids": [],
    "order_id": None
}

# Test credentials
TEST_USER = {
    "name": "Dazeen Test User",
    "email": "testuser@dazeen.com",
    "password": "DazeenTest123!",
    "phone": "9876543210"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}TEST: {test_name}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def make_request(method: str, endpoint: str, data: Optional[Dict] = None, 
                 params: Optional[Dict] = None, auth_token: Optional[str] = None) -> tuple:
    """Make HTTP request and return (success, response, error_message)"""
    url = f"{BACKEND_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, params=params, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params, timeout=10)
        else:
            return False, None, f"Unsupported method: {method}"
        
        print_info(f"{method} {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            try:
                return True, response.json(), None
            except:
                return True, response.text, None
        else:
            try:
                error_detail = response.json()
                return False, None, f"Status {response.status_code}: {error_detail}"
            except:
                return False, None, f"Status {response.status_code}: {response.text}"
    
    except requests.exceptions.Timeout:
        return False, None, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error - backend may be down"
    except Exception as e:
        return False, None, f"Exception: {str(e)}"

# ==================== TEST FUNCTIONS ====================

def test_seed_endpoint():
    """Test 1: Seed Database"""
    print_test_header("1. Seed Database")
    
    success, response, error = make_request("POST", "/seed")
    
    if success:
        print_success("Seed endpoint successful")
        print_info(f"Response: {response}")
        return True
    else:
        print_error(f"Seed endpoint failed: {error}")
        return False

def test_get_all_products():
    """Test 2: Get All Products"""
    print_test_header("2. Get All Products")
    
    success, response, error = make_request("GET", "/products")
    
    if success:
        if isinstance(response, list) and len(response) > 0:
            print_success(f"Retrieved {len(response)} products")
            # Store product IDs for later tests
            test_data["product_ids"] = [p["id"] for p in response[:3]]
            print_info(f"Sample product IDs: {test_data['product_ids']}")
            
            # Display first product
            print_info(f"First product: {response[0]['name']} - ₹{response[0]['price']}")
            return True
        else:
            print_error("No products returned")
            return False
    else:
        print_error(f"Get products failed: {error}")
        return False

def test_get_bestsellers():
    """Test 3: Get Bestseller Products"""
    print_test_header("3. Get Bestseller Products")
    
    success, response, error = make_request("GET", "/products", params={"is_bestseller": "true"})
    
    if success:
        if isinstance(response, list):
            bestsellers = [p for p in response if p.get("is_bestseller")]
            print_success(f"Retrieved {len(bestsellers)} bestseller products")
            if len(bestsellers) > 0:
                print_info(f"Bestseller: {bestsellers[0]['name']}")
            return True
        else:
            print_error("Invalid response format")
            return False
    else:
        print_error(f"Get bestsellers failed: {error}")
        return False

def test_get_single_product():
    """Test 4: Get Single Product by ID"""
    print_test_header("4. Get Single Product by ID")
    
    if not test_data["product_ids"]:
        print_error("No product IDs available - skipping test")
        return False
    
    product_id = test_data["product_ids"][0]
    success, response, error = make_request("GET", f"/products/{product_id}")
    
    if success:
        if isinstance(response, dict) and response.get("id") == product_id:
            print_success(f"Retrieved product: {response['name']}")
            print_info(f"Price: ₹{response['price']}, Stock: {response['stock']}")
            return True
        else:
            print_error("Product data mismatch")
            return False
    else:
        print_error(f"Get single product failed: {error}")
        return False

def test_register():
    """Test 5: User Registration"""
    print_test_header("5. User Registration")
    
    success, response, error = make_request("POST", "/auth/register", data=TEST_USER)
    
    if success:
        if response.get("access_token") and response.get("user"):
            test_data["auth_token"] = response["access_token"]
            test_data["user_id"] = response["user"]["id"]
            print_success("User registered successfully")
            print_info(f"User ID: {test_data['user_id']}")
            print_info(f"Token: {test_data['auth_token'][:20]}...")
            return True
        else:
            print_error("Invalid registration response")
            return False
    else:
        # If user already exists, try login instead
        if "already registered" in str(error).lower():
            print_info("User already exists, will test login instead")
            return test_login()
        print_error(f"Registration failed: {error}")
        return False

def test_login():
    """Test 6: User Login"""
    print_test_header("6. User Login")
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    success, response, error = make_request("POST", "/auth/login", data=login_data)
    
    if success:
        if response.get("access_token") and response.get("user"):
            test_data["auth_token"] = response["access_token"]
            test_data["user_id"] = response["user"]["id"]
            print_success("User logged in successfully")
            print_info(f"User ID: {test_data['user_id']}")
            print_info(f"Token: {test_data['auth_token'][:20]}...")
            return True
        else:
            print_error("Invalid login response")
            return False
    else:
        print_error(f"Login failed: {error}")
        return False

def test_get_profile():
    """Test 7: Get User Profile"""
    print_test_header("7. Get User Profile")
    
    if not test_data["auth_token"]:
        print_error("No auth token available - skipping test")
        return False
    
    success, response, error = make_request("GET", "/auth/profile", auth_token=test_data["auth_token"])
    
    if success:
        if response.get("email") == TEST_USER["email"]:
            print_success(f"Profile retrieved: {response['name']}")
            print_info(f"Email: {response['email']}")
            return True
        else:
            print_error("Profile data mismatch")
            return False
    else:
        print_error(f"Get profile failed: {error}")
        return False

def test_add_to_cart():
    """Test 8: Add Item to Cart"""
    print_test_header("8. Add Item to Cart")
    
    if not test_data["auth_token"] or not test_data["product_ids"]:
        print_error("Missing auth token or product IDs - skipping test")
        return False
    
    product_id = test_data["product_ids"][1] if len(test_data["product_ids"]) > 1 else test_data["product_ids"][0]
    params = {"product_id": product_id, "quantity": 2}
    
    success, response, error = make_request("POST", "/cart/add", params=params, auth_token=test_data["auth_token"])
    
    if success:
        print_success(f"Added product {product_id} to cart (quantity: 2)")
        return True
    else:
        print_error(f"Add to cart failed: {error}")
        return False

def test_get_cart():
    """Test 9: Get Cart Contents"""
    print_test_header("9. Get Cart Contents")
    
    if not test_data["auth_token"]:
        print_error("No auth token available - skipping test")
        return False
    
    success, response, error = make_request("GET", "/cart", auth_token=test_data["auth_token"])
    
    if success:
        if "items" in response and "total" in response:
            print_success(f"Cart retrieved: {len(response['items'])} items, Total: ₹{response['total']}")
            if len(response['items']) > 0:
                print_info(f"First item: {response['items'][0]['name']} x {response['items'][0]['quantity']}")
            return True
        else:
            print_error("Invalid cart response format")
            return False
    else:
        print_error(f"Get cart failed: {error}")
        return False

def test_update_cart():
    """Test 10: Update Cart Item Quantity"""
    print_test_header("10. Update Cart Item Quantity")
    
    if not test_data["auth_token"] or not test_data["product_ids"]:
        print_error("Missing auth token or product IDs - skipping test")
        return False
    
    product_id = test_data["product_ids"][1] if len(test_data["product_ids"]) > 1 else test_data["product_ids"][0]
    params = {"product_id": product_id, "quantity": 3}
    
    success, response, error = make_request("PUT", "/cart/update", params=params, auth_token=test_data["auth_token"])
    
    if success:
        print_success(f"Updated cart item quantity to 3")
        return True
    else:
        print_error(f"Update cart failed: {error}")
        return False

def test_verify_cart_update():
    """Test 11: Verify Cart Update"""
    print_test_header("11. Verify Cart Update")
    
    if not test_data["auth_token"]:
        print_error("No auth token available - skipping test")
        return False
    
    success, response, error = make_request("GET", "/cart", auth_token=test_data["auth_token"])
    
    if success:
        if "items" in response and len(response["items"]) > 0:
            # Check if quantity was updated to 3
            item = response["items"][0]
            if item["quantity"] == 3:
                print_success(f"Cart update verified: quantity is 3")
                return True
            else:
                print_error(f"Cart quantity mismatch: expected 3, got {item['quantity']}")
                return False
        else:
            print_error("Cart is empty")
            return False
    else:
        print_error(f"Verify cart update failed: {error}")
        return False

def test_add_to_wishlist():
    """Test 12: Add Item to Wishlist"""
    print_test_header("12. Add Item to Wishlist")
    
    if not test_data["auth_token"] or not test_data["product_ids"]:
        print_error("Missing auth token or product IDs - skipping test")
        return False
    
    product_id = test_data["product_ids"][2] if len(test_data["product_ids"]) > 2 else test_data["product_ids"][0]
    
    success, response, error = make_request("POST", f"/wishlist/add/{product_id}", auth_token=test_data["auth_token"])
    
    if success:
        print_success(f"Added product {product_id} to wishlist")
        return True
    else:
        print_error(f"Add to wishlist failed: {error}")
        return False

def test_get_wishlist():
    """Test 13: Get Wishlist"""
    print_test_header("13. Get Wishlist")
    
    if not test_data["auth_token"]:
        print_error("No auth token available - skipping test")
        return False
    
    success, response, error = make_request("GET", "/wishlist", auth_token=test_data["auth_token"])
    
    if success:
        if isinstance(response, list):
            print_success(f"Wishlist retrieved: {len(response)} items")
            if len(response) > 0:
                print_info(f"First item: {response[0]['name']}")
            return True
        else:
            print_error("Invalid wishlist response format")
            return False
    else:
        print_error(f"Get wishlist failed: {error}")
        return False

def test_remove_from_wishlist():
    """Test 14: Remove Item from Wishlist"""
    print_test_header("14. Remove Item from Wishlist")
    
    if not test_data["auth_token"] or not test_data["product_ids"]:
        print_error("Missing auth token or product IDs - skipping test")
        return False
    
    product_id = test_data["product_ids"][2] if len(test_data["product_ids"]) > 2 else test_data["product_ids"][0]
    
    success, response, error = make_request("DELETE", f"/wishlist/remove/{product_id}", auth_token=test_data["auth_token"])
    
    if success:
        print_success(f"Removed product {product_id} from wishlist")
        return True
    else:
        print_error(f"Remove from wishlist failed: {error}")
        return False

def test_verify_wishlist_removal():
    """Test 15: Verify Wishlist Removal"""
    print_test_header("15. Verify Wishlist Removal")
    
    if not test_data["auth_token"]:
        print_error("No auth token available - skipping test")
        return False
    
    success, response, error = make_request("GET", "/wishlist", auth_token=test_data["auth_token"])
    
    if success:
        if isinstance(response, list):
            removed_product_id = test_data["product_ids"][2] if len(test_data["product_ids"]) > 2 else test_data["product_ids"][0]
            product_in_wishlist = any(p["id"] == removed_product_id for p in response)
            
            if not product_in_wishlist:
                print_success(f"Wishlist removal verified: product removed")
                return True
            else:
                print_error(f"Product still in wishlist")
                return False
        else:
            print_error("Invalid wishlist response format")
            return False
    else:
        print_error(f"Verify wishlist removal failed: {error}")
        return False

def test_create_order():
    """Test 16: Create Order"""
    print_test_header("16. Create Order")
    
    if not test_data["auth_token"] or not test_data["product_ids"]:
        print_error("Missing auth token or product IDs - skipping test")
        return False
    
    # First, get cart to see what items we have
    success, cart_response, error = make_request("GET", "/cart", auth_token=test_data["auth_token"])
    
    if not success or not cart_response.get("items"):
        print_error("Cart is empty, cannot create order")
        return False
    
    # Create order with cart items
    order_items = []
    for item in cart_response["items"]:
        order_items.append({
            "product_id": item["product_id"],
            "product_name": item["name"],
            "price": item["price"],
            "quantity": item["quantity"],
            "image_base64": item.get("image_base64")
        })
    
    order_data = {
        "user_id": test_data["user_id"],
        "items": order_items,
        "total_amount": cart_response["total"],
        "shipping_address": {
            "full_name": "Dazeen Test User",
            "phone": "9876543210",
            "address_line1": "123 Test Street",
            "address_line2": "Apartment 4B",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "is_default": True
        }
    }
    
    success, response, error = make_request("POST", "/orders", data=order_data, auth_token=test_data["auth_token"])
    
    if success:
        if response.get("id"):
            test_data["order_id"] = response["id"]
            print_success(f"Order created successfully: {test_data['order_id']}")
            return True
        else:
            print_error("Order ID not returned")
            return False
    else:
        print_error(f"Create order failed: {error}")
        return False

def test_get_orders():
    """Test 17: Get User Orders"""
    print_test_header("17. Get User Orders")
    
    if not test_data["auth_token"]:
        print_error("No auth token available - skipping test")
        return False
    
    success, response, error = make_request("GET", "/orders", auth_token=test_data["auth_token"])
    
    if success:
        if isinstance(response, list):
            print_success(f"Retrieved {len(response)} orders")
            if len(response) > 0:
                order = response[0]
                print_info(f"Latest order: {order['id']}, Total: ₹{order['total_amount']}, Status: {order['order_status']}")
            return True
        else:
            print_error("Invalid orders response format")
            return False
    else:
        print_error(f"Get orders failed: {error}")
        return False

# ==================== MAIN TEST RUNNER ====================

def run_all_tests():
    """Run all backend tests in sequence"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}DAZEEN E-COMMERCE BACKEND API TEST SUITE{Colors.END}")
    print(f"{Colors.BOLD}Backend URL: {BACKEND_URL}{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    tests = [
        ("Seed Database", test_seed_endpoint),
        ("Get All Products", test_get_all_products),
        ("Get Bestsellers", test_get_bestsellers),
        ("Get Single Product", test_get_single_product),
        ("User Registration", test_register),
        ("User Login", test_login),
        ("Get Profile", test_get_profile),
        ("Add to Cart", test_add_to_cart),
        ("Get Cart", test_get_cart),
        ("Update Cart", test_update_cart),
        ("Verify Cart Update", test_verify_cart_update),
        ("Add to Wishlist", test_add_to_wishlist),
        ("Get Wishlist", test_get_wishlist),
        ("Remove from Wishlist", test_remove_from_wishlist),
        ("Verify Wishlist Removal", test_verify_wishlist_removal),
        ("Create Order", test_create_order),
        ("Get Orders", test_get_orders),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{Colors.BOLD}Total: {len(results)} | Passed: {Colors.GREEN}{passed}{Colors.END}{Colors.BOLD} | Failed: {Colors.RED}{failed}{Colors.END}{Colors.BOLD}{Colors.END}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  {failed} TEST(S) FAILED{Colors.END}")
    
    return passed, failed

if __name__ == "__main__":
    passed, failed = run_all_tests()
    exit(0 if failed == 0 else 1)
