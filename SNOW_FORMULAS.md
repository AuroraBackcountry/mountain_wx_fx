# Advanced Snow Forecast Formulas

Physically-based meteorological formulas for calculating snowfall depth from temperature, humidity, and precipitation data. These formulas account for snow phase probability, variable snow density, and environmental factors.

## Overview

This model improves on simple snow-to-liquid ratio (SLR) approaches by:
- Using **wet-bulb temperature** to determine snow vs rain probability
- Applying a **non-linear SLR** that peaks at optimal temperatures
- Adjusting for **humidity effects** on snow density
- Adjusting for **precipitation rate effects** on compaction

## Quick Usage

```python
from advanced_snow_formulas import snowfall_cm

# Simple calculation
snow_depth = snowfall_cm(
    temp_c=-4.0,      # Temperature in Celsius
    rh_pct=85.0,      # Relative humidity (%)
    precip_mm=10.0,   # Precipitation in mm
    duration_h=12.0   # Duration in hours (optional)
)

print(f"Expected snowfall: {snow_depth:.1f} cm")
# Output: Expected snowfall: 10.1 cm
```

## Formula Components

### 1. Wet-Bulb Temperature (Tw)

Approximates the wet-bulb temperature from air temperature and relative humidity. This is more accurate than dry-bulb temperature for determining precipitation phase.

**Formula:**
```
Tw = T·arctan(0.151977·√(RH+8.313659))
     + arctan(T+RH)
     - arctan(RH-1.676331)
     + 0.00391838·RH^1.5·arctan(0.023101·RH)
     - 4.686035
```

**Accuracy:** Within ~0.5°C for typical conditions

---

### 2. Snow Probability (p_snow)

Determines the probability that precipitation falls as snow (0-1) using a logistic function based on wet-bulb temperature.

**Formula:**
```
p_snow = 1 / (1 + exp(α·(Tw - β)))
```

**Default Parameters:**
- α = 1.2 (steepness of transition)
- β = 0.5°C (50% snow at this wet-bulb temp)

**Examples:**
| Wet-Bulb Temp | p_snow | Interpretation |
|---------------|--------|----------------|
| -2°C          | 0.95   | Mostly snow    |
| 0.5°C         | 0.50   | Mixed          |
| 3°C           | 0.10   | Mostly rain    |

---

### 3. Base Snow-to-Liquid Ratio (SLR)

Uses a Gaussian peak model where SLR is highest at an optimal temperature (typically -12°C for mountain snowpacks).

**Formula:**
```
SLR_base = R_min + (R_max - R_min)·exp[-(T - T_peak)²/(2σ²)]
```

**Default Parameters:**
- R_min = 6 (dense, wet snow)
- R_max = 18 (fluffy snow)
- T_peak = -12°C (optimal temperature)
- σ = 7°C (width of distribution)

**Tuning Guide:**
- **Maritime climates:** R_max = 12-15 (wetter, denser snow)
- **Continental climates:** R_max = 18-25 (drier, fluffier snow)

---

### 4. Humidity Factor (f_RH)

Adjusts SLR based on relative humidity. Very humid storms produce denser snow.

**Formula:**
```
f_RH = max(0.8, min(1.2, 1 + γ·(50 - RH)/50))
```

**Default Parameters:**
- γ = 0.2 (±20% maximum effect)

**Examples:**
| RH    | Factor | Effect         |
|-------|--------|----------------|
| 100%  | 0.8    | Denser snow    |
| 50%   | 1.0    | Neutral        |
| 20%   | 1.12   | Fluffier snow  |

---

### 5. Rate Factor (f_rate)

Adjusts SLR based on precipitation rate. High rates cause slight densification.

**Formula:**
```
R = P / H  [mm/h]
f_rate = 1 / (1 + δ·R)
```

**Default Parameters:**
- δ = 0.05

**Examples:**
| Rate     | Factor | Effect              |
|----------|--------|---------------------|
| 1 mm/h   | 0.95   | Slight densification|
| 3 mm/h   | 0.87   | Moderate densification|

---

### 6. Final Snowfall Calculation

Combines all factors to compute snowfall depth.

**Formula:**
```
SLR_eff = SLR_base(T) · f_RH · f_rate
Snowfall_cm = (P · SLR_eff · p_snow) / 10
```

Where:
- P = precipitation in mm (liquid equivalent)
- Result is in centimeters of snow

---

## Advanced Usage

### Custom Parameters

You can override default parameters for different climate regimes:

