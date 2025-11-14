# 🏔️ Mountain Weather Forecast System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open-Meteo API](https://img.shields.io/badge/API-Open--Meteo-green)](https://open-meteo.com/)

Complete ensemble weather forecast processing system designed for mountain environments. Integrates with Open-Meteo API to generate detailed JSON forecasts with statistics, probabilities, and model comparisons.

## 📁 Project Structure

```
.
├── README.md                       # This file
├── PROJECT_SUMMARY.md              # High-level project overview
├── SNOW_FORMULAS.md                # Documentation for snow calculations
│
├── main.py                         # Complete integration script
├── data_processor.py               # Open-Meteo API response processor
├── statistics_calculator.py        # Ensemble statistics (min/max/mean/trends)
├── probability_analyzer.py         # Event probabilities
├── model_comparison.py             # Model agreement/disagreement analysis
├── forecast_generator.py           # JSON forecast generator
├── advanced_snow_formulas.py       # Physically-based snow calculations
├── usage_example.py                # Simple usage example
│
├── forecast_cli.py                 # Command-line interface for automation
└── n8n_integration.md              # n8n workflow integration guide
```

## 🚀 Quick Start

### 1. Set Up Virtual Environment (Recommended)

**Quick Setup (Easiest):**
```bash
# On macOS/Linux:
./setup.sh

# On Windows:
setup.bat
```

**Manual Setup:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Alternative: Direct Installation (Not Recommended)**
```bash
pip install openmeteo-requests requests-cache retry-requests numpy pandas
```

### 2. Run Complete Workflow

```bash
python main.py
```

This will:
- Fetch ensemble data from Open-Meteo
- Process all forecast models
- Calculate statistics and probabilities
- Compare models
- Calculate snowfall (if conditions allow)
- Generate structured JSON output
- Save to `forecast_output.json`

### 3. Use Individual Modules

```python
from data_processor import DataProcessor
from forecast_generator import ForecastGenerator

# Get your Open-Meteo responses
responses = openmeteo.weather_api(url, params)

# Process them
processor = DataProcessor()
data = processor.process_responses(responses)

# Generate forecast
generator = ForecastGenerator()
location = {"lat": 50.06, "lon": -123.15, "name": "Squamish, BC"}
forecast = generator.generate_forecast(data, location)

# Export to JSON
json_output = generator.to_json(forecast)
```

## 📊 Core Modules

### DataProcessor
Processes Open-Meteo API responses into pandas DataFrames.

```python
from data_processor import DataProcessor

processor = DataProcessor()
data = processor.process_responses(responses)

# Returns: {'hourly': DataFrame, 'daily': DataFrame}
# Columns: model_variable_memberN (e.g., ecmwf_ifs025_temperature_2m_member0)
```

### StatisticsCalculator
Calculates ensemble statistics across all models and members.

```python
from statistics_calculator import StatisticsCalculator

stats = StatisticsCalculator()

# Calculate stats for a variable
temp_stats = stats.calculate_statistics(df, 'temperature_2m')
# Returns DataFrame with: min, max, mean, median, std, p10, p25, p75, p90

# Calculate trends
trends = stats.calculate_trend(temp_stats['mean'])
# Returns: ['stable', 'rising', 'rapidly_rising', 'falling', 'rapidly_falling']
```

### ProbabilityAnalyzer
Calculates event probabilities from ensemble spread.

```python
from probability_analyzer import ProbabilityAnalyzer

prob = ProbabilityAnalyzer()

# Precipitation probabilities
precip_probs = prob.calculate_precipitation_probabilities(df)
# Returns: p_measurable, p_heavy (>5mm), p_very_heavy (>10mm)

# Temperature probabilities
temp_probs = prob.calculate_temperature_probabilities(df)
# Returns: p_freezing, p_hard_freeze, p_hot

# Wind probabilities
wind_probs = prob.calculate_wind_probabilities(df)
# Returns: p_breezy (>25), p_windy (>40), p_very_windy (>60 km/h)
```

### ModelComparison
Compares forecast models to identify agreement/disagreement.

```python
from model_comparison import ModelComparison

comp = ModelComparison()

# Compare models for a variable
comparison_df, model_means = comp.compare_models(df, 'temperature_2m')
# Returns: mean, std, range, coefficient of variation

# Identify outliers
outliers = comp.identify_outliers(model_means, threshold=1.5)
# Returns: outlier flags and z-scores for each model

# Get agreement level
agreement = comp.calculate_agreement_level(cv)
# Returns: 'high', 'moderate', or 'low'
```

### AdvancedSnowFormulas
Physically-based snow calculations using wet-bulb temperature, phase probability, and variable SLR.

