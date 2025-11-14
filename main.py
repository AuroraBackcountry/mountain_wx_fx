"""
Main Integration Script
Complete workflow for generating weather forecasts from Open-Meteo ensemble data.
"""

import openmeteo_requests
import requests_cache
from retry_requests import retry

from data_processor import DataProcessor
from statistics_calculator import StatisticsCalculator
from probability_analyzer import ProbabilityAnalyzer
from model_comparison import ModelComparison
from forecast_generator import ForecastGenerator
from advanced_snow_formulas import AdvancedSnowFormulas


def main():
    """Main workflow for ensemble forecast processing."""
    
    # ========== 1. FETCH DATA FROM OPEN-METEO ==========
    print("Step 1: Fetching ensemble data from Open-Meteo...")
    
    # Setup API client with cache and retry
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    
    # Configure API request
    url = "https://ensemble-api.open-meteo.com/v1/ensemble"
    params = {
        "latitude": 50.06,   # Example: Squamish, BC
        "longitude": -123.15,
        "hourly": [
            "temperature_2m", 
            "relative_humidity_2m",
            "precipitation", 
            "snowfall",
            "wind_speed_80m",
            "wind_direction_80m"
        ],
        "daily": [
            "temperature_2m_min", 
            "temperature_2m_max",
            "temperature_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_mean"
        ],
        "models": ["ecmwf_ifs025", "gem_global", "ecmwf_aifs025", "gfs_seamless"],
        "timezone": "auto",
        "forecast_days": 3
    }
    
    # Get responses from API
    responses = openmeteo.weather_api(url, params=params)
    
    
    # ========== 2. PROCESS RESPONSES ==========
    print("Step 2: Processing API responses...")
    
    processor = DataProcessor()
    data = processor.process_responses(responses)
    
    print(f"  Hourly data shape: {data['hourly'].shape}")
    print(f"  Daily data shape: {data['daily'].shape}")
    
    
    # ========== 3. CALCULATE STATISTICS ==========
    print("\nStep 3: Calculating ensemble statistics...")
    
    stats_calc = StatisticsCalculator()
    
    # Calculate temperature statistics
    temp_stats = stats_calc.calculate_statistics(data['hourly'], 'temperature_2m')
    print(f"  Temperature range: {temp_stats['min'].min():.1f} to {temp_stats['max'].max():.1f}°C")
    
    # Calculate precipitation statistics
    precip_stats = stats_calc.calculate_statistics(data['hourly'], 'precipitation')
    print(f"  Max hourly precip: {precip_stats['max'].max():.1f} mm")
    
    
    # ========== 4. CALCULATE PROBABILITIES ==========
    print("\nStep 4: Calculating event probabilities...")
    
    prob_analyzer = ProbabilityAnalyzer()
    
    # Precipitation probabilities
    precip_probs = prob_analyzer.calculate_precipitation_probabilities(data['hourly'])
    print(f"  Max P(heavy rain): {precip_probs['p_heavy'].max():.2f}")
    
    # Temperature probabilities
    temp_probs = prob_analyzer.calculate_temperature_probabilities(data['hourly'])
    print(f"  Max P(freezing): {temp_probs['p_freezing'].max():.2f}")
    
    # Wind probabilities
    wind_probs = prob_analyzer.calculate_wind_probabilities(data['hourly'])
    print(f"  Max P(strong winds): {wind_probs['p_windy'].max():.2f}")
    
    
    # ========== 5. COMPARE MODELS ==========
    print("\nStep 5: Comparing forecast models...")
    
    model_comp = ModelComparison()
    
    # Compare temperature forecasts
    temp_comparison, temp_model_means = model_comp.compare_models(data['hourly'], 'temperature_2m')
    temp_outliers = model_comp.identify_outliers(temp_model_means)
    
    print(f"  Model spread (max range): {temp_comparison['range'].max():.1f}°C")
    print(f"  Agreement level: {model_comp.calculate_agreement_level(temp_comparison['cv'].mean())}")
    
    
    # ========== 6. CALCULATE SNOWFALL (ADVANCED) ==========
    print("\nStep 6: Calculating snowfall using advanced formulas...")
    
    # Get columns for ensemble members
    temp_cols = processor.get_variable_columns(data['hourly'], 'temperature_2m')
    rh_cols = processor.get_variable_columns(data['hourly'], 'relative_humidity_2m')
    precip_cols = processor.get_variable_columns(data['hourly'], 'precipitation')
    
    # Calculate snowfall for each member
    snow_formulas = AdvancedSnowFormulas()
    
    for i, (t_col, rh_col, p_col) in enumerate(zip(temp_cols, rh_cols, precip_cols)):
        data['hourly'][f'snowfall_calculated_member{i}'] = snow_formulas.calculate_snowfall(
            data['hourly'][t_col],
            data['hourly'][rh_col],
            data['hourly'][p_col],
            duration_h=1.0  # Hourly data
        )
    
    # Calculate snowfall statistics
    snow_stats = stats_calc.calculate_statistics(data['hourly'], 'snowfall_calculated')
    max_snow = snow_stats['max'].max()
    
    if max_snow > 0.1:
        print(f"  Max snowfall: {max_snow:.1f} cm/hr")
        print(f"  Total snow (sum of means): {snow_stats['mean'].sum():.1f} cm")
    else:
        print("  No significant snowfall expected")
    
    
    # ========== 7. GENERATE COMPLETE FORECAST ==========
    print("\nStep 7: Generating complete JSON forecast...")
    
    generator = ForecastGenerator()
    
    location = {
        "lat": params["latitude"],
        "lon": params["longitude"],
        "name": "Squamish, BC"
    }
    
    variables = ['temperature_2m', 'precipitation', 'wind_speed_80m']
    
    forecast = generator.generate_forecast(data, location, variables)
    
    print(f"  Generated forecast with {len(forecast['hourly'])} hourly entries")
    print(f"  Generated forecast with {len(forecast['daily'])} daily entries")
    print(f"  Model comparisons: {len(forecast['model_comparison'])}")
    
    
    # ========== 8. EXPORT RESULTS ==========
    print("\nStep 8: Exporting results...")
    
    # Save to JSON file
    json_output = generator.to_json(forecast, pretty=True)
    
    with open('forecast_output.json', 'w') as f:
        f.write(json_output)
    
    print("  ✓ Saved to forecast_output.json")
    
    # Print summary
    print("\n" + "="*60)
    print("FORECAST SUMMARY")
    print("="*60)
    print(forecast['summary']['executive_summary'])
    print(f"\nOperational Rating: {forecast['summary']['operational_conditions']['rating']}")
    print(f"Rationale: {forecast['summary']['operational_conditions']['rationale']}")
    
    if forecast['summary']['key_concerns']:
        print(f"\nKey Concerns: {', '.join(forecast['summary']['key_concerns'])}")
    
    print("\n✓ Complete forecast generated successfully!")
    print("="*60)
    
    return forecast


if __name__ == "__main__":
    forecast = main()
