#!/usr/bin/env python3
"""
Comprehensive API test script for Mountain Weather Forecast API
Tests all endpoints with various scenarios
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:5001"

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(name: str):
    """Print test header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Testing: {name}{Colors.RESET}")
    print("-" * 60)

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")

def check_server_running() -> bool:
    """Check if the API server is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def test_health_endpoint():
    """Test the health check endpoint"""
    print_test("Health Check Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data.get('status')}")
            print_info(f"Service: {data.get('service')}")
            print_info(f"Version: {data.get('version')}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Health check failed: {str(e)}")
        return False

def test_dashboard_endpoint():
    """Test the dashboard HTML endpoint"""
    print_test("Dashboard Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            if "Mountain Weather Forecast" in content and "<html" in content.lower():
                print_success("Dashboard endpoint returns HTML")
                print_info(f"Content length: {len(content)} characters")
                return True
            else:
                print_error("Dashboard endpoint doesn't return expected HTML")
                return False
        else:
            print_error(f"Dashboard endpoint failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Dashboard endpoint failed: {str(e)}")
        return False

def test_forecast_endpoint_valid():
    """Test the forecast endpoint with valid data"""
    print_test("Forecast Endpoint - Valid Request")
    
    test_data = {
        "latitude": 50.06,
        "longitude": -123.15,
        "location_name": "Squamish, BC",
        "forecast_days": 3
    }
    
    try:
        print_info(f"Sending request with data: {json.dumps(test_data, indent=2)}")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/forecast",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120  # Forecast generation can take time
        )
        
        elapsed_time = time.time() - start_time
        print_info(f"Request completed in {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate mountain-focused response structure
            required_keys = ["location", "current_conditions", "next_6_hours", "next_3_days"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                print_error(f"Response missing required keys: {missing_keys}")
                print_info(f"Available keys: {list(data.keys())}")
                return False
            
            print_success("Forecast endpoint returned valid response")
            print_info(f"Location: {data.get('location', {}).get('name', 'N/A')}")
            print_info(f"Current temp: {data.get('current_conditions', {}).get('temperature', {}).get('value', 'N/A')}°C")
            print_info(f"6-hour entries: {len(data.get('next_6_hours', []))}")
            print_info(f"3-day entries: {len(data.get('next_3_days', []))}")
            
            return True
        else:
            print_error(f"Forecast endpoint failed with status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error message: {error_data.get('error', 'Unknown error')}")
            except:
                print_error(f"Response: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print_error("Forecast endpoint timed out (took longer than 120 seconds)")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Forecast endpoint failed: {str(e)}")
        return False

def test_forecast_endpoint_missing_fields():
    """Test the forecast endpoint with missing required fields"""
    print_test("Forecast Endpoint - Missing Required Fields")
    
    test_data = {
        "location_name": "Test Location"
        # Missing latitude and longitude
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/forecast",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 400:
            data = response.json()
            if "error" in data:
                print_success(f"Correctly rejected invalid request: {data['error']}")
                return True
            else:
                print_error("Returned 400 but no error message")
                return False
        else:
            print_error(f"Expected 400, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def test_forecast_endpoint_invalid_coordinates():
    """Test the forecast endpoint with invalid coordinates"""
    print_test("Forecast Endpoint - Invalid Coordinates")
    
    test_cases = [
        {"latitude": 91, "longitude": -123.15, "name": "Latitude too high"},
        {"latitude": -91, "longitude": -123.15, "name": "Latitude too low"},
        {"latitude": 50.06, "longitude": 181, "name": "Longitude too high"},
        {"latitude": 50.06, "longitude": -181, "name": "Longitude too low"},
    ]
    
    all_passed = True
    for test_case in test_cases:
        test_data = {
            "latitude": test_case["latitude"],
            "longitude": test_case["longitude"],
            "location_name": "Test",
            "forecast_days": 3
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/forecast",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 400:
                print_success(f"Correctly rejected: {test_case['name']}")
            else:
                print_error(f"Failed to reject: {test_case['name']} (got {response.status_code})")
                all_passed = False
        except requests.exceptions.RequestException as e:
            print_error(f"Request failed for {test_case['name']}: {str(e)}")
            all_passed = False
    
    return all_passed

def test_forecast_endpoint_invalid_days():
    """Test the forecast endpoint with invalid forecast_days"""
    print_test("Forecast Endpoint - Invalid Forecast Days")
    
    test_cases = [
        {"days": 0, "name": "Zero days"},
        {"days": 17, "name": "Too many days"},
        {"days": -1, "name": "Negative days"},
    ]
    
    all_passed = True
    for test_case in test_cases:
        test_data = {
            "latitude": 50.06,
            "longitude": -123.15,
            "location_name": "Test",
            "forecast_days": test_case["days"]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/forecast",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 400:
                print_success(f"Correctly rejected: {test_case['name']}")
            else:
                print_error(f"Failed to reject: {test_case['name']} (got {response.status_code})")
                all_passed = False
        except requests.exceptions.RequestException as e:
            print_error(f"Request failed for {test_case['name']}: {str(e)}")
            all_passed = False
    
    return all_passed

def test_test_forecast_endpoint():
    """Test the test-forecast endpoint"""
    print_test("Test Forecast Endpoint")
    
    test_data = {
        "latitude": 47.4,
        "longitude": -121.5,
        "location_name": "Test Location",
        "forecast_days": 3
    }
    
    try:
        print_info(f"Sending test request...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/test-forecast",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success("Test forecast endpoint returned valid response")
            print_info(f"Success: {data.get('success', False)}")
            print_info(f"Location: {data.get('location', 'N/A')}")
            print_info(f"Generation time: {data.get('generation_time', 'N/A')}")
            print_info(f"Actual elapsed: {elapsed_time:.2f} seconds")
            return True
        else:
            print_error(f"Test forecast endpoint failed with status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print_error(f"Response: {response.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Test forecast endpoint failed: {str(e)}")
        return False

def test_forecast_with_elevation():
    """Test the forecast endpoint with elevation parameter"""
    print_test("Forecast Endpoint - With Elevation")
    
    test_data = {
        "latitude": 50.06,
        "longitude": -123.15,
        "location_name": "Whistler Peak",
        "forecast_days": 3,
        "elevation": 2181
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/forecast",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Forecast with elevation returned valid response")
            print_info(f"Elevation provided: {test_data['elevation']}m")
            return True
        else:
            print_error(f"Forecast with elevation failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Forecast with elevation failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("Mountain Weather Forecast API Test Suite")
    print("="*60 + Colors.RESET)
    
    # Check if server is running
    print(f"\n{Colors.YELLOW}Checking if server is running at {BASE_URL}...{Colors.RESET}")
    if not check_server_running():
        print_error(f"Server is not running at {BASE_URL}")
        print_info("Please start the server with: python forecast_api.py")
        print_info("Or run: python -m flask run --host=0.0.0.0 --port=5000")
        sys.exit(1)
    
    print_success("Server is running!")
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health_endpoint()))
    results.append(("Dashboard", test_dashboard_endpoint()))
    results.append(("Forecast - Valid", test_forecast_endpoint_valid()))
    results.append(("Forecast - Missing Fields", test_forecast_endpoint_missing_fields()))
    results.append(("Forecast - Invalid Coordinates", test_forecast_endpoint_invalid_coordinates()))
    results.append(("Forecast - Invalid Days", test_forecast_endpoint_invalid_days()))
    results.append(("Forecast - With Elevation", test_forecast_with_elevation()))
    results.append(("Test Forecast", test_test_forecast_endpoint()))
    
    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("Test Summary")
    print("="*60 + Colors.RESET)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}All tests passed! ✓{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}Some tests failed ✗{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()

