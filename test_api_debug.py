import requests
import json

url = "https://mountain-wx-fx.onrender.com/api/forecast"

# Test 1: With all parameters as the correct types
print("Test 1: Correct types")
body1 = {
    "latitude": 47.4,
    "longitude": -121.5,
    "location_name": "Snoqualmie Pass",
    "forecast_days": 5,
    "simplified": True
}
response1 = requests.post(url, json=body1)
print(f"Status: {response1.status_code}")
if response1.status_code == 200:
    print("✅ Success with correct types")
else:
    print(f"Response: {response1.text[:200]}")
print()

# Test 2: With string parameters like n8n might send
print("Test 2: String parameters (like n8n)")
body2 = {
    "latitude": "47.4",
    "longitude": "-121.5",
    "location_name": "Snoqualmie Pass",
    "forecast_days": "5",
    "simplified": "true"
}
response2 = requests.post(url, json=body2)
print(f"Status: {response2.status_code}")
if response2.status_code == 200:
    print("✅ Success with string parameters")
else:
    print(f"Response: {response2.text[:200]}")
print()

# Test 3: Mixed types
print("Test 3: Mixed types")
body3 = {
    "latitude": "47.4",
    "longitude": "-121.5", 
    "location_name": "Snoqualmie Pass",
    "forecast_days": "5",
    "simplified": True  # boolean
}
response3 = requests.post(url, json=body3)
print(f"Status: {response3.status_code}")
if response3.status_code == 200:
    print("✅ Success with mixed types")
else:
    print(f"Response: {response3.text[:200]}")

# Check Render deployment info
print("\nChecking API health...")
health_response = requests.get("https://mountain-wx-fx.onrender.com/api/health")
print(f"Health check status: {health_response.status_code}")
print(f"Health response: {health_response.text}")