```python
from advanced_snow_formulas import AdvancedSnowFormulas

# Maritime climate with denser snow
snow = AdvancedSnowFormulas.calculate_snowfall(
    temp_c=-6.0,
    rh_pct=90.0,
    precip_mm=15.0,
    duration_h=12.0,
    r_max=12.0,      # Lower max SLR
    r_min=5.0,       # Lower min SLR
    t_peak=-10.0     # Warmer optimal temp
)
```

### Array Processing

Process multiple timesteps at once using NumPy arrays:

```python
import numpy as np

temps = np.array([-6, -4, -2, 0, 2])
rh = np.array([80, 85, 90, 95, 100])
precip = np.array([5, 10, 15, 10, 5])
duration = np.array([6, 12, 18, 12, 6])

snow_array = snowfall_cm(temps, rh, precip, duration)
# Result: array([ 6.0, 10.1, 12.3,  5.4,  0.5])
```

### Individual Components

Access individual formula components:

```python
from advanced_snow_formulas import AdvancedSnowFormulas as ASF

# Calculate just wet-bulb temperature
tw = ASF.wet_bulb_temperature(temp_c=-4.0, rh_pct=85.0)

# Calculate just snow probability
p_snow = ASF.snow_probability(wet_bulb_c=0.5)

# Calculate just base SLR
slr = ASF.base_slr(temp_c=-12.0)

# Calculate humidity adjustment
f_rh = ASF.humidity_factor(rh_pct=85.0)

# Calculate rate adjustment
f_rate = ASF.rate_factor(precip_mm=10.0, duration_h=12.0)
```

---

## Integration with Ensemble Forecasts

Use with your ensemble forecast data:

```python
import pandas as pd
from advanced_snow_formulas import snowfall_cm

# Assuming you have ensemble DataFrames from Open-Meteo
hourly_df = data['hourly']

# Get temperature columns for all ensemble members
temp_cols = [col for col in hourly_df.columns if 'temperature_2m' in col and 'member' in col]
rh_cols = [col for col in hourly_df.columns if 'relative_humidity' in col and 'member' in col]
precip_cols = [col for col in hourly_df.columns if 'precipitation' in col and 'member' in col]

# Calculate snowfall for each ensemble member
for i, (t_col, rh_col, p_col) in enumerate(zip(temp_cols, rh_cols, precip_cols)):
    hourly_df[f'snowfall_member{i}'] = snowfall_cm(
        hourly_df[t_col],
        hourly_df[rh_col],
        hourly_df[p_col],
        duration_h=1.0  # Hourly data
    )

# Then calculate ensemble statistics
snow_mean = hourly_df[[col for col in hourly_df.columns if 'snowfall_member' in col]].mean(axis=1)
snow_max = hourly_df[[col for col in hourly_df.columns if 'snowfall_member' in col]].max(axis=1)
```

---

## Validation & Tuning

### Test Cases

| Conditions | Expected Result |
|------------|-----------------|
| T=-4°C, RH=85%, P=10mm, H=12h | ~10-12 cm |
| T=-1°C, RH=95%, P=10mm, H=12h | ~7-9 cm |
| T=-12°C, RH=50%, P=5mm, H=6h | ~8-9 cm (fluffy) |

### Regional Tuning

**For Maritime Climates (Coastal mountains):**
```python
snow = snowfall_cm(temp, rh, precip, duration,
    r_max=12.0,     # Wetter, denser snow
    t_peak=-10.0,   # Warmer optimal temp
    gamma=0.25      # Stronger humidity effect
)
```

**For Continental Climates (Interior mountains):**
```python
snow = snowfall_cm(temp, rh, precip, duration,
    r_max=22.0,     # Drier, fluffier snow
    t_peak=-14.0,   # Colder optimal temp
    gamma=0.15      # Weaker humidity effect
)
```

**For Arctic Conditions:**
```python
snow = snowfall_cm(temp, rh, precip, duration,
    r_max=25.0,     # Very fluffy snow
    t_peak=-18.0,   # Very cold optimal temp
    beta=-1.0       # Snow at colder wet-bulb
)
```

---

## References

- **Wet-bulb approximation:** Stull (2011) "Wet-Bulb Temperature from Relative Humidity and Air Temperature"
- **Snow phase:** Marks et al. (2013) "An Atmospheric-Energy-Balance Model for Snowmelt"
- **SLR variability:** Roebber et al. (2003) "Improving Snowfall Forecasting by Accounting for Snow Density"
- **Humidity effects:** Judson & Doesken (2000) "Density of Freshly Fallen Snow in the Central Rocky Mountains"

---

## PostgreSQL Implementation

If you need the same formulas in PostgreSQL (for database calculations), see the included SQL function in the original documentation.

---

## License & Attribution

These formulas are based on published meteorological research. When using in academic or professional work, please cite the relevant references above.
