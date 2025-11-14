import requests
import json
import time

# Test the API directly
url = "https://mountain-wx-fx.onrender.com/api/forecast"

# First, check if the API is responding
print("Checking API health...")
health_response = requests.get("https://mountain-wx-fx.onrender.com/api/health")
print(f"Health check: {health_response.status_code}")
print(f"Health response: {health_response.text}\n")

# Test with proper parameters
print("Testing API with simplified=true...")
body = {
    "latitude": 47.4,
    "longitude": -121.5,
    "location_name": "Snoqualmie Pass",
    "forecast_days": 5,
    "simplified": True
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=body, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Response size: {len(response.content)} bytes")
    
    # Check if it's HTML (error) or JSON
    if response.content.startswith(b'<'):
        print("❌ Response is HTML (error page):")
        print(response.text[:500])
    else:
        try:
            data = response.json()
            print("✅ Valid JSON response!")
            print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"First 200 chars: {response.text[:200]}")
            
except requests.exceptions.Timeout:
    print("❌ Request timed out (>30 seconds)")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
