#!/usr/bin/env python3
"""Test script for the live Mountain Weather API"""

import requests
import json

# Your live API endpoint
API_URL = "https://mountain-wx-fx.onrender.com/api/forecast"

# Test location (Squamish, BC)
test_data = {
    "latitude": 50.06,
    "longitude": -123.15,
    "location_name": "Squamish, BC",
    "forecast_days": 3
}

print("🏔️  Testing Mountain Weather Forecast API")
print(f"📍 Location: {test_data['location_name']}")
print(f"🌐 API URL: {API_URL}")
print("-" * 50)

try:
    # Make the API request
    print("📡 Sending request...")
    response = requests.post(API_URL, json=test_data)
    
    # Check if successful
    if response.status_code == 200:
        print("✅ Success! API is working")
        
        # Parse the response
        data = response.json()
        
        # Display summary
        print("\n📊 Forecast Summary:")
        print(f"   {data['summary']['executive_summary']}")
        print(f"   Rating: {data['summary']['operational_conditions']['rating']}")
        
        # Display first hour
        if data['hourly']:
            first_hour = data['hourly'][0]
            print(f"\n🕐 Next Hour Forecast:")
            print(f"   Temperature: {first_hour['temperature_2m']['mean']:.1f}°C")
            print(f"   Precipitation: {first_hour['precipitation']['mean']:.1f} mm")
            print(f"   Rain Probability: {first_hour['probabilities']['precipitation']['measurable']*100:.0f}%")
        
        print(f"\n📄 Full response saved to: test_response.json")
        with open('test_response.json', 'w') as f:
            json.dump(data, f, indent=2)
            
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Connection error: {e}")
    print("\nPossible reasons:")
    print("- Service might still be starting up (wait a minute)")
    print("- Check if the URL is correct")
