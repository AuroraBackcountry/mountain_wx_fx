import requests
import json

# Test the full response (simplified=false)
url = "https://mountain-wx-fx.onrender.com/api/forecast"
body = {
    "latitude": 47.4,
    "longitude": -121.5,
    "location_name": "Snoqualmie Pass",
    "forecast_days": 3,
    "simplified": False  # Get the full response
}

print("Testing full response (simplified=false)...")
try:
    response = requests.post(url, json=body, timeout=45)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"Response size: {len(response.content)} bytes")
        print(f"Response size: {len(response.content)/1024:.1f} KB")
        print(f"\nTop-level keys: {list(data.keys())}")
        
        # Show structure
        if 'hourly' in data:
            print(f"\nHourly forecast points: {len(data['hourly'])}")
            if data['hourly']:
                print("First hourly entry keys:", list(data['hourly'][0].keys()))
                
        if 'daily' in data:
            print(f"\nDaily forecast points: {len(data['daily'])}")
            if data['daily']:
                print("First daily entry keys:", list(data['daily'][0].keys()))
                
        if 'model_comparison' in data:
            print(f"\nModel comparison keys: {list(data['model_comparison'].keys())}")
            
        # Save to file for inspection
        with open('full_response_example.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("\nFull response saved to full_response_example.json")
        
        # Show a sample of the hourly data structure
        if data.get('hourly'):
            print("\n--- Sample hourly forecast entry ---")
            print(json.dumps(data['hourly'][0], indent=2)[:800] + "...")
            
    else:
        print(f"❌ Error: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Error: {e}")
