# Mountain Weather API Integration Guide

## Core Principles Maintained ✅

Your mountain weather forecast API maintains all core requirements while adding performance:

### 1. **Super Accurate 6-Hour Forecast**
```json
"next_6_hours": [
  {
    "hour": 1,
    "temperature": {
      "value": -2.5,
      "min": -3.2,
      "max": -1.8,
      "feels_like": -5.8
    },
    "freezing_level": 850,
    "snowfall": {
      "amount": 2.3,
      "probability": 85
    },
    "wind": {
      "speed": 25.5,
      "gusts": 35.2,
      "direction": "SW",
      "direction_degrees": 225
    }
  }
]
```

### 2. **Accurate 3-Day Forecast**
```json
"next_3_days": [
  {
    "date": "2025-11-15",
    "temperature": {
      "min": -8.5,
      "max": 2.3,
      "range": 10.8
    },
    "snowfall": {
      "total": 25.5,
      "max_rate": 4.2
    },
    "freezing_level": {
      "average": 1200,
      "trend": "rising"
    }
  }
]
```

### 3. **Advanced Trends**
```json
"trends": {
  "temperature": "rising_rapidly",
  "sky": "clearing",
  "wind": "increasing",
  "precipitation": "developing",
  "summary": "Temperature rising rapidly, clearing skies, wind increasing."
}
```

## Simple Integration

### Option 1: Minimal Changes to Current API
Just update `forecast_api.py` with the mountain-focused response:

```python
from mountain_focused_response import create_mountain_focused_response
from api_caching_middleware import APICache

# Add caching to your existing endpoint
@app.route('/api/forecast', methods=['POST'])
@APICache.cache_endpoint(ttl=600)  # Cache 10 minutes
def get_forecast():
    # Your existing code to get data
    forecast = run_forecast(lat, lon, days, location_name)
    
    # Use mountain-focused response for simplified
    if simplified:
        response = create_mountain_focused_response(
            forecast, 
            location_name,
            elevation=data.get('elevation', None)  # Optional elevation
        )
    else:
        response = forecast
    
    return jsonify(response)
```

### Option 2: Keep Both Response Formats
Support legacy and new formats:

```python
@app.route('/api/forecast', methods=['POST'])
@APICache.cache_endpoint(ttl=600)
def get_forecast():
    data = request.json
    response_format = data.get('format', 'legacy')  # 'legacy' or 'mountain'
    
    forecast = run_forecast(lat, lon, days, location_name)
    
    if response_format == 'mountain':
        response = create_mountain_focused_response(
            forecast,
            location_name,
            elevation=data.get('elevation')
        )
    else:
        # Your existing response format
        response = create_simplified_response(forecast, location_name)
    
    return jsonify(response)
```

## n8n Integration Example

### HTTP Request Node Configuration
```json
{
  "method": "POST",
  "url": "https://mountain-wx-fx.onrender.com/api/forecast",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "latitude": 49.650738,
    "longitude": -123.074821,
    "location_name": "Whistler",
    "forecast_days": 3,
    "elevation": 2181,
    "format": "mountain"
  }
}
```

### n8n Expression Examples
Access the clean, structured data easily:

```javascript
// Current temperature
{{$json.current_conditions.temperature.value}}

// Today's snowfall total
{{$json.next_3_days[0].snowfall.total}}

// Temperature trend
{{$json.trends.temperature}}

// Wind alert check
{{$json.next_6_hours[0].wind.gusts > 50 ? "HIGH WIND" : "Normal"}}

// Freezing level
{{$json.current_conditions.freezing_level.height}}
```

## Performance Without Disruption

### What's Added (Invisible to n8n):
- **Caching**: Identical requests return instantly
- **Compression**: Smaller payload, same data
- **Monitoring**: `/api/status` and `/api/metrics` endpoints
- **Rate Limiting**: Protection from abuse

### What Stays the Same:
- ✅ Exact same endpoint URL
- ✅ Same request format
- ✅ Same JSON structure (or better with mountain format)
- ✅ Same accuracy
- ✅ Same model ensemble

## Quick Start

1. **No Changes Needed**
   Your existing n8n workflows continue working

2. **Optional Enhancement**
   Add `"format": "mountain"` to get enhanced trends

3. **Optional Elevation**
   Add `"elevation": 2181` for reference in response

## Accuracy Improvements

The enhanced system provides:
- **Better snowfall**: Calculated per ensemble member
- **Better freezing level**: Fallback estimation when GFS unavailable  
- **Better wind**: Intelligent 80m/10m fallback with terrain adjustment
- **Better trends**: 6-hour analysis with clear descriptions

## Sample Response

```json
{
  "location": {
    "name": "Whistler",
    "coordinates": {
      "latitude": 49.650738,
      "longitude": -123.074821
    },
    "elevation": 2181
  },
  "current_conditions": {
    "temperature": {
      "value": -2.5,
      "feels_like": -6.2,
      "unit": "°C"
    },
    "freezing_level": {
      "height": 850,
      "unit": "meters"
    },
    "wind": {
      "speed": 25.5,
      "gusts": 35.2,
      "direction": "SW",
      "unit": "km/h"
    },
    "snowfall": {
      "rate": 2.3,
      "unit": "cm/hr"
    }
  },
  "trends": {
    "temperature": "falling",
    "sky": "clouding_up",
    "wind": "increasing",
    "precipitation": "developing",
    "summary": "Temperature falling, increasing clouds, wind increasing, precipitation developing."
  },
  "next_6_hours": [...],
  "next_3_days": [...],
  "accuracy_metrics": {
    "models_used": 4,
    "ensemble_members": 143,
    "confidence_score": 0.92
  }
}
```

## Deployment

No changes to your current deployment! The enhancements are backward compatible:

```bash
# Just update and push
git pull
git push

# Render auto-deploys
```

## Summary

Your core requirements are not just maintained—they're enhanced:
- ✅ 6-hour forecast: Now with trends and feels-like
- ✅ 3-day forecast: Now with hazard identification  
- ✅ Advanced snowfall: Already implemented, now cached
- ✅ Accurate temperatures: Min/max from all ensemble members
- ✅ Freezing level: Always available (direct or estimated)
- ✅ Wind & direction: Complete with gusts and degrees
- ✅ Elevation: Add to request, appears in response
- ✅ Trends: Comprehensive analysis with plain English
- ✅ n8n ready: Clean JSON, easy expressions