```python
from advanced_snow_formulas import snowfall_cm

# Simple calculation
snow = snowfall_cm(
    temp_c=-4.0,
    rh_pct=85.0,
    precip_mm=10.0,
    duration_h=12.0
)

# Array processing
import numpy as np
temps = np.array([-6, -4, -2, 0])
rh = np.array([80, 85, 90, 95])
precip = np.array([5, 10, 15, 10])
snow_array = snowfall_cm(temps, rh, precip, duration_h=1.0)
```

See `SNOW_FORMULAS.md` for complete documentation.

### ForecastGenerator
Combines everything into structured JSON output.

```python
from forecast_generator import ForecastGenerator

generator = ForecastGenerator()

# Generate complete forecast
forecast = generator.generate_forecast(
    data={'hourly': hourly_df, 'daily': daily_df},
    location={'lat': 50.06, 'lon': -123.15, 'name': 'Squamish, BC'},
    variables=['temperature_2m', 'precipitation', 'wind_speed_80m']
)

# Convert to JSON
json_str = generator.to_json(forecast, pretty=True)
```

## 📋 JSON Output Structure

```json
{
  "metadata": {
    "generated_at": "2025-11-14T17:00:00Z",
    "location": {"lat": 50.06, "lon": -123.15, "name": "Squamish, BC"},
    "forecast_start": "2025-11-14T18:00:00Z",
    "forecast_end": "2025-11-17T18:00:00Z",
    "models": ["ECMWF_IFS", "GEM", "ECMWF_AIFS", "GFS"],
    "ensemble_members": 200
  },
  "summary": {
    "executive_summary": "Temps 5 to 12°C. Rain expected.",
    "key_concerns": ["heavy precipitation"],
    "operational_conditions": {
      "rating": "FAIR",
      "rationale": "Watch for heavy precipitation"
    }
  },
  "hourly": [
    {
      "time": "2025-11-14T18:00:00Z",
      "temperature_2m": {
        "min": 4.2,
        "max": 6.8,
        "mean": 5.5,
        "median": 5.4,
        "std_dev": 0.8,
        "trend": "rising",
        "percentiles": {"p10": 4.5, "p25": 5.0, "p75": 6.0, "p90": 6.5}
      },
      "precipitation": { /* ... */ },
      "probabilities": {
        "precipitation": {"measurable": 0.85, "heavy": 0.15},
        "freezing": 0.02,
        "strong_winds": 0.35
      }
    }
  ],
  "daily": [ /* ... */ ],
  "model_comparison": [
    {
      "variable": "temperature_2m",
      "agreement_level": "high",
      "models_in_agreement": ["ECMWF_IFS", "GEM", "ECMWF_AIFS"],
      "outlier_models": ["GFS"],
      "spread": 2.3,
      "coefficient_variation": 0.08,
      "model_values": {
        "ecmwf_ifs025": 5.5,
        "gem_global": 5.7,
        "ecmwf_aifs025": 5.4,
        "gfs_seamless": 7.8
      }
    }
  ]
}
```

## 🎯 Common Use Cases

### 1. Basic Forecast

```python
from main import main

# Run complete workflow
forecast = main()
```

### 2. Custom Location and Variables

```python
from data_processor import DataProcessor
from forecast_generator import ForecastGenerator
import openmeteo_requests

# Setup API
openmeteo = openmeteo_requests.Client()

# Custom parameters
params = {
    "latitude": 49.28,
    "longitude": -123.12,
    "hourly": ["temperature_2m", "precipitation", "wind_speed_80m"],
    "models": ["ecmwf_ifs025", "gem_global"],
    "forecast_days": 5
}

responses = openmeteo.weather_api(url, params=params)

# Process and generate
processor = DataProcessor()
data = processor.process_responses(responses)

generator = ForecastGenerator()
location = {"lat": 49.28, "lon": -123.12, "name": "Vancouver, BC"}
forecast = generator.generate_forecast(data, location)
```

### 3. Snowfall Analysis

```python
from advanced_snow_formulas import AdvancedSnowFormulas

# Calculate snowfall for each ensemble member
snow_calc = AdvancedSnowFormulas()

temp_cols = [col for col in df.columns if 'temperature_2m' in col]
rh_cols = [col for col in df.columns if 'relative_humidity' in col]
precip_cols = [col for col in df.columns if 'precipitation' in col]

for i, (t, rh, p) in enumerate(zip(temp_cols, rh_cols, precip_cols)):
    df[f'snow_member{i}'] = snow_calc.calculate_snowfall(
        df[t], df[rh], df[p], duration_h=1.0
    )

# Get snow statistics
snow_mean = df[[c for c in df.columns if 'snow_member' in c]].mean(axis=1)
snow_max = df[[c for c in df.columns if 'snow_member' in c]].max(axis=1)
```

### 4. Probability Analysis

