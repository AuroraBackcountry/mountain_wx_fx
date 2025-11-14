"""
Advanced Snow Forecast Formulas
Based on meteorological research for calculating snowfall depth from ensemble forecasts.

Includes:
- Wet-bulb temperature approximation
- Probability of snow vs rain (logistic model)
- Non-linear snow-to-liquid ratio (SLR)
- Humidity and precipitation rate adjustments
"""

import numpy as np
from typing import Optional, Union


class AdvancedSnowFormulas:
    """
    Advanced meteorological formulas for snow forecasting.
    
    Calculates snowfall depth from temperature, humidity, and precipitation
    using physically-based models that account for snow phase probability,
    variable snow density, and environmental factors.
    """
    
    # Default parameters (tunable for different climate regimes)
    PARAMS = {
        # Phase probability (logistic model)
        'alpha': 1.2,          # Steepness of snow/rain transition
        'beta': 0.5,           # 50% snow probability at this wet-bulb temp (°C)
        
        # Snow-to-liquid ratio (Gaussian peak model)
        'r_min': 6.0,          # Dense, wet snow ratio
        'r_max': 18.0,         # Fluffy snow ratio (tune for maritime vs continental)
        't_peak': -12.0,       # Temperature of peak SLR (°C)
        'sigma': 7.0,          # Width of Gaussian (°C)
        
        # Humidity effect
        'gamma': 0.2,          # Max ±20% effect from humidity
        
        # Precipitation rate effect
        'delta': 0.05,         # Rate densification factor
    }
    
    @staticmethod
    def wet_bulb_temperature(temp_c: Union[float, np.ndarray], 
                            rh_pct: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate wet-bulb temperature from air temperature and relative humidity.
        
        This is a well-validated approximation that's accurate within ~0.5°C
        for typical conditions.
        
        Args:
            temp_c: Air temperature in Celsius
            rh_pct: Relative humidity in percent (0-100)
            
        Returns:
            Wet-bulb temperature in Celsius
            
        Formula:
            Tw = T·arctan(0.151977·√(RH+8.313659))
                 + arctan(T+RH)
                 - arctan(RH-1.676331)
                 + 0.00391838·RH^1.5·arctan(0.023101·RH)
                 - 4.686035
        """
        # Convert pandas Series to numpy arrays if needed
        if hasattr(temp_c, 'values'):
            temp_c = temp_c.values
        if hasattr(rh_pct, 'values'):
            rh_pct = rh_pct.values
            
        # Ensure RH is in valid range
        rh = np.clip(rh_pct, 0.0, 100.0)
        
        tw = (temp_c * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
              + np.arctan(temp_c + rh)
              - np.arctan(rh - 1.676331)
              + 0.00391838 * np.power(rh, 1.5) * np.arctan(0.023101 * rh)
              - 4.686035)
        
        return tw
    
    @staticmethod
    def snow_probability(wet_bulb_c: Union[float, np.ndarray],
                        alpha: float = PARAMS['alpha'],
                        beta: float = PARAMS['beta']) -> Union[float, np.ndarray]:
        """
        Calculate probability that precipitation falls as snow (0-1).
        
        Uses logistic function centered on wet-bulb temperature. Around 0-1°C
        the phase is ambiguous; far below that it's almost all snow.
        
        Args:
            wet_bulb_c: Wet-bulb temperature in Celsius
            alpha: Steepness of transition (default: 1.2)
            beta: Center point - 50% snow at this Tw (default: 0.5°C)
            
        Returns:
            Probability of snow (0 = all rain, 1 = all snow)
            
        Formula:
            p_snow = 1 / (1 + exp(α·(Tw - β)))
            
        Examples:
            Tw = -2°C  → p_snow ≈ 0.95 (mostly snow)
            Tw = 0.5°C → p_snow ≈ 0.50 (mixed)
            Tw = 3°C   → p_snow ≈ 0.10 (mostly rain)
        """
        # Convert pandas Series to numpy arrays if needed
        if hasattr(wet_bulb_c, 'values'):
            wet_bulb_c = wet_bulb_c.values
            
        return 1.0 / (1.0 + np.exp(alpha * (wet_bulb_c - beta)))
    
    @staticmethod
    def base_slr(temp_c: Union[float, np.ndarray],
                r_min: float = PARAMS['r_min'],
                r_max: float = PARAMS['r_max'],
                t_peak: float = PARAMS['t_peak'],
                sigma: float = PARAMS['sigma']) -> Union[float, np.ndarray]:
        """
        Calculate base snow-to-liquid ratio from temperature.
        
        Uses Gaussian peak model where SLR is highest at optimal temperature
        (typically -12°C) and decreases for warmer or much colder conditions.
        
        Args:
            temp_c: Air temperature in Celsius
            r_min: Minimum SLR for dense, wet snow (default: 6)
            r_max: Maximum SLR for fluffy snow (default: 18)
            t_peak: Temperature of peak SLR (default: -12°C)
            sigma: Width of Gaussian distribution (default: 7°C)
            
        Returns:
            Snow-to-liquid ratio (dimensionless)
            
        Formula:
            SLR_base = R_min + (R_max - R_min)·exp[-(T - T_peak)²/(2σ²)]
            
        Notes:
            - Maritime climates: use lower r_max (12-15)
            - Continental climates: use higher r_max (18-25)
        """
        # Convert pandas Series to numpy arrays if needed
        if hasattr(temp_c, 'values'):
            temp_c = temp_c.values
            
        return r_min + (r_max - r_min) * np.exp(
            -np.power(temp_c - t_peak, 2) / (2 * np.power(sigma, 2))
        )
    
    @staticmethod
    def humidity_factor(rh_pct: Union[float, np.ndarray],
                       gamma: float = PARAMS['gamma']) -> Union[float, np.ndarray]:
        """
        Calculate humidity adjustment factor for SLR.
        
        Very humid storms produce denser snow (lower SLR).
        Drier air produces fluffier snow (higher SLR).
        
        Args:
            rh_pct: Relative humidity in percent (0-100)
            gamma: Maximum effect magnitude (default: 0.2 for ±20%)
            
        Returns:
            Adjustment factor (0.8 to 1.2)
            
        Formula:
            f_RH = max(0.8, min(1.2, 1 + γ·(50 - RH)/50))
            
        Examples:
            RH = 100% → factor ≈ 0.8  (denser snow)
            RH = 50%  → factor = 1.0  (neutral)
            RH = 20%  → factor ≈ 1.12 (fluffier snow)
        """
        # Convert pandas Series to numpy arrays if needed
        if hasattr(rh_pct, 'values'):
            rh_pct = rh_pct.values
            
        rh = np.clip(rh_pct, 0.0, 100.0)
        factor = 1.0 + gamma * (50.0 - rh) / 50.0
        return np.clip(factor, 0.8, 1.2)
    
    @staticmethod
    def rate_factor(precip_mm: Union[float, np.ndarray],
                   duration_h: Union[float, np.ndarray],
                   delta: float = PARAMS['delta']) -> Union[float, np.ndarray]:
        """
        Calculate precipitation rate adjustment factor.
        
        High precipitation rates produce slightly denser snow due to
        compaction and riming effects.
        
        Args:
            precip_mm: Precipitation amount in mm
            duration_h: Duration in hours
            delta: Rate effect magnitude (default: 0.05)
            
        Returns:
            Adjustment factor (< 1.0, reduces SLR)
            
        Formula:
            R = P / H  [mm/h]
            f_rate = 1 / (1 + δ·R)
            
        Examples:
            R = 1 mm/h → factor ≈ 0.95
            R = 3 mm/h → factor ≈ 0.87
        """
        # Convert pandas Series to numpy arrays if needed
        if hasattr(precip_mm, 'values'):
            precip_mm = precip_mm.values
        if hasattr(duration_h, 'values'):
            duration_h = duration_h.values
            
        # Handle arrays and scalars
        if isinstance(precip_mm, np.ndarray) or isinstance(duration_h, np.ndarray):
            rate = np.divide(precip_mm, duration_h, 
                           where=(duration_h > 0) & (precip_mm > 0),
                           out=np.zeros_like(precip_mm, dtype=float))
        else:
            if duration_h > 0 and precip_mm > 0:
                rate = precip_mm / duration_h
            else:
                rate = 0.0
        
        return 1.0 / (1.0 + delta * rate)
    
    @classmethod
    def calculate_snowfall(cls,
                          temp_c: Union[float, np.ndarray],
                          rh_pct: Union[float, np.ndarray],
                          precip_mm: Union[float, np.ndarray],
                          duration_h: Optional[Union[float, np.ndarray]] = None,
                          **kwargs) -> Union[float, np.ndarray]:
        """
        Calculate snowfall depth using the complete advanced model.
        
        This is the main function that combines all components:
        1. Calculate wet-bulb temperature
        2. Determine snow probability
        3. Calculate base SLR from temperature
        4. Apply humidity adjustment
        5. Apply rate adjustment (if duration provided)
        6. Compute final snowfall depth
        
        Args:
            temp_c: Air temperature in Celsius
            rh_pct: Relative humidity in percent (0-100)
            precip_mm: Liquid-equivalent precipitation in mm
            duration_h: Duration in hours (optional, for rate adjustment)
            **kwargs: Override default parameters (alpha, beta, r_min, r_max, etc.)
            
        Returns:
            Snowfall depth in centimeters
            
        Formula:
            SLR_eff = SLR_base(T) · f_RH · f_rate
            Snowfall_cm = (P · SLR_eff · p_snow) / 10
            
        Example:
            >>> temp = -4.0
            >>> rh = 85.0
            >>> precip = 10.0
            >>> duration = 12.0
            >>> snow_cm = AdvancedSnowFormulas.calculate_snowfall(
            ...     temp, rh, precip, duration
            ... )
            >>> print(f"Expected snowfall: {snow_cm:.1f} cm")
        """
        # Get parameters (use kwargs to override defaults)
        params = {**cls.PARAMS, **kwargs}
        
        # Step 1: Wet-bulb temperature
        tw = cls.wet_bulb_temperature(temp_c, rh_pct)
        
        # Step 2: Snow probability
        p_snow = cls.snow_probability(tw, params['alpha'], params['beta'])
        
        # Step 3: Base SLR
        slr_base = cls.base_slr(temp_c, params['r_min'], params['r_max'],
                               params['t_peak'], params['sigma'])
        
        # Step 4: Humidity factor
        f_rh = cls.humidity_factor(rh_pct, params['gamma'])
        
        # Step 5: Rate factor (if duration provided)
        if duration_h is not None:
            f_rate = cls.rate_factor(precip_mm, duration_h, params['delta'])
        else:
            f_rate = 1.0
        
        # Step 6: Effective SLR and snowfall
        slr_eff = slr_base * f_rh * f_rate
        
        # Convert: mm liquid × SLR → mm snow, then ÷ 10 → cm
        snowfall_cm = (precip_mm * slr_eff * p_snow) / 10.0
        
        # Handle negative or invalid values
        snowfall_cm = np.maximum(snowfall_cm, 0.0)
        
        return snowfall_cm


# Convenience function for quick calculations
def snowfall_cm(temp_c: Union[float, np.ndarray],
               rh_pct: Union[float, np.ndarray],
               precip_mm: Union[float, np.ndarray],
               duration_h: Optional[Union[float, np.ndarray]] = None) -> Union[float, np.ndarray]:
    """
    Quick snowfall calculation with default parameters.
    
    Args:
        temp_c: Air temperature (°C)
        rh_pct: Relative humidity (%)
        precip_mm: Precipitation (mm)
        duration_h: Duration (hours, optional)
        
    Returns:
        Snowfall depth (cm)
    """
    return AdvancedSnowFormulas.calculate_snowfall(temp_c, rh_pct, precip_mm, duration_h)


if __name__ == "__main__":
    # Test cases
    print("Advanced Snow Forecast Formula - Test Cases\n")
    
    # Test 1: Cold, humid storm
    print("Test 1: Cold, humid storm")
    print(f"  T=-4°C, RH=85%, P=10mm, H=12h")
    snow1 = snowfall_cm(-4.0, 85.0, 10.0, 12.0)
    print(f"  → Snowfall: {snow1:.1f} cm\n")
    
    # Test 2: Warmer, very humid
    print("Test 2: Warmer, very humid")
    print(f"  T=-1°C, RH=95%, P=10mm, H=12h")
    snow2 = snowfall_cm(-1.0, 95.0, 10.0, 12.0)
    print(f"  → Snowfall: {snow2:.1f} cm\n")
    
    # Test 3: Optimal conditions
    print("Test 3: Optimal fluffy snow conditions")
    print(f"  T=-12°C, RH=50%, P=5mm, H=6h")
    snow3 = snowfall_cm(-12.0, 50.0, 5.0, 6.0)
    print(f"  → Snowfall: {snow3:.1f} cm\n")
    
    # Test 4: Arrays
    print("Test 4: Array processing")
    temps = np.array([-6, -4, -2, 0, 2])
    rh = np.array([80, 85, 90, 95, 100])
    precip = np.array([5, 10, 15, 10, 5])
    duration = np.array([6, 12, 18, 12, 6])
    
    snow_array = snowfall_cm(temps, rh, precip, duration)
    print(f"  Temps: {temps}")
    print(f"  Snow:  {np.round(snow_array, 1)} cm")
