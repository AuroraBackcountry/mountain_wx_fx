# Full Response vs Simplified Response

## Response Sizes
- **Simplified (`simplified: true`)**: ~7 KB
- **Full (`simplified: false`)**: ~65 KB (9x larger!)

## Full Response Structure

When you set `simplified: false` or omit the parameter entirely, you get a comprehensive forecast with:

### 1. **Hourly Forecasts** (72 points for 3 days)
Each hour includes detailed ensemble statistics:
```json
{
  "time": "2025-11-14T19:00:00",
  "temperature_2m": {
    "mean": -2.3,
    "min": -3.1,
    "max": -1.5,
    "std": 0.8,
    "median": -2.2,
    "p25": -2.8,      // 25th percentile
    "p75": -1.8,      // 75th percentile
    "trend": "stable" // or "increasing"/"decreasing"
  },
  "precipitation": {
    "mean": 0.2,
    "min": 0.0,
    "max": 0.5,
    "std": 0.15,
    "median": 0.1,
    "p25": 0.0,
    "p75": 0.3,
    "trend": "stable"
  },
  "wind_speed_80m": {
    // Similar detailed statistics
  },
  "probabilities": {
    "precipitation": {
      "measurable": 0.25,  // >0.1mm
      "moderate": 0.10,    // >2.5mm
      "heavy": 0.0         // >10mm
    },
    "freezing": {
      "at_surface": 0.85,
      "at_2m": 0.90
    },
    "strong_winds": {
      "moderate": 0.15,    // >40 km/h
      "strong": 0.05,      // >60 km/h
      "extreme": 0.0       // >80 km/h
    }
  },
  "snow_calculations": {
    "snow_depth": {
      "low": 0.5,
      "expected": 2.1,
      "high": 3.8
    },
    "snow_probability": 0.85
  }
}
```

### 2. **Daily Summaries** (3 days)
Aggregated daily statistics:
```json
{
  "date": "2025-11-15",
  "day_of_week": "Saturday",
  "summary": "Light snow likely with cool temperatures throughout the day",
  "temperature_2m": {
    "min": -5.2,
    "max": 0.1,
    "mean": -2.5,
    // Plus all the ensemble statistics
  },
  "precipitation": {
    "total": 5.2,
    "min": 2.1,
    "max": 8.3,
    // Plus percentiles and trends
  }
}
```

### 3. **Model Comparison**
Analysis of forecast confidence:
```json
"model_comparison": {
  "model_agreement": {
    "temperature": 0.92,      // High agreement
    "precipitation": 0.78,    // Moderate agreement
    "wind": 0.85
  },
  "outlier_models": {
    "temperature": [],
    "precipitation": ["jma_gsm"]  // Japan model differs
  },
  "confidence_assessment": "High confidence in temperature, moderate confidence in precipitation timing"
}
```

### 4. **Complete Metadata**
```json
"metadata": {
  "location_name": "Snoqualmie Pass",
  "latitude": 47.4,
  "longitude": -121.5,
  "elevation": 920,
  "forecast_days": 3,
  "models_used": ["ecmwf_ifs025", "gfs_global", "icon_global", "jma_gsm"],
  "ensemble_members": 180,
  "generated_at": "2025-11-14T18:45:00Z",
  "generated_at_readable": "November 14, 2025 at 06:45 PM UTC"
}
```

## When to Use Each

### Use Simplified (`simplified: true`)
- ✅ For n8n workflows
- ✅ For quick dashboards
- ✅ When you need current conditions + near-term forecast
- ✅ For mobile apps or bandwidth-limited scenarios
- ✅ When you only need key decision-making data

### Use Full Response (`simplified: false`)
- ✅ For detailed analysis applications
- ✅ When you need ensemble statistics (percentiles, std dev)
- ✅ For scientific/research purposes
- ✅ When building comprehensive weather displays
- ✅ For model comparison and confidence assessment
- ✅ When you need hourly data beyond 6 hours

## Key Differences

| Feature | Simplified | Full |
|---------|-----------|------|
| Response Size | ~7 KB | ~65 KB |
| Hourly Data | Next 6 hours | All hours (72-384) |
| Statistics | Basic (min/max/mean) | Complete (percentiles, std, trends) |
| Model Comparison | ❌ | ✅ |
| Snow Calculations | Basic | Detailed ranges |
| Probabilities | Basic | Detailed thresholds |
| Processing Time | Fast | Slower |
| Best For | Automation/Display | Analysis/Research |
