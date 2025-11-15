# Codebase Review - Alignment with Goal

## Goal
**Input:** Latitude/Longitude  
**Output:** 
- 6-hour detailed forecast
- 3-day forecast

## Current Production Flow

```
forecast_api.py (API endpoint)
  ↓
forecast_cli.run_forecast()
  ↓
EnhancedForecastGenerator.generate_forecast()
  ↓
mountain_focused_response.create_mountain_focused_response()
  ↓
Returns: {next_6_hours, next_3_days, ...}
```

## ✅ Files Used in Production API

### Core API Files
- **forecast_api.py** - Main Flask API (KEEP - Required)
  - Contains HTML Dashboard (KEEP as requested)
  - `/api/forecast` endpoint
  - `/api/health` endpoint
  - `/api/test-forecast` endpoint

### Core Processing Files
- **forecast_cli.py** - Core forecast function `run_forecast()` (KEEP - Required)
- **enhanced_forecast_generator.py** - Generates forecast data (KEEP - Required)
- **mountain_focused_response.py** - Formats response for 6-hour + 3-day (KEEP - Required)
- **data_processor.py** - Processes Open-Meteo API responses (KEEP - Required)
- **statistics_calculator.py** - Calculates ensemble statistics (KEEP - Required)
- **probability_analyzer.py** - Calculates event probabilities (KEEP - Required)
- **model_comparison.py** - Compares forecast models (KEEP - Required)
- **advanced_snow_formulas.py** - Snow calculations (KEEP - Required)
- **model_mappings.py** - Model name mappings (KEEP - Required, used by model_comparison and data_processor)

### Supporting Files
- **test_api.py** - API tests (KEEP - Useful for testing)
- **requirements.txt** - Dependencies (KEEP - Required)
- **setup.sh**, **setup.bat** - Setup scripts (KEEP - Useful)

## ❌ Files NOT Used in Production API

### Unused Code Files
1. **main.py** - ❌ **ISSUE: Broken import**
   - Imports `ForecastGenerator` which doesn't exist
   - Should import `EnhancedForecastGenerator` instead
   - Standalone script, not used by API
   - **Recommendation:** Fix import or remove if not needed

2. **usage_example.py** - ❌ **Example only**
   - Simple example script
   - Not used in production
   - **Recommendation:** Keep for reference or remove

3. **api_caching_middleware.py** - ❌ **Not imported**
   - Caching middleware with Redis support
   - Not used in `forecast_api.py`
   - **Recommendation:** Remove or integrate if caching needed

4. **api_improvements.py** - ❌ **Not imported**
   - Compression and monitoring features
   - Not used in `forecast_api.py`
   - **Recommendation:** Remove or integrate if needed

5. **model_aggregation_strategies.py** - ❌ **Not imported**
   - Advanced model aggregation strategies
   - Not used anywhere in codebase
   - **Recommendation:** Remove (functionality may be in EnhancedForecastGenerator)

6. **forecast_generator.py** - ❌ **Doesn't exist**
   - Referenced in `main.py` and docs but file doesn't exist
   - Replaced by `enhanced_forecast_generator.py`
   - **Recommendation:** Update references or create stub if needed

### Unused HTML Files
7. **forecast_widget.html** - ❌ **Not referenced**
   - HTML widget file
   - Not imported or referenced in `forecast_api.py`
   - Dashboard HTML is embedded in `forecast_api.py`
   - **Recommendation:** Remove or integrate if needed

## 📝 Documentation Files (Keep for Reference)

- **README.md** - Project documentation
- **API_ALIGNMENT.md** - API alignment notes
- **api_integration_guide.md** - Integration guide
- **CONTRIBUTING.md** - Contribution guidelines
- **deployment_guide.md** - Deployment instructions
- **MODEL_CAPABILITIES.md** - Model documentation
- **MOUNTAIN_FORECAST_SOLUTION.md** - Solution overview
- **n8n_example.json** - n8n integration example
- **n8n_integration.md** - n8n integration guide
- **OPEN_METEO_INSPIRED_IMPROVEMENTS.md** - Improvement notes
- **OPEN_METEO_INTEGRATION.md** - Integration notes
- **PROJECT_SUMMARY_1.md** - Project summary
- **SNOW_FORMULAS.md** - Snow calculation docs
- **WIND_DATA_STRATEGY.md** - Wind data strategy
- **LICENSE** - License file

**Recommendation:** Keep documentation but note that some references may be outdated.

## 🔧 Issues Found

### 1. Broken Import in main.py
```python
# Line 14 in main.py
from forecast_generator import ForecastGenerator  # ❌ File doesn't exist
```
**Should be:**
```python
from enhanced_forecast_generator import EnhancedForecastGenerator
```

### 2. Redundant Features Not Used
- Caching middleware exists but not integrated
- API improvements exist but not integrated
- Model aggregation strategies exist but not used

### 3. Misalignment
- `main.py` is a standalone script that doesn't align with API goal
- `usage_example.py` is just an example
- `forecast_widget.html` is separate from embedded dashboard

## 📊 Summary

**Total Python Files:** 16
- **Used in Production:** 9 core files
- **Not Used:** 6 files
- **Documentation:** Multiple .md files

**Recommendations:**
1. Fix `main.py` import or remove if not needed
2. Remove unused files: `api_caching_middleware.py`, `api_improvements.py`, `model_aggregation_strategies.py`
3. Decide on `forecast_widget.html` - remove or integrate
4. Keep `usage_example.py` for reference or remove
5. Update documentation to reflect current architecture

## ✅ Core Files Required for Goal

For the goal of "lat/long → 6-hour + 3-day forecast", these files are essential:

1. `forecast_api.py` - API endpoint
2. `forecast_cli.py` - Core forecast function
3. `enhanced_forecast_generator.py` - Forecast generation
4. `mountain_focused_response.py` - Response formatting (creates 6-hour + 3-day)
5. `data_processor.py` - Data processing
6. `statistics_calculator.py` - Statistics
7. `probability_analyzer.py` - Probabilities
8. `model_comparison.py` - Model comparison
9. `advanced_snow_formulas.py` - Snow calculations
10. `model_mappings.py` - Model mappings

All other files are either documentation, examples, or unused code.

