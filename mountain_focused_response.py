"""
Mountain-Focused Response Generator
Optimized for n8n integration with core mountain weather requirements

Core Principles:
1. Super accurate 6-hour and 3-day forecasts
2. Advanced snowfall calculations (already implemented)
3. Highly accurate temperatures and freezing levels
4. Wind data with direction
5. Elevation reference
6. Clear trend analysis
7. Easy-to-read JSON for n8n
"""

from typing import Dict, List, Any, Tuple
import numpy as np
from datetime import datetime, timedelta

def analyze_trends(hourly_data: List[Dict], hours: int = 6) -> Dict[str, str]:
    """
    Analyze weather trends over specified hours.
    Returns human-readable trend descriptions.
    """
    if not hourly_data or len(hourly_data) < hours:
        return {}
    
    trends = {}
    
    # Temperature trend
    temps = [h.get('temperature_2m', {}).get('mean', 0) for h in hourly_data[:hours]]
    temp_change = temps[-1] - temps[0] if temps else 0
    
    if temp_change > 3:
        trends['temperature'] = 'rising_rapidly'
    elif temp_change > 1:
        trends['temperature'] = 'rising'
    elif temp_change < -3:
        trends['temperature'] = 'falling_rapidly'
    elif temp_change < -1:
        trends['temperature'] = 'falling'
    else:
        trends['temperature'] = 'steady'
    
    # Cloud cover trend
    if all('cloud_cover' in h for h in hourly_data[:hours]):
        cloud_start = np.mean([h['cloud_cover']['mean'] for h in hourly_data[:2]])
        cloud_end = np.mean([h['cloud_cover']['mean'] for h in hourly_data[hours-2:hours]])
        
        if cloud_start > 70 and cloud_end < 30:
            trends['sky'] = 'clearing'
        elif cloud_start < 30 and cloud_end > 70:
            trends['sky'] = 'clouding_up'
        elif cloud_end < 20:
            trends['sky'] = 'clear'
        elif cloud_end > 80:
            trends['sky'] = 'overcast'
        else:
            trends['sky'] = 'partly_cloudy'
    
    # Wind trend
    winds = [h.get('wind_speed', {}).get('mean', 0) for h in hourly_data[:hours]]
    if len(winds) >= 2:
        wind_change = winds[-1] - winds[0]
        
        if wind_change > 20:
            trends['wind'] = 'increasing_rapidly'
        elif wind_change > 10:
            trends['wind'] = 'increasing'
        elif wind_change < -20:
            trends['wind'] = 'decreasing_rapidly'
        elif wind_change < -10:
            trends['wind'] = 'decreasing'
        else:
            trends['wind'] = 'steady'
    
    # Precipitation trend
    precip_probs = [h.get('probabilities', {}).get('precipitation', {}).get('any', 0) 
                    for h in hourly_data[:hours]]
    if precip_probs:
        avg_start = np.mean(precip_probs[:2])
        avg_end = np.mean(precip_probs[-2:])
        
        if avg_end > 0.7 and avg_start < 0.3:
            trends['precipitation'] = 'developing'
        elif avg_start > 0.7 and avg_end < 0.3:
            trends['precipitation'] = 'ending'
        elif avg_end > 0.5:
            trends['precipitation'] = 'likely'
        else:
            trends['precipitation'] = 'unlikely'
    
    return trends

def get_6hour_summary(hourly_data: List[Dict]) -> List[Dict[str, Any]]:
    """
    Create highly accurate 6-hour summary with all required fields.
    """
    summary = []
    
    for i in range(min(6, len(hourly_data))):
        hour = hourly_data[i]
        
        # Ensure all required data is present and accurate
        hour_summary = {
            'hour': i + 1,
            'time': hour.get('time'),
            'temperature': {
                'value': round(hour.get('temperature_2m', {}).get('mean', 0), 1),
                'min': round(hour.get('temperature_2m', {}).get('min', 0), 1),
                'max': round(hour.get('temperature_2m', {}).get('max', 0), 1),
                'feels_like': round(
                    calculate_feels_like(
                        hour.get('temperature_2m', {}).get('mean', 0),
                        hour.get('wind_speed', {}).get('mean', 0)
                    ), 1
                )
            },
            'wind': {
                'speed': round(hour.get('wind_speed', {}).get('mean', 0), 1),
                'gusts': round(hour.get('wind_speed', {}).get('max', 0), 1),
                'direction': hour.get('wind_direction', 'N/A'),
                'direction_degrees': get_direction_degrees(hour.get('wind_direction', 'N/A'))
            },
            'precipitation': {
                'amount': round(hour.get('precipitation', {}).get('mean', 0), 1),
                'probability': round(hour.get('probabilities', {}).get('precipitation', {}).get('any', 0) * 100),
                'type': determine_precip_type(hour)
            },
            'snowfall': {
                'amount': round(hour.get('snowfall', {}).get('mean', 0), 1),
                'probability': round(hour.get('probabilities', {}).get('snow', {}).get('any', 0) * 100, 0)
            },
            'freezing_level': hour.get('freezing_level_height', 'N/A'),
            'visibility': estimate_visibility(hour)
        }
        
        summary.append(hour_summary)
    
    return summary

