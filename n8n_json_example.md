# n8n JSON Response Examples

## Simplified Response (with `simplified: true`)

This is what you'll get when you include `"simplified": true` in your n8n request:

```json
{
  "metadata": {
    "location_name": "Snoqualmie Pass",
    "latitude": 47.4,
    "longitude": -121.5,
    "forecast_days": 5,
    "models_used": ["ecmwf_ifs025", "gfs_global", "icon_global", "jma_gsm"],
    "generated_at": "2025-11-14T18:31:20.123456",
    "generated_at_readable": "November 14, 2025 at 06:31 PM UTC"
  },
  "summary": {
    "executive_summary": "Mixed conditions over the next 5 days with light to moderate precipitation...",
    "operational_conditions": {
      "rating": "FAIR",
      "concern_level": "MODERATE",
      "primary_hazards": ["Moderate snowfall", "Variable visibility"],
      "key_recommendations": ["Monitor changing conditions", "Prepare for winter weather"]
    }
  },
  "current": {
    "time": "2025-11-14T18:00:00",
    "temperature_2m": {
      "mean": -2.3,
      "min": -3.1,
      "max": -1.5,
      "std": 0.8
    },
    "precipitation": {
      "mean": 0.2,
      "min": 0.0,
      "max": 0.5
    },
    "probabilities": {
      "precipitation": {
        "measurable": 0.25,
        "moderate": 0.1,
        "heavy": 0.0
      }
    }
  },
  "next_6_hours": [
    // Array of 6 hourly forecast objects similar to "current"
  ],
  "daily_summary": [
    {
      "date": "2025-11-15",
      "summary": "Light snow likely with cool temperatures",
      "temperature_range": "-5.2 to 0.1°C",
      "precipitation_total": 2.5
    },
    {
      "date": "2025-11-16", 
      "summary": "Partly cloudy with minimal precipitation",
      "temperature_range": "-3.8 to 1.2°C",
      "precipitation_total": 0.8
    },
    {
      "date": "2025-11-17",
      "summary": "Increasing clouds with possible snow",
      "temperature_range": "-4.1 to -0.5°C", 
      "precipitation_total": 3.2
    }
  ]
}
```

## Full Response (without `simplified` parameter or `simplified: false`)

The full response is much larger (~65KB) and includes:

```json
{
  "metadata": { /* same as simplified */ },
  "summary": { /* same as simplified */ },
  "hourly": [
    // 120-384 hourly forecast objects (5-16 days worth)
    {
      "time": "2025-11-14T18:00:00",
      "temperature_2m": {
        "mean": -2.3,
        "min": -3.1,
        "max": -1.5,
        "std": 0.8,
        "median": -2.2,
        "p25": -2.8,
        "p75": -1.8,
        "trend": "stable"
      },
      "precipitation": { /* detailed stats */ },
      "wind_speed_80m": { /* detailed stats */ },
      "cloud_cover": { /* detailed stats */ },
      "probabilities": {
        "precipitation": { /* detailed probabilities */ },
        "freezing": { /* detailed probabilities */ },
        "strong_winds": { /* detailed probabilities */ }
      },
      "snow_calculations": {
        "snow_depth": { /* detailed snow depth calculations */ },
        "snow_probability": 0.85
      }
    }
    // ... many more hours
  ],
  "daily": [
    // Daily summaries with comprehensive statistics
    {
      "date": "2025-11-15",
      "summary": "Light snow likely with cool temperatures",
      "temperature_2m": { /* min/max/mean stats */ },
      "precipitation": { /* daily totals */ },
      "probabilities": { /* daily probabilities */ }
    }
    // ... more days
  ],
  "alerts": [
    // Weather alerts and warnings
  ],
  "model_comparison": {
    "model_agreement": {
      "temperature": 0.92,
      "precipitation": 0.78
    },
    "outlier_models": {},
    "confidence_assessment": "High confidence in temperature forecast"
  }
}
```

## n8n Configuration

In your n8n HTTP Request node, use this configuration:

```json
{
  "method": "POST",
  "url": "https://mountain-wx-fx.onrender.com/api/forecast",
  "authentication": "none",
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {
        "name": "Content-Type",
        "value": "application/json"
      }
    ]
  },
  "sendBody": true,
  "bodyParameters": {
    "parameters": [
      {
        "name": "latitude",
        "value": "={{$json.latitude}}"
      },
      {
        "name": "longitude", 
        "value": "={{$json.longitude}}"
      },
      {
        "name": "location_name",
        "value": "={{$json.location_name}}"
      },
      {
        "name": "forecast_days",
        "value": "={{$json.forecast_days}}"
      },
      {
        "name": "simplified",
        "value": true
      }
    ]
  }
}
```

**Important**: Always use `"simplified": true` for n8n workflows to avoid overwhelming the system with large responses.
