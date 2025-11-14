import requests
import json
import time

# Wait a bit for deployment
print("Waiting 60 seconds for Render deployment to complete...")
time.sleep(60)

# Test the debug endpoint
url = "https://mountain-wx-fx.onrender.com/api/test-forecast"
body = {
    "latitude": 47.4,
    "longitude": -121.5,
    "location_name": "Snoqualmie Pass",
    "forecast_days": 3
}

print("\nTesting debug endpoint...")
try:
    response = requests.post(url, json=body, timeout=45)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success!")
        print(f"Generation time: {data.get('generation_time')}")
        print(f"Summary: {data.get('summary')[:100]}...")
    else:
        print(f"❌ Error: {response.text}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Error: {e}")

# Now test the main endpoint with simplified=true
print("\n\nTesting main endpoint with simplified=true...")
main_url = "https://mountain-wx-fx.onrender.com/api/forecast"
body["simplified"] = True

try:
    response = requests.post(main_url, json=body, timeout=45)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success!")
        print(f"Response size: {len(response.content)} bytes")
        print(f"Keys: {list(data.keys())}")
    else:
        print(f"❌ Error: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Error: {e}")
