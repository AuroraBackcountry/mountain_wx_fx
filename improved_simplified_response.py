"""
Improved simplified response formatter for mountain weather
Removes redundant fields and focuses on what matters
"""

def create_simplified_response(forecast: dict, location_name: str) -> dict:
    """
    Create a clean, simplified response optimized for mountain weather.
    
    Key improvements:
    - Remove redundant fields (percentiles, std_dev for simplified view)
    - Clear precipitation type indication
    - Proper snowfall calculations
    - Wind data that makes sense
    - Mountain-specific alerts
    """
    
    # Helper to round values
    def round_val(val):
        if isinstance(val, (int, float)):
            return round(val, 1)
        return val
    
    # Process current conditions
    current_hour = forecast['hourly'][0] if forecast.get('hourly') else {}
    
    current = {
        'time': current_hour.get('time'),
        'temperature': {
            'value': round_val(current_hour.get('temperature_2m', {}).get('mean')),
            'range': [
                round_val(current_hour.get('temperature_2m', {}).get('min')),
                round_val(current_hour.get('temperature_2m', {}).get('max'))
            ]
        },
        'precipitation': {
            'amount': round_val(current_hour.get('precipitation', {}).get('mean', 0)),
            'probability': round_val(current_hour.get('probabilities', {}).get('precipitation', {}).get('any', 0)),
            'type': 'snow' if current_hour.get('snowfall', {}).get('mean', 0) > 0 else 'rain'
        },
        'snowfall': round_val(current_hour.get('snowfall', {}).get('mean', 0)),
        'wind': {
            'speed': round_val(current_hour.get('wind_speed', {}).get('mean', 0)),
            'gusts': round_val(current_hour.get('wind_speed', {}).get('max', 0)),
            'direction': current_hour.get('wind_direction', 'N/A'),
            'height': current_hour.get('wind_height', '10m_adjusted')
        },
        'freezing_level': round_val(current_hour.get('freezing_level_height', 0)),
        'snow_level': round_val(current_hour.get('snow_level', 0))
    }
    
    # Process next 6 hours - simplified
    next_6_hours = []
    for hour in forecast.get('hourly', [])[:6]:
        next_6_hours.append({
            'time': hour.get('time'),
            'temp': round_val(hour.get('temperature_2m', {}).get('mean')),
            'precip': round_val(hour.get('precipitation', {}).get('mean', 0)),
            'snow': round_val(hour.get('snowfall', {}).get('mean', 0)),
            'wind': round_val(hour.get('wind_speed', {}).get('mean', 0)),
            'snow_probability': round_val(hour.get('probabilities', {}).get('snow', {}).get('any', 0))
        })
    
    # Process daily summary - cleaner format
    daily_summary = []
    for day in forecast.get('daily', [])[:3]:
        daily_summary.append({
            'date': day.get('date'),
            'day': day.get('day_of_week'),
            'temps': {
                'min': round_val(day.get('temperature', {}).get('min')),
                'max': round_val(day.get('temperature', {}).get('max'))
            },
            'precipitation': {
                'total': round_val(day.get('precipitation_total', 0)),
                'snow': round_val(day.get('snowfall', {}).get('total', 0)),
                'type': 'snow' if day.get('snowfall', {}).get('total', 0) > 1 else 'rain' if day.get('precipitation_total', 0) > 0 else 'none'
            },
            'wind': {
                'max': round_val(day.get('wind', {}).get('speed', 0)),
                'direction': day.get('wind', {}).get('direction', 'Variable')
            },
            'freezing_level': round_val(day.get('freezing_level', 'N/A')),
            'summary': day.get('summary')
        })
    
    # Mountain-specific data
    mountain_data = {
        'snow_24h': sum([h.get('snowfall', {}).get('mean', 0) for h in forecast.get('hourly', [])[:24]]),
        'snow_48h': sum([h.get('snowfall', {}).get('mean', 0) for h in forecast.get('hourly', [])[:48]]),
        'max_wind_24h': max([h.get('wind_speed', {}).get('max', 0) for h in forecast.get('hourly', [])[:24]], default=0),
        'freezing_trend': 'rising' if len(forecast.get('hourly', [])) > 12 and 
                         forecast['hourly'][12].get('freezing_level_height', 0) > 
                         forecast['hourly'][0].get('freezing_level_height', 0) else 'falling'
    }
    
    # Build response
    response = {
        'location': location_name,
        'updated': forecast['metadata']['generated_at'],
        'conditions': forecast['summary']['operational_conditions']['rating'],
        'current': current,
        'hourly_6h': next_6_hours,
        'daily_3d': daily_summary,
        'mountain': mountain_data,
        'alerts': [
            {
                'type': alert['type'],
                'message': alert['message'],
                'severity': alert['severity']
            } 
            for alert in forecast.get('alerts', [])
        ],
        'data_quality': {
            'models': len(forecast['metadata']['models']),
            'members': forecast['metadata']['ensemble_members'],
            'confidence': 'high' if forecast['metadata']['ensemble_members'] > 100 else 'moderate'
        }
    }
    
    return response


def create_dashboard_response(forecast: dict) -> dict:
    """
    Create an ultra-simplified response for dashboard display.
    Just the essentials for quick decision making.
    """
    
    current = forecast['hourly'][0] if forecast.get('hourly') else {}
    
    # Determine primary concern
    concerns = []
    snow_24h = sum([h.get('snowfall', {}).get('mean', 0) for h in forecast.get('hourly', [])[:24]])
    wind_max = max([h.get('wind_speed', {}).get('max', 0) for h in forecast.get('hourly', [])[:24]], default=0)
    
    if snow_24h > 30:
        concerns.append(f"Heavy snow: {snow_24h:.0f}cm/24h")
    elif snow_24h > 10:
        concerns.append(f"Moderate snow: {snow_24h:.0f}cm/24h")
    
    if wind_max > 60:
        concerns.append(f"Strong winds: {wind_max:.0f}km/h")
    
    # Get temperature trend
    if len(forecast.get('hourly', [])) > 6:
        temp_now = current.get('temperature_2m', {}).get('mean', 0)
        temp_6h = forecast['hourly'][6].get('temperature_2m', {}).get('mean', 0)
        temp_trend = "warming" if temp_6h > temp_now + 2 else "cooling" if temp_6h < temp_now - 2 else "stable"
    else:
        temp_trend = "stable"
    
    return {
        'status': forecast['summary']['operational_conditions']['rating'],
        'temperature': current.get('temperature_2m', {}).get('mean'),
        'snow_24h': round(snow_24h, 0),
        'wind': current.get('wind_speed', {}).get('mean'),
        'concerns': concerns[:2],  # Top 2 concerns
        'temp_trend': temp_trend,
        'next_update': forecast['metadata']['generated_at']
    }
