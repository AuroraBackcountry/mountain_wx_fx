#!/usr/bin/env python3
"""
Command-line interface for Mountain Weather Forecast System
Designed for easy integration with n8n and other automation tools

Usage:
    python forecast_cli.py --lat 50.06 --lon -123.15 --days 3
    python forecast_cli.py --lat 50.06 --lon -123.15 --name "Squamish, BC" --output stdout
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add parent directory to path to import main
sys.path.append(str(Path(__file__).parent))

import openmeteo_requests
import requests_cache
from retry_requests import retry
from data_processor import DataProcessor
from statistics_calculator import StatisticsCalculator
from probability_analyzer import ProbabilityAnalyzer
from model_comparison import ModelComparison
from enhanced_forecast_generator import EnhancedForecastGenerator
from advanced_snow_formulas import AdvancedSnowFormulas


def run_forecast(lat, lon, days=3, location_name=None, 
                hourly_vars=None, daily_vars=None, models=None):
    """
    Run weather forecast with custom parameters
    
    Args:
        lat: Latitude
        lon: Longitude  
        days: Number of forecast days (1-16)
        location_name: Optional location name
        hourly_vars: List of hourly variables (or None for defaults)
        daily_vars: List of daily variables (or None for defaults)
        models: List of models (or None for defaults)
        
    Returns:
        Dictionary with forecast data
    """
    
    # Ensure proper types
    lat = float(lat)
    lon = float(lon)
    days = int(days)
    
    # Default variables if not specified
    if hourly_vars is None:
        hourly_vars = [
            "temperature_2m", 
            "relative_humidity_2m",
            "dew_point_2m",
            "precipitation", 
            "snowfall",
            "cloud_cover",
            "surface_pressure",
            "wind_speed_80m",
            "wind_direction_80m",
            "wind_speed_10m",
            "wind_direction_10m",
            "temperature_850hPa",
            "freezing_level_height"
        ]
    
    if daily_vars is None:
        daily_vars = [
            "temperature_2m_min", 
            "temperature_2m_max",
            "temperature_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_mean",
            "wind_direction_10m_dominant"
        ]
    
    if models is None:
        models = ["ecmwf_ifs025", "gfs_seamless", "gem_global", "icon_global"]
    
    # Setup API client
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    
    # Configure API request
    url = "https://ensemble-api.open-meteo.com/v1/ensemble"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": hourly_vars,
        "daily": daily_vars,
        "models": models,
        "timezone": "auto",
        "forecast_days": days
    }
    
    # Get responses from API
    responses = openmeteo.weather_api(url, params=params)
    
    # Process responses
    processor = DataProcessor()
    data = processor.process_responses(responses)
    
    # Generate forecast
    generator = EnhancedForecastGenerator()
    location = {
        "lat": lat,
        "lon": lon,
        "name": location_name or f"{lat}, {lon}"
    }
    
    # Determine which variables we can process
    available_vars = []
    if 'temperature_2m' in hourly_vars:
        available_vars.append('temperature_2m')
    if 'precipitation' in hourly_vars:
        available_vars.append('precipitation')
    if 'wind_speed_80m' in hourly_vars:
        available_vars.append('wind_speed_80m')
    
    forecast = generator.generate_forecast(data, location, available_vars)
    
    return forecast


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='Generate mountain weather forecast',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic forecast for a location
  python forecast_cli.py --lat 50.06 --lon -123.15
  
  # With location name and custom days
  python forecast_cli.py --lat 50.06 --lon -123.15 --name "Squamish, BC" --days 5
  
  # Output to stdout for piping
  python forecast_cli.py --lat 50.06 --lon -123.15 --output stdout
  
  # Save to custom file
  python forecast_cli.py --lat 50.06 --lon -123.15 --output custom.json
        """
    )
    
    parser.add_argument('--lat', type=float, required=True, 
                       help='Latitude (e.g., 50.06)')
    parser.add_argument('--lon', type=float, required=True, 
                       help='Longitude (e.g., -123.15)')
    parser.add_argument('--days', type=int, default=3, 
                       help='Forecast days 1-16 (default: 3)')
    parser.add_argument('--name', type=str, 
                       help='Location name (e.g., "Squamish, BC")')
    parser.add_argument('--output', type=str, default='forecast_output.json',
                       help='Output destination: stdout, or filename (default: forecast_output.json)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress messages')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not -90 <= args.lat <= 90:
        parser.error("Latitude must be between -90 and 90")
    if not -180 <= args.lon <= 180:
        parser.error("Longitude must be between -180 and 180")
    if not 1 <= args.days <= 16:
        parser.error("Days must be between 1 and 16")
    
    try:
        if not args.quiet:
            print(f"Generating forecast for {args.name or f'{args.lat}, {args.lon}'}...", 
                  file=sys.stderr)
        
        # Run forecast
        forecast = run_forecast(
            lat=args.lat,
            lon=args.lon,
            days=args.days,
            location_name=args.name
        )
        
        # Convert to JSON
        json_output = json.dumps(forecast, indent=2, default=str)
        
        # Output based on argument
        if args.output == 'stdout':
            print(json_output)
        else:
            with open(args.output, 'w') as f:
                f.write(json_output)
            if not args.quiet:
                print(f"Forecast saved to {args.output}", file=sys.stderr)
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