def get_daily_summary(daily_data: List[Dict], hourly_data: List[Dict] = None) -> List[Dict[str, Any]]:
    """
    Create highly accurate 3-day summary with all required fields.
    """
    summary = []
    
    for day in daily_data[:3]:  # Limit to 3 days
        # Calculate accurate min/max from hourly if available
        if hourly_data:
            day_date = day['date']
            day_hourly = [h for h in hourly_data if h.get('time', '').startswith(day_date)]
            
            if day_hourly:
                # More accurate min/max from hourly data
                all_temps = []
                for h in day_hourly:
                    temp_data = h.get('temperature_2m', {})
                    all_temps.extend([temp_data.get('min', 0), temp_data.get('max', 0)])
                
                actual_min = min(all_temps) if all_temps else day['temperature']['min']
                actual_max = max(all_temps) if all_temps else day['temperature']['max']
            else:
                actual_min = day['temperature']['min']
                actual_max = day['temperature']['max']
        else:
            actual_min = day['temperature']['min']
            actual_max = day['temperature']['max']
        
        day_summary = {
            'date': day['date'],
            'day_name': day.get('day_of_week', day['date']),
            'temperature': {
                'min': round(actual_min, 1),
                'max': round(actual_max, 1),
                'range': round(actual_max - actual_min, 1)
            },
            'wind': {
                'max_speed': round(day['wind']['speed'], 1),
                'predominant_direction': day['wind']['direction']
            },
            'precipitation': {
                'total': round(day['precipitation_total'], 1),
                'type': day['precipitation']['type']
            },
            'snowfall': {
                'total': round(day['snowfall']['total'], 1),
                'max_rate': round(day['snowfall'].get('max_hourly', 0), 1)
            },
            'freezing_level': {
                'average': day.get('freezing_level', 'N/A'),
                'trend': 'rising' if day.get('freezing_level', 0) > daily_data[0].get('freezing_level', 0) else 'falling'
            },
            'conditions': day.get('summary', ''),
            'hazards': identify_hazards(day)
        }
        
        summary.append(day_summary)
    
    return summary

def calculate_feels_like(temp: float, wind_speed: float) -> float:
    """Calculate feels like temperature using wind chill formula."""
    if temp > 10 or wind_speed < 5:
        return temp
    
    # Wind chill formula
    wind_chill = 13.12 + 0.6215 * temp - 11.37 * (wind_speed ** 0.16) + 0.3965 * temp * (wind_speed ** 0.16)
    return min(temp, wind_chill)

def get_direction_degrees(direction: str) -> int:
    """Convert wind direction to degrees."""
    directions = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    }
    
    if isinstance(direction, (int, float)):
        return int(direction)
    
    return directions.get(direction, 0)

def determine_precip_type(hour_data: Dict) -> str:
    """Determine precipitation type based on temperature and snow probability."""
    temp = hour_data.get('temperature_2m', {}).get('mean', 0)
    snow_prob = hour_data.get('probabilities', {}).get('snow', {}).get('any', 0)
    
    if snow_prob > 0.7 or temp < 0:
        return 'snow'
    elif 0.3 < snow_prob < 0.7 and -2 < temp < 2:
        return 'mixed'
    else:
        return 'rain'

def estimate_visibility(hour_data: Dict) -> str:
    """Estimate visibility based on precipitation and wind."""
    precip = hour_data.get('precipitation', {}).get('mean', 0)
    snow = hour_data.get('snowfall', {}).get('mean', 0)
    wind = hour_data.get('wind_speed', {}).get('mean', 0)
    
    if snow > 2 and wind > 40:
        return 'poor'
    elif snow > 1 or (precip > 5 and wind > 30):
        return 'moderate'
    else:
        return 'good'

def identify_hazards(day_data: Dict) -> List[str]:
    """Identify potential mountain hazards."""
    hazards = []
    
    if day_data['snowfall']['total'] > 30:
        hazards.append('heavy_snow')
    elif day_data['snowfall']['total'] > 15:
        hazards.append('moderate_snow')
    
    if day_data['wind']['max_speed'] > 60:
        hazards.append('high_wind')
    
    if day_data['temperature']['min'] < -20:
        hazards.append('extreme_cold')
    
    if day_data.get('freezing_level', 0) == 'N/A':
        pass
    elif isinstance(day_data.get('freezing_level'), (int, float)) and day_data['freezing_level'] > 3000:
        hazards.append('high_freezing_level')
    
    return hazards

