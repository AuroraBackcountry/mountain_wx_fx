#!/usr/bin/env python3
"""Test the enhanced forecast generator"""

from forecast_cli import run_forecast
from improved_simplified_response import create_simplified_response
import json

print("Testing enhanced forecast generator with Whistler location...")

# Run forecast for Whistler
forecast = run_forecast(
    lat=49.650738,
    lon=-123.074821,
    days=3,
    location_name="Whistler"
)

print("\n1. Checking metadata:")
print(f"   Models: {forecast['metadata']['models']}")
print(f"   Members: {forecast['metadata']['ensemble_members']}")
print(f"   Calculations: {forecast['metadata'].get('calculations_included', 'Not found')}")

print("\n2. Checking current conditions:")
if forecast['hourly']:
    current = forecast['hourly'][0]
    print(f"   Time: {current['time']}")
    print(f"   Temp: {current.get('temperature_2m', {}).get('mean')}°C")
    print(f"   Snowfall: {current.get('snowfall', {}).get('mean', 'Not calculated')} cm")
    print(f"   Wind: {current.get('wind_speed', {}).get('mean')} km/h @ {current.get('wind_height')}")
    print(f"   Freezing Level: {current.get('freezing_level_height')} m")

print("\n3. Checking daily summaries:")
for day in forecast.get('daily', [])[:2]:
    print(f"\n   {day['date']}:")
    print(f"   - Summary: {day.get('summary')}")
    print(f"   - Snow Total: {day.get('snowfall', {}).get('total')} cm")
    print(f"   - Wind: {day.get('wind', {}).get('speed')} km/h @ {day.get('wind', {}).get('height')}")

print("\n4. Checking alerts:")
for alert in forecast.get('alerts', []):
    print(f"   - {alert['type']}: {alert['message']}")

print("\n5. Testing simplified response:")
simplified = create_simplified_response(forecast, "Whistler")
print(f"   Status: {simplified['conditions']}")
print(f"   Snow 24h: {simplified['mountain']['snow_24h']} cm")
print(f"   Current precip type: {simplified['current']['precipitation']['type']}")

# Save full response for inspection
with open('test_enhanced_output.json', 'w') as f:
    json.dump(simplified, f, indent=2)
print("\nSimplified response saved to test_enhanced_output.json")
