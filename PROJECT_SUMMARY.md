# Weather Forecast System - Project Summary

## Objective
Build a system that processes ensemble weather forecast data from Open-Meteo API and produces structured JSON forecasts. The goal is to take large datasets and compile them into focused, meaningful forecasts with statistics, probabilities, trends, and model comparisons.

## Data Source

### Open-Meteo Ensemble API
- **API**: `https://ensemble-api.open-meteo.com/v1/ensemble`
- **Models**: ECMWF IFS, GEM Global, ECMWF AIFS, GFS Seamless
- **Format**: Multiple ensemble members per model
- **Column naming**: `{model}_{variable}_member{N}` (e.g., `ecmwf_ifs025_temperature_2m_member0`)
- **Timeframes**: Both hourly and daily data
- **Index**: DatetimeIndex

### Key Variables
**Hourly:**
- Temperature (2m, 850hPa)
- Precipitation, Snowfall
- Wind (speed, direction at 80m and 10m)
- Cloud cover, Humidity, Dew point
- Surface pressure, Freezing level height

**Daily:**
- Temperature (min, max, mean)
- Precipitation sum
- Wind (speed mean, gusts, direction)
- Cloud cover (min, max)
- Humidity, Dew point

## System Architecture

### 1. Data Processor (`data_processor.py`)
Processes Open-Meteo API responses directly:
- Takes raw `responses` from `openmeteo.weather_api()`
- Extracts hourly and daily DataFrames
- Handles all models and ensemble members
- Prefixes columns with model names
- Returns: `{'hourly': DataFrame, 'daily': DataFrame}`

### 2. Statistics Calculator (`statistics_calculator.py`)
Calculates ensemble statistics for each variable:
- **Min/Max**: Range across all ensemble members
- **Mean**: Average of all members
- **Median**: Middle value
- **Std Dev**: Spread/uncertainty
- **Percentiles**: 10th, 25th, 75th, 90th
- **Trends**: Rising, Falling, Rapidly Rising, Rapidly Falling (based on hour-over-hour changes)

### 3. Probability Analyzer (`probability_analyzer.py`)
Calculates event probabilities from ensemble spread:
- **Precipitation**: P(measurable), P(>5mm), P(>10mm)
- **Snow**: P(snow), P(>5cm), P(>10cm)
- **Temperature**: P(freezing), P(<0°C), P(>30°C)
- **Wind**: P(>25 km/h), P(>40 km/h), P(>60 km/h)
- **Probability = (members meeting criteria) / (total members)**

### 4. Model Comparison (`model_comparison.py`)
Compares models to identify agreement/disagreement:
- Analyzes each variable across models
- Identifies outliers (models deviating >1.5 std dev from mean)
- Calculates agreement level (high/moderate/low based on coefficient of variation)
- Tracks which specific models agree or disagree

### 5. Forecast Generator (`forecast_generator.py`)
Produces final JSON output with:
- Metadata (location, generation time, models, ensemble members)
- Executive summary (brief text summary)
- Hourly and daily forecasts with statistics, probabilities, trends
- Model comparison results
- Operational conditions assessment

## Desired JSON Output Structure

```json
{
  "metadata": {
    "generated_at": "ISO timestamp",
    "location": {"lat": float, "lon": float, "name": "string"},
    "forecast_start": "ISO timestamp",
    "forecast_end": "ISO timestamp",
    "models": ["ECMWF_IFS", "GEM", "ECMWF_AIFS", "GFS"],
    "ensemble_members": int
  },
  "summary": {
    "executive_summary": "Brief text summary",
    "key_concerns": ["list of concerns"],
    "operational_conditions": {
      "rating": "GOOD/FAIR/POOR",
      "rationale": "explanation"
    }
  },
  "hourly": [
    {
      "time": "ISO timestamp",
      "temperature_2m": {
        "min": float,
        "max": float,
        "mean": float,
        "median": float,
        "std_dev": float,
        "trend": "rising/falling/rapidly_rising/rapidly_falling/stable",
        "percentiles": {"p10": float, "p25": float, "p75": float, "p90": float}
      },
      "precipitation": { /* same structure */ },
      "wind_speed_80m": { /* same structure */ },
      "probabilities": {
        "precipitation": {"measurable": float, "heavy": float},
        "freezing": float,
        "strong_winds": float
      }
    }
  ],
  "daily": [
    {
      "date": "ISO date",
      "temperature_2m": { /* statistics */ },
      "precipitation_sum": { /* statistics */ },
      "probabilities": { /* event probabilities */ },
      "summary": "Brief daily summary text"
    }
  ],
  "model_comparison": [
    {
      "variable": "temperature_2m",
      "agreement_level": "high/moderate/low",
      "models_in_agreement": ["model1", "model2"],
      "outlier_models": ["model3"],
      "details": "explanation"
    }
  ]
}
```

## Key Requirements

1. **JSON Output**: Structured data for downstream use
2. **Statistics**: Min, max, mean, median, std dev, percentiles for all variables
3. **Trends**: Identify rising/falling patterns
4. **Probabilities**: Calculate event likelihoods from ensemble spread
5. **Model Comparison**: Identify model agreement/disagreement and outliers
6. **Brief Summaries**: Concise text summaries at executive and daily levels
7. **Technical Detail**: Full statistics available alongside summaries

## Usage Pattern

```python
# 1. Fetch data from Open-Meteo
responses = openmeteo.weather_api(url, params=params)

# 2. Process responses
processor = DataProcessor()
data = processor.process_responses(responses)

# 3. Calculate statistics
stats_calc = StatisticsCalculator()
hourly_stats = stats_calc.calculate_statistics(data['hourly'], 'temperature_2m')

# 4. Calculate probabilities
prob_analyzer = ProbabilityAnalyzer()
precip_probs = prob_analyzer.calculate_precipitation_probabilities(data['hourly'])

# 5. Compare models
comparison = ModelComparison()
model_results = comparison.compare_models(data['hourly'], 'temperature_2m')

# 6. Generate forecast
generator = ForecastGenerator()
forecast_json = generator.generate_forecast(data, location_info)
```

## Current Status
- ✅ Data Processor built and tested
- ✅ Statistics Calculator complete
- ✅ Probability Analyzer complete
- ✅ Model Comparison complete
- ✅ Forecast Generator complete
- ⏳ Integration and end-to-end testing needed
- ⏳ Real-world validation with actual Open-Meteo data

## Next Steps
1. Create main integration script that ties all components together
2. Test with real Open-Meteo API responses
3. Validate JSON output structure
4. Fine-tune probability thresholds and trend detection
5. Optimize for performance with large datasets
