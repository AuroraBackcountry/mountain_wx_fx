# Unused Files in Production API

Based on dependency analysis of the production API flow (`forecast_api.py` → `forecast_cli.py` → ...), these files are **NOT used**:

## ❌ Unused Python Files

### 1. **api_caching_middleware.py**
- **Status:** Not imported anywhere
- **Purpose:** Redis/in-memory caching middleware
- **Reason:** Not integrated into `forecast_api.py`
- **Recommendation:** Remove or integrate if caching needed

### 2. **api_improvements.py**
- **Status:** Not imported anywhere
- **Purpose:** Compression and API monitoring features
- **Reason:** Not integrated into `forecast_api.py`
- **Recommendation:** Remove or integrate if needed

### 3. **model_aggregation_strategies.py**
- **Status:** Not imported anywhere
- **Purpose:** Advanced model aggregation strategies
- **Reason:** Functionality not used in production flow
- **Recommendation:** Remove

### 4. **usage_example.py**
- **Status:** Not imported anywhere
- **Purpose:** Simple example script for data processor
- **Reason:** Example/educational file only
- **Recommendation:** Remove (or keep for reference)

### 5. **main.py**
- **Status:** Not imported by API
- **Purpose:** Standalone workflow script
- **Reason:** Standalone script, not part of API flow
- **Note:** Fixed import error, but still not used by production API
- **Recommendation:** Keep for development/testing OR remove

## ❌ Unused HTML Files

### 6. **forecast_widget.html**
- **Status:** Not referenced anywhere
- **Purpose:** HTML widget for forecast display
- **Reason:** Dashboard HTML is embedded in `forecast_api.py` (DASHBOARD_HTML)
- **Recommendation:** Remove (duplicate of embedded dashboard)

## 📋 Files Used in Production

### Core API Files
- ✅ `forecast_api.py` - Main Flask API
- ✅ `forecast_cli.py` - Core forecast function
- ✅ `enhanced_forecast_generator.py` - Forecast generation
- ✅ `mountain_focused_response.py` - Response formatting

### Supporting Modules
- ✅ `data_processor.py` - Data processing
- ✅ `statistics_calculator.py` - Statistics
- ✅ `probability_analyzer.py` - Probabilities
- ✅ `model_comparison.py` - Model comparison
- ✅ `advanced_snow_formulas.py` - Snow calculations
- ✅ `model_mappings.py` - Model name mappings

### Supporting Files
- ✅ `test_api.py` - API tests (useful for testing)
- ✅ `requirements.txt` - Dependencies
- ✅ `setup.sh`, `setup.bat` - Setup scripts

## Summary

**Total Unused Files:** 6
- 5 Python files (.py)
- 1 HTML file (.html)

**Action:** These files can be safely removed without affecting the production API.

