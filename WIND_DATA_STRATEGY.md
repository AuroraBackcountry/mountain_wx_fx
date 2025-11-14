# Wind Data Strategy for Mountain Weather

## The Problem

Our testing revealed that **only GFS provides 80m wind data**, which is critical for mountain weather:
- ECMWF models: Only provide 10m winds
- GFS: Provides both 10m and 80m winds
- Other models: Only provide 10m winds

## Why 80m Wind Matters for Mountains

1. **Ridge Exposure**: 80m approximates ridge-top wind conditions
2. **Avalanche Loading**: Wind transport at ridge height drives snow loading
3. **Climbing Safety**: Ridge winds affect climbing conditions
4. **Valley vs Ridge**: 10m winds represent valley floor, not mountain conditions

## Our Solution: Intelligent Wind Fallback

### Automatic Height Detection
The API now intelligently handles wind data availability:

```python
# Priority order:
1. Use 80m wind if available (from GFS)
2. Fall back to 10m wind with terrain adjustment (from other models)
3. Apply 1.4x factor for ridge exposure when using 10m data
```

### API Response Structure

The simplified response now includes a `wind_height` field to indicate data source:

```json
{
  "wind_speed": {
    "mean": 42.0,
    "min": 28.0,
    "max": 56.0
  },
  "wind_direction": 225.0,
  "wind_height": "80m"  // or "10m_adjusted" or "unavailable"
}
```

### Wind Height Values:
- `"80m"` - Direct measurement from GFS
- `"10m_adjusted"` - 10m wind × 1.4 terrain factor
- `"unavailable"` - No wind data available

## Terrain Adjustment Factor

When using 10m winds, we apply a 1.4x multiplier based on:
- Typical wind speed increase with elevation
- Mountain ridge exposure effects
- Conservative estimate for safety

### Example:
- 10m wind: 20 km/h
- Adjusted ridge estimate: 28 km/h

## Best Practices

1. **Always check `wind_height`** to understand data source
2. **Document limitations** when using adjusted values
3. **Consider additional safety margin** for critical decisions
4. **Use GFS data when available** for most accurate ridge winds

## Model Selection Impact

Our current model mix ensures:
- **GFS always included** for 80m winds and freezing level
- **ECMWF included** for superior temperature/precipitation
- **Fallback mechanism** ensures wind data always available
- **Transparent reporting** of data source

## Future Improvements

1. **Terrain-specific adjustments** based on local topography
2. **Machine learning** to improve 10m→80m conversion
3. **Additional height levels** (e.g., 100m, 120m) as available
4. **Wind gust calculations** for both heights

## Technical Implementation

The fallback logic is implemented in `forecast_api.py`:

```python
# Check 80m first
if wind_80m data exists:
    use wind_80m directly
# Fall back to 10m with adjustment
elif wind_10m data exists:
    apply 1.4x terrain factor
else:
    mark as unavailable
```

This ensures users always get wind data while being transparent about its source and limitations.
