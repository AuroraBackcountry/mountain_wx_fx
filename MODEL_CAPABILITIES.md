# Open-Meteo Model Capabilities Matrix

Based on comprehensive testing, here's what each weather model provides:

## Key Findings

**Only GFS provides all critical mountain weather variables!**

### Critical Variables Only Available in GFS:
- ❌ **freezing_level_height** - Only GFS has data
- ❌ **wind_speed_80m** - Only GFS has data  
- ❌ **wind_direction_80m** - Only GFS has data

## Complete Model Capability Matrix

| Variable | ECMWF IFS | GFS | GEM | ICON | ECMWF AIFS |
|----------|-----------|-----|-----|------|------------|
| **Basic Atmospheric** |
| temperature_2m | ✅ | ✅ | ✅ | ✅ | ✅ |
| relative_humidity_2m | ✅ | ✅ | ✅ | ✅ | ✅ |
| dew_point_2m | ✅ | ✅ | ✅ | ✅ | ✅ |
| surface_pressure | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Precipitation** |
| precipitation | ✅ | ✅ | ✅ | ✅ | ✅ |
| snowfall | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Cloud & Upper Air** |
| cloud_cover | ✅ | ✅ | ✅ | ✅ | ✅ |
| temperature_850hPa | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| **Critical Mountain Variables** |
| freezing_level_height | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| **80m Wind (Mountain ridges)** |
| wind_speed_80m | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| wind_direction_80m | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| **10m Wind (Valley floor)** |
| wind_speed_10m | ✅ | ✅ | ✅ | ✅ | ✅ |
| wind_direction_10m | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend:
- ✅ = Available with valid data
- ⚠️ = Variable exists but returns all NaN values
- ❌ = Variable not available

## Implications for Mountain Weather Forecasting

### Why 80m Wind Matters
- **Mountain ridges**: 80m approximates ridge-top winds
- **Avalanche hazard**: Wind loading is critical for snow stability
- **Climbing conditions**: Ridge winds affect safety
- **10m wind insufficient**: Valley winds don't represent mountain conditions

### Recommended Model Strategy

#### Option 1: GFS-Primary Strategy (Current Implementation)
```python
models = ["gfs_seamless", "ecmwf_ifs025", "gem_global", "icon_global"]
```
- **Pros**: Get all critical variables from GFS
- **Cons**: GFS generally less accurate than ECMWF for other variables

#### Option 2: Hybrid Approach (Recommended)
```python
# For basic forecast
models = ["ecmwf_ifs025", "gem_global", "icon_global"]  

# Additional request for GFS-only variables
gfs_variables = ["freezing_level_height", "wind_speed_80m", "wind_direction_80m"]
models_gfs = ["gfs_seamless"]
```

#### Option 3: Wind Height Fallback
When 80m wind isn't available:
1. Use 10m wind and apply terrain adjustment
2. Factor = 1.3-1.5x for ridge exposure
3. Add warning about approximation

## Model-Specific Notes

### ECMWF IFS025
- **Best for**: Temperature, precipitation, general weather
- **Missing**: 80m winds, freezing level
- **Ensemble members**: 51

### GFS Seamless  
- **Best for**: Complete variable coverage
- **Unique**: Only model with 80m winds and freezing level
- **Ensemble members**: 31

### GEM Global
- **Best for**: Canadian terrain, cold weather
- **Missing**: 80m winds, freezing level
- **Ensemble members**: 21

### ICON Global
- **Best for**: European weather patterns
- **Missing**: 80m winds, freezing level, 850hPa temp
- **Ensemble members**: 40

## Recommendations

1. **Always include GFS** for mountain-specific variables
2. **Use ECMWF as primary** for temperature/precipitation accuracy
3. **Document limitations** when 80m wind data unavailable
4. **Consider dual requests** to optimize for both accuracy and completeness

## API Optimization

To minimize latency while getting all data:

```python
# Request 1: High-accuracy models for core variables
params1 = {
    "models": ["ecmwf_ifs025", "gem_global", "icon_global"],
    "hourly": ["temperature_2m", "precipitation", "snowfall", ...]
}

# Request 2: GFS for exclusive variables
params2 = {
    "models": ["gfs_seamless"],
    "hourly": ["freezing_level_height", "wind_speed_80m", "wind_direction_80m"]
}

# Merge results in data processor
```

This ensures we get ECMWF's superior temperature/precipitation forecasts while still capturing critical mountain-specific data from GFS.
