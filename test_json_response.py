#!/usr/bin/env python3
"""Test JSON response from the API"""

import requests
import json

# Test with simplified response
print("Testing simplified response...")
response = requests.post(
    "https://mountain-wx-fx.onrender.com/api/forecast",
    json={
        "latitude": 50.06,
        "longitude": -123.15,
        "location_name": "Squamish, BC",
        "forecast_days": 1,
        "simplified": True
    }
)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(f"Response size: {len(response.content)} bytes")

try:
    data = response.json()
    print("✅ Valid JSON!")
    print(f"Keys: {list(data.keys())}")
    
    # Save to file for inspection
    with open('test_simplified.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("Saved to test_simplified.json")
    
except json.JSONDecodeError as e:
    print(f"❌ JSON Error: {e}")
    print(f"Response text (first 500 chars): {response.text[:500]}")