def create_mountain_focused_response(forecast: Dict, location_name: str, elevation: int = None) -> Dict:
    """
    Create the ultimate mountain-focused response for n8n.
    
    Core principles:
    1. 6-hour detailed forecast
    2. 3-day summary
    3. Advanced snowfall data
    4. Accurate temperatures and freezing levels
    5. Complete wind data
    6. Clear trends
    7. Easy n8n integration
    """
    
    # Extract hourly and daily data
    hourly_data = forecast.get('hourly', [])
    daily_data = forecast.get('daily', [])
    
    # Get current conditions (first hour)
    current = hourly_data[0] if hourly_data else {}
    
    # Analyze trends
    trends = analyze_trends(hourly_data, 6)
    
    # Build focused response
    response = {
        'location': {
            'name': location_name,
            'coordinates': {
                'latitude': forecast['metadata']['location']['lat'],
                'longitude': forecast['metadata']['location']['lon']
            },
            'elevation': elevation or 'not_specified'
        },
        'generated_at': forecast['metadata']['generated_at'],
        'current_conditions': {
            'time': current.get('time'),
            'temperature': {
                'value': round(current.get('temperature_2m', {}).get('mean', 0), 1),
                'feels_like': round(
                    calculate_feels_like(
                        current.get('temperature_2m', {}).get('mean', 0),
                        current.get('wind_speed', {}).get('mean', 0)
                    ), 1
                ),
                'unit': '°C'
            },
            'freezing_level': {
                'height': current.get('freezing_level_height', 'N/A'),
                'unit': 'meters'
            },
            'wind': {
                'speed': round(current.get('wind_speed', {}).get('mean', 0), 1),
                'gusts': round(current.get('wind_speed', {}).get('max', 0), 1),
                'direction': current.get('wind_direction', 'N/A'),
                'unit': 'km/h'
            },
            'snowfall': {
                'rate': round(current.get('snowfall', {}).get('mean', 0), 1),
                'unit': 'cm/hr'
            }
        },
        'trends': {
            'temperature': trends.get('temperature', 'steady'),
            'sky': trends.get('sky', 'unknown'),
            'wind': trends.get('wind', 'steady'),
            'precipitation': trends.get('precipitation', 'unknown'),
            'summary': generate_trend_summary(trends)
        },
        'next_6_hours': get_6hour_summary(hourly_data),
        'next_3_days': get_daily_summary(daily_data, hourly_data),
        'accuracy_metrics': {
            'models_used': len(forecast['metadata']['models']),
            'ensemble_members': forecast['metadata']['ensemble_members'],
            'confidence_score': forecast.get('data_quality', {}).get('confidence_score', 0.85)
        },
        'units': {
            'temperature': '°C',
            'wind_speed': 'km/h',
            'precipitation': 'mm',
            'snowfall': 'cm',
            'elevation': 'meters',
            'freezing_level': 'meters'
        }
    }
    
    # Add critical alerts if needed
    alerts = []
    if response['next_3_days']:
        for day in response['next_3_days']:
            if 'heavy_snow' in day.get('hazards', []):
                alerts.append({
                    'type': 'heavy_snow_warning',
                    'date': day['date'],
                    'amount': day['snowfall']['total']
                })
            if 'high_wind' in day.get('hazards', []):
                alerts.append({
                    'type': 'high_wind_warning',
                    'date': day['date'],
                    'speed': day['wind']['max_speed']
                })
    
    if alerts:
        response['alerts'] = alerts
    
    return response

def generate_trend_summary(trends: Dict[str, str]) -> str:
    """Generate human-readable trend summary."""
    parts = []
    
    # Temperature
    temp_trend = trends.get('temperature', 'steady')
    if temp_trend == 'rising_rapidly':
        parts.append('Temperature rising rapidly')
    elif temp_trend == 'falling_rapidly':
        parts.append('Temperature falling rapidly')
    elif temp_trend == 'rising':
        parts.append('Temperature rising')
    elif temp_trend == 'falling':
        parts.append('Temperature falling')
    
    # Sky
    sky_trend = trends.get('sky', '')
    if sky_trend == 'clearing':
        parts.append('clearing skies')
    elif sky_trend == 'clouding_up':
        parts.append('increasing clouds')
    
    # Wind
    wind_trend = trends.get('wind', 'steady')
    if wind_trend == 'increasing_rapidly':
        parts.append('wind increasing rapidly')
    elif wind_trend == 'increasing':
        parts.append('wind increasing')
    elif wind_trend == 'decreasing':
        parts.append('wind decreasing')
    
    # Precipitation
    precip_trend = trends.get('precipitation', '')
    if precip_trend == 'developing':
        parts.append('precipitation developing')
    elif precip_trend == 'ending':
        parts.append('precipitation ending')
    
    if parts:
        return ', '.join(parts).capitalize() + '.'
    else:
        return 'Conditions remaining steady.'
