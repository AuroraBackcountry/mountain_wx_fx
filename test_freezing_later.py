#!/usr/bin/env python3
"""Check when freezing level data becomes available"""

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
params = {
    "latitude": 47.4,
    "longitude": -121.5,
    "hourly": ["freezing_level_height"],
    "models": ["ecmwf_ifs025"],
    "forecast_days": 7  # Extended forecast to check more hours
}

print("Checking 7-day forecast for freezing level data availability...")
responses = openmeteo.weather_api(url, params=params)

for response in responses:
    hourly = response.Hourly()
    hourly_variables = list(map(lambda i: hourly.Variables(i), range(0, hourly.VariablesLength())))
    
    # Create time index
    time_range = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )
    
    # Get freezing level data for first member
    freezing_vars = filter(lambda x: x.Variable() == Variable.freezing_level_height and x.EnsembleMember() == 0, hourly_variables)
    
    for variable in freezing_vars:
        data = variable.ValuesAsNumpy()
        
        # Find first valid index
        valid_mask = ~np.isnan(data)
        if valid_mask.any():
            first_valid_idx = np.argmax(valid_mask)
            print(f"\nFirst valid freezing level data at hour {first_valid_idx} ({time_range[first_valid_idx]})")
            print(f"Value: {data[first_valid_idx]:.1f} meters")
            
            # Show some valid values
            print("\nSample of valid freezing level heights:")
            valid_indices = np.where(valid_mask)[0][:10]
            for idx in valid_indices:
                print(f"  {time_range[idx]}: {data[idx]:.1f} m")
                
            # Calculate percentage of valid data
            valid_pct = (valid_mask.sum() / len(data)) * 100
            print(f"\nValid data: {valid_mask.sum()}/{len(data)} hours ({valid_pct:.1f}%)")
            
        else:
            print("\nNo valid freezing level data found in entire forecast!")
            
        # Check if it's a pattern (e.g., only certain times of day)
        print(f"\nChecking pattern of NaN values...")
        for i in range(min(48, len(data))):  # First 2 days
            if i % 12 == 0:
                print(f"\nDay {i//24+1}:")
            print(f"  Hour {i:2d}: {'Valid' if not np.isnan(data[i]) else 'NaN'}", end="")
            if (i + 1) % 6 == 0:
                print()  # New line every 6 hours
