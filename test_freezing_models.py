#!/usr/bin/env python3
"""Test freezing level with different models"""

import openmeteo_requests
from openmeteo_sdk.Variable import Variable
import pandas as pd
import numpy as np
import requests_cache
from retry_requests import retry

# Setup
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

url = "https://ensemble-api.open-meteo.com/v1/ensemble"

# Test multiple models
models_to_test = ["ecmwf_ifs025", "gfs_seamless", "gem_global", "ecmwf_aifs025"]

for model in models_to_test:
    print(f"\n{'='*50}")
    print(f"Testing model: {model}")
    print('='*50)
    
    params = {
        "latitude": 47.4,
        "longitude": -121.5,
        "hourly": ["temperature_2m", "freezing_level_height"],
        "models": [model],
        "forecast_days": 3
    }
    
    try:
        responses = openmeteo.weather_api(url, params=params)
        
        for response in responses:
            print(f"Model ID: {response.Model()}")
            
            hourly = response.Hourly()
            hourly_variables = list(map(lambda i: hourly.Variables(i), range(0, hourly.VariablesLength())))
            
            # Check temperature (should always work)
            temp_vars = filter(lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2 and x.EnsembleMember() == 0, hourly_variables)
            for var in temp_vars:
                data = var.ValuesAsNumpy()
                valid_count = np.sum(~np.isnan(data))
                print(f"Temperature 2m: {valid_count}/{len(data)} valid values")
                if valid_count > 0:
                    print(f"  First value: {data[np.argmax(~np.isnan(data))]:.1f}°C")
            
            # Check freezing level
            freezing_vars = filter(lambda x: x.Variable() == Variable.freezing_level_height and x.EnsembleMember() == 0, hourly_variables)
            found_freezing = False
            for var in freezing_vars:
                found_freezing = True
                data = var.ValuesAsNumpy()
                valid_count = np.sum(~np.isnan(data))
                print(f"Freezing level: {valid_count}/{len(data)} valid values")
                if valid_count > 0:
                    first_valid_idx = np.argmax(~np.isnan(data))
                    print(f"  First valid value at hour {first_valid_idx}: {data[first_valid_idx]:.1f} m")
                    # Show a few more valid values
                    valid_indices = np.where(~np.isnan(data))[0][:5]
                    for idx in valid_indices[1:]:
                        print(f"  Hour {idx}: {data[idx]:.1f} m")
            
            if not found_freezing:
                print("Freezing level: Variable not found in response")
                
    except Exception as e:
        print(f"Error with model {model}: {e}")

# Also test if we can calculate freezing level from temperature profile
print("\n" + "="*50)
print("Alternative: Calculate freezing level from temperature profile")
print("="*50)

params = {
    "latitude": 47.4,
    "longitude": -121.5,
    "hourly": ["temperature_850hPa", "geopotential_height_850hPa", 
               "temperature_700hPa", "geopotential_height_700hPa"],
    "models": ["ecmwf_ifs025"],
    "forecast_days": 1
}

print("\nChecking if we can get temperature at different pressure levels...")
try:
    responses = openmeteo.weather_api(url, params=params)
    for response in responses:
        hourly = response.Hourly()
        hourly_variables = list(map(lambda i: hourly.Variables(i), range(0, hourly.VariablesLength())))
        
        # List all available variables
        print("\nAvailable variables in response:")
        for var in hourly_variables[:10]:  # Show first 10
            print(f"  - Variable: {var.Variable()}, Altitude: {var.Altitude()}, "
                  f"Pressure: {var.PressureLevel()}, Member: {var.EnsembleMember()}")
                  
except Exception as e:
    print(f"Error: {e}")
