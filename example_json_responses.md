# Mountain Weather API - JSON Response Examples

## 🎯 Simplified Response (7KB) - Recommended for n8n

When you send `"simplified": true` in your request, you get this structure:

```json
{
  "metadata": {
    "generated_at": "2025-11-14T18:25:08.453981Z",
    "generated_at_readable": "November 14, 2025 at 06:25 PM UTC",
    "location": {
      "lat": 50.06,
      "lon": -123.15,
      "name": "Squamish, BC"
    },
    "models": ["ECMWF_AIFS", "ECMWF_IFS", "GEM", "GFS"],
    "ensemble_members": 154,
    "forecast_start": "2025-11-14T08:00:00+00:00",
    "forecast_end": "2025-11-17T07:00:00+00:00"
  },
  
  "summary": {
    "executive_summary": "Temps -4 to 5°C. Rain expected.",
    "key_concerns": [],
    "operational_conditions": {
      "rating": "GOOD",
      "rationale": "Favorable conditions"
    }
  },
  
  "current": {
    "time": "2025-11-14T08:00:00+00:00",
    "temperature_2m": {
      "mean": 1.48,
      "min": -1.45,
      "max": 3.8,
      "median": 1.55,
      "std_dev": 0.95,
      "trend": "stable",
      "percentiles": {
        "p10": 0.17,
        "p25": 0.9,
        "p75": 2.19,
        "p90": 2.53
      }
    },
    "precipitation": {
      "mean": 0.006,
      "min": 0.0,
      "max": 0.1,
      "median": 0.0,
      "std_dev": 0.025,
      "trend": "stable"
    },
    "wind_speed_80m": {
      "mean": 5.2,
      "min": 1.48,
      "max": 10.46,
      "median": 5.09,
      "std_dev": 2.04,
      "trend": "stable"
    },
    "probabilities": {
      "precipitation": {
        "measurable": 0.06,
        "heavy": 0.0
      },
      "freezing": 0.14,
      "strong_winds": 0.0
    }
  },
  
  "next_6_hours": [
    // Array of 6 hourly entries with same structure as "current"
  ],
  
  "daily_summary": [
    {
      "date": "2025-11-14",
      "summary": "Temps -4 to 5°C. Rain expected.",
      "temperature_range": "-3.95 to 5.35°C",
      "precipitation_total": 9.04
    },
    {
      "date": "2025-11-15",
      "summary": "Temps -2 to 8°C. Rain expected.",
      "temperature_range": "-2.25 to 8.15°C",
      "precipitation_total": 7.16
    }
  ]
}
```

## 📦 Full Response (65KB+) - Too large for n8n

Without `"simplified": true`, you get:

```json
{
  "metadata": {...},
  "summary": {...},
  "hourly": [
    // 72 hourly entries, each with full statistics for all variables
    {
      "time": "2025-11-14T08:00:00+00:00",
      "temperature_2m": {
        "min": -1.45,
        "max": 3.8,
        "mean": 1.48,
        "median": 1.55,
        "std_dev": 0.95,
        "trend": "stable",
        "percentiles": {...}
      },
      "precipitation": {...},
      "wind_speed_80m": {...},
      "wind_direction_80m": {...},
      "relative_humidity_2m": {...},
      "probabilities": {...}
    }
    // ... 71 more entries
  ],
  "daily": [
    // 3 daily entries with full statistics
  ],
  "model_comparison": [
    // Detailed model agreement analysis
  ]
}
```

## 🔧 n8n HTTP Request Configuration

### ✅ Correct Configuration:

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
  "specifyBody": "json",
  "jsonBody": "{\n  \"latitude\": {{$json.latitude}},\n  \"longitude\": {{$json.longitude}},\n  \"location_name\": \"{{$json.location_name}}\",\n  \"forecast_days\": {{$json.forecast_days || 3}},\n  \"simplified\": true\n}",
  "options": {
    "timeout": 30000,
    "response": {
      "response": {
        "responseFormat": "json"
      }
    }
  }
}
```

## 📊 Extracting Data in n8n

After the HTTP Request node, you can access the data:

- **Current Temperature**: `{{$json.current.temperature_2m.mean}}`
- **Summary**: `{{$json.summary.executive_summary}}`
- **Rating**: `{{$json.summary.operational_conditions.rating}}`
- **Rain Probability**: `{{$json.current.probabilities.precipitation.measurable}}`
- **Daily High**: `{{$json.daily_summary[0].temperature_range}}`

## 🚨 Troubleshooting

1. **Still getting 65KB response?**
   - Make sure `"simplified": true` is in the request body
   - Wait 5 minutes for Render deployment to complete

2. **JSON Parse Error?**
   - Check the response in n8n's output panel
   - Verify Content-Type header is set
   - Ensure responseFormat is set to "json"

3. **Test with cURL:**
   ```bash
   curl -X POST https://mountain-wx-fx.onrender.com/api/forecast \
     -H "Content-Type: application/json" \
     -d '{"latitude": 50.06, "longitude": -123.15, "simplified": true}'
   ```
