#!/usr/bin/env python3
"""Test with user's exact example"""

import openmeteo_requests
from openmeteo_sdk.Variable import Variable
from openmeteo_sdk.Aggregation import Aggregation
import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# User's exact parameters
url = "https://ensemble-api.open-meteo.com/v1/ensemble"
params = {
    "latitude": 52.52,  # Berlin
    "longitude": 13.41,
    "hourly": ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "precipitation", 
               "snowfall", "surface_pressure", "cloud_cover", "temperature_850hPa", 
               "freezing_level_height", "wind_direction_80m", "wind_speed_80m"],
    "models": ["ecmwf_ifs025"],
    "timezone": "auto",
    "forecast_days": 3,
}

print("Testing with Berlin coordinates (user's example)...")
responses = openmeteo.weather_api(url, params=params)

# Process response
for response in responses:
    print(f"\nCoordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Model: {response.Model()}")
    
    # Process hourly data
    hourly = response.Hourly()
    hourly_variables = list(map(lambda i: hourly.Variables(i), range(0, hourly.VariablesLength())))
    
    # Filter freezing level height
    hourly_freezing_level_height = filter(lambda x: x.Variable() == Variable.freezing_level_height, hourly_variables)
    
    # Get the data
    freezing_data = {}
    for variable in hourly_freezing_level_height:
        member = variable.EnsembleMember()
        data = variable.ValuesAsNumpy()
        freezing_data[f"member{member}"] = data
        
        # Check first few values
        print(f"\nMember {member} first 10 values:")
        for i in range(min(10, len(data))):
            if pd.notna(data[i]):
                print(f"  Hour {i}: {data[i]:.1f} m")
            else:
                print(f"  Hour {i}: NaN")
    
    # Check if we have any valid data
    if freezing_data:
        all_values = []
        for values in freezing_data.values():
            all_values.extend(values)
        valid_count = sum(1 for v in all_values if pd.notna(v))
        print(f"\nTotal valid freezing level values: {valid_count} out of {len(all_values)}")

print("\n\nNow testing with Snoqualmie Pass (mountain location)...")
params["latitude"] = 47.4
params["longitude"] = -121.5

responses = openmeteo.weather_api(url, params=params)

for response in responses:
    print(f"\nCoordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    
    hourly = response.Hourly()
    hourly_variables = list(map(lambda i: hourly.Variables(i), range(0, hourly.VariablesLength())))
    hourly_freezing_level_height = filter(lambda x: x.Variable() == Variable.freezing_level_height, hourly_variables)
    
    for variable in hourly_freezing_level_height:
        member = variable.EnsembleMember()
        data = variable.ValuesAsNumpy()
        print(f"\nMember {member} first 10 values:")
        for i in range(min(10, len(data))):
            if pd.notna(data[i]):
                print(f"  Hour {i}: {data[i]:.1f} m")
            else:
                print(f"  Hour {i}: NaN")
