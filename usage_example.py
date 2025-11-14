"""
Example usage of the Open-Meteo data processor
"""

import openmeteo_requests
import requests_cache
from retry_requests import retry
from data_processor import DataProcessor

# Setup the Open-Meteo API client
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# API parameters
url = "https://ensemble-api.open-meteo.com/v1/ensemble"
params = {
    "latitude": 52.52,
    "longitude": 13.41,
    "daily": ["temperature_2m_min", "temperature_2m_max", "precipitation_sum", 
              "temperature_2m_mean", "wind_speed_10m_mean"],
    "hourly": ["temperature_2m", "precipitation", "wind_speed_80m"],
    "models": ["ecmwf_ifs025", "gem_global", "ecmwf_aifs025", "gfs_seamless"],
    "timezone": "auto",
    "forecast_days": 3
}

# Get responses
responses = openmeteo.weather_api(url, params=params)

# Process responses
processor = DataProcessor()
data = processor.process_responses(responses)

# Access the data
hourly_df = data['hourly']
daily_df = data['daily']

print("Hourly DataFrame shape:", hourly_df.shape)
print("\nHourly columns sample:", hourly_df.columns[:5].tolist())
print("\nDaily DataFrame shape:", daily_df.shape)
print("\nDaily columns sample:", daily_df.columns[:5].tolist())

# Get specific variable across all models
temp_cols = processor.get_variable_columns(hourly_df, 'temperature_2m')
print(f"\nFound {len(temp_cols)} temperature columns")

# Get specific model data
ecmwf_cols = processor.get_model_columns(hourly_df, 'ecmwf_ifs025')
print(f"\nFound {len(ecmwf_cols)} ECMWF IFS columns")