```python
from probability_analyzer import ProbabilityAnalyzer

prob = ProbabilityAnalyzer()

# Custom probability calculation
p_light_rain = prob.calculate_probability(
    df, 'precipitation', 
    lambda x: (x > 0.1) & (x < 2.0)
)

# Temperature in specific range
p_ideal_temp = prob.calculate_probability(
    df, 'temperature_2m',
    lambda x: (x >= 15) & (x <= 25)
)
```

## ⚙️ Configuration

### Tuning Snow Formulas for Your Region

```python
from advanced_snow_formulas import AdvancedSnowFormulas

# Maritime climate (wetter, denser snow)
snow = AdvancedSnowFormulas.calculate_snowfall(
    temp, rh, precip, duration,
    r_max=12.0,      # Lower max SLR
    t_peak=-10.0,    # Warmer optimal temp
    gamma=0.25       # Stronger humidity effect
)

# Continental climate (drier, fluffier snow)
snow = AdvancedSnowFormulas.calculate_snowfall(
    temp, rh, precip, duration,
    r_max=22.0,      # Higher max SLR
    t_peak=-14.0,    # Colder optimal temp
    gamma=0.15       # Weaker humidity effect
)
```

### Custom Probability Thresholds

Modify thresholds in `probability_analyzer.py`:
- Change precipitation amounts (currently 5mm, 10mm)
- Adjust wind speed thresholds (currently 25, 40, 60 km/h)
- Customize temperature thresholds

### Trend Detection Sensitivity

Modify in `statistics_calculator.py`:
- `window`: Number of hours for trend calculation (default: 3)
- Rate thresholds for rapid changes (default: ±2.0 per hour)

## 🔧 Troubleshooting

**Problem: No data returned**
- Check internet connection
- Verify coordinates are valid
- Check Open-Meteo API status

**Problem: Missing variables**
- Verify variable names match Open-Meteo API
- Check that requested variables are in the data
- Use `processor.get_variable_columns(df, 'var_name')` to list available columns

**Problem: Model comparison fails**
- Ensure multiple models are requested
- Check that all models have data for the variable
- Try with default models: `["ecmwf_ifs025", "gem_global", "ecmwf_aifs025", "gfs_seamless"]`

## 📚 Additional Resources

- **PROJECT_SUMMARY.md**: High-level project overview and objectives
- **SNOW_FORMULAS.md**: Complete documentation of snow calculation formulas
- **Open-Meteo API Docs**: https://open-meteo.com/en/docs/ensemble-api

## 🤝 Contributing

This codebase is designed for easy extension:

1. Add new probability calculations in `probability_analyzer.py`
2. Add new statistical metrics in `statistics_calculator.py`
3. Customize JSON output structure in `forecast_generator.py`
4. Tune snow formulas in `advanced_snow_formulas.py`

## 📝 Notes

- All times are in UTC by default (configurable via Open-Meteo timezone parameter)
- Ensemble members are numbered sequentially across all models
- Missing data is handled gracefully (returns empty arrays/dicts)
- Cache is stored in `.cache` directory (auto-refreshes after 1 hour)

## 🎓 Understanding the Output

**Ensemble Statistics:**
- `min/max`: Range across all ensemble members
- `mean`: Average (most likely value)
- `std_dev`: Spread/uncertainty (higher = more uncertain)
- `p10/p90`: 80% confidence interval

**Probabilities:**
- Based on fraction of ensemble members meeting criteria
- 0.0 = 0% chance, 1.0 = 100% chance
- Use 0.3-0.7 as "possible", >0.7 as "likely"

**Model Agreement:**
- `high`: Models closely agree (CV < 0.1)
- `moderate`: Some spread (CV 0.1-0.3)
- `low`: Significant disagreement (CV > 0.3)

**Trends:**
- `stable`: No significant change
- `rising/falling`: Gradual change (>0.5 units/hour)
- `rapidly_rising/falling`: Quick change (>2.0 units/hour)

---

## 🔌 Integration Options

### Command-Line Interface

For easy integration with automation tools:

```bash
# Basic usage
python forecast_cli.py --lat 47.6062 --lon -122.3321 --days 3

# With location name and stdout output
python forecast_cli.py --lat 47.6062 --lon -122.3321 --name "Seattle, WA" --output stdout

# Help and options
python forecast_cli.py --help
```

### n8n Workflow Integration

See `n8n_integration.md` for detailed instructions on:
- Command execution nodes
- HTTP API wrapper setup  
- Example workflows
- JSON data processing

### Automation Use Cases

- **Scheduled Weather Reports**: Daily forecasts for multiple locations
- **Alert Systems**: Trigger notifications based on weather thresholds
- **Data Collection**: Archive forecasts for historical analysis
- **Dashboard Integration**: Real-time weather data for web applications

---

Ready to use! Open this project and start with `main.py` for a complete working example.
