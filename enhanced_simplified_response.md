# Enhanced Simplified Response

The simplified response now includes the additional fields you requested. All numeric values are rounded to 1 decimal place.

## New Fields Added

### In `next_6_hours` (hourly data):
- `wind_direction_80m` - Wind direction in degrees (0-360)
- `freezing_level_height` - Height of freezing level in meters
- `snowfall` - Expected snowfall in centimeters
- `units` - Object showing units for all measurements

### In `daily_summary`:
- `freezing_level` - Object with height in meters
- `snowfall` - Object with min/max values in centimeters  
- `wind` - Object with speed (km/h) and direction (degrees)
- All values include their units for clarity

## Example Enhanced Simplified Response

```json
{
  "metadata": {
    "location_name": "Snoqualmie Pass",
    "latitude": 47.4,
    "longitude": -121.5,
    "forecast_days": 5,
    "models_used": ["ecmwf_ifs025", "gfs_global", "icon_global", "jma_gsm"],
    "generated_at": "2025-11-14T19:30:00Z",
    "generated_at_readable": "November 14, 2025 at 07:30 PM UTC"
  },
  "summary": {
    "executive_summary": "Mixed conditions with light snow likely. Temperatures below freezing.",
    "operational_conditions": {
      "rating": "FAIR",
      "concern_level": "MODERATE",
      "primary_hazards": ["Moderate snowfall", "Variable visibility"],
      "key_recommendations": ["Monitor conditions", "Winter gear required"]
    }
  },
  "current": {
    "time": "2025-11-14T20:00:00",
    "temperature_2m": {
      "mean": -2.3,  // Rounded from -2.345
      "min": -3.1,   // Rounded from -3.089
      "max": -1.5    // Rounded from -1.523
    },
    "precipitation": {
      "mean": 0.2,
      "min": 0.0,
      "max": 0.5
    },
    "wind_speed_80m": {
      "mean": 25.3,
      "min": 18.7,
      "max": 31.2
    },
    "wind_direction_80m": 225.0,  // SW direction
    "freezing_level_height": 850.0,  // meters
    "snowfall": 2.1,  // cm
    "probabilities": {
      "precipitation": {
        "measurable": 0.3  // Rounded from 0.253
      }
    },
    "units": {
      "temperature": "°C",
      "precipitation": "mm", 
      "snowfall": "cm",
      "wind_speed": "km/h",
      "wind_direction": "degrees",
      "freezing_level": "m"
    }
  },
  "next_6_hours": [
    // 6 hourly objects with same structure as "current"
  ],
  "daily_summary": [
    {
      "date": "2025-11-15",
      "summary": "Light snow likely with cool temperatures",
      "temperature_range": "-5.2 to 0.1°C",
      "temperature": {
        "min": -5.2,
        "max": 0.1,
        "units": "°C"
      },
      "precipitation_total": 2.5,
      "snowfall": {
        "min": 3.2,   // Rounded from 3.189
        "max": 8.7,   // Rounded from 8.656
        "units": "cm"
      },
      "wind": {
        "speed": 35.8,      // Max wind speed
        "direction": 240.0,  // WSW
        "speed_units": "km/h",
        "direction_units": "degrees"
      },
      "freezing_level": {
        "height": 920.0,
        "units": "m"
      }
    },
    // 2 more daily summaries
  ]
}
```

## Key Improvements

1. **All numeric values rounded to 1 decimal place** - No more 2.345678 values
2. **Wind direction included** - Essential for mountain weather assessment
3. **Freezing level data** - Critical for avalanche and precipitation type assessment
4. **Snowfall amounts** - Both hourly and daily min/max ranges
5. **Clear units** - Every measurement includes its units for clarity
6. **Consistent structure** - Similar fields across hourly and daily data

## Usage in n8n

The response remains compact (~8-9KB) and perfect for workflow automation. The additional fields provide the critical mountain weather data you need while maintaining efficiency.
