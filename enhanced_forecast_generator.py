"""
Enhanced Forecast Generator for Mountain Weather
Includes snowfall calculations, proper wind handling, and mountain-specific features
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from statistics_calculator import StatisticsCalculator
from probability_analyzer import ProbabilityAnalyzer
from model_comparison import ModelComparison
from advanced_snow_formulas import AdvancedSnowFormulas


class EnhancedForecastGenerator:
    """Enhanced forecast generator with mountain-specific calculations."""
    
    def __init__(self):
        self.stats_calc = StatisticsCalculator()
        self.prob_analyzer = ProbabilityAnalyzer()
        self.model_comp = ModelComparison()
        self.snow_calc = AdvancedSnowFormulas()
    
    def generate_forecast(self, 
                         data: Dict[str, pd.DataFrame],
                         location: Dict[str, Any],
                         variables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate complete forecast with mountain-specific enhancements."""
        
        # Calculate snowfall for all ensemble members
        self._calculate_ensemble_snowfall(data)
        
        # Generate base forecast
        forecast = {
            'metadata': self._generate_metadata(data, location),
            'summary': {},
            'hourly': [],
            'daily': [],
            'alerts': []
        }
        
        # Process hourly data
        if 'hourly' in data and data['hourly'] is not None:
            forecast['hourly'] = self._process_hourly_enhanced(data['hourly'])
            
        # Process daily data with proper aggregation
        if 'daily' in data and data['daily'] is not None:
            forecast['daily'] = self._process_daily_enhanced(data['daily'], data.get('hourly'))
            
        # Generate enhanced summary
        forecast['summary'] = self._generate_mountain_summary(forecast)
        
        # Add mountain-specific alerts
        forecast['alerts'] = self._generate_mountain_alerts(forecast)
        
        return forecast
    
    def _calculate_ensemble_snowfall(self, data: Dict[str, pd.DataFrame]):
        """Calculate snowfall for all ensemble members using advanced formulas."""
        if 'hourly' not in data:
            return
            
        df = data['hourly']
        
        # Get all member columns
        temp_cols = [c for c in df.columns if 'temperature_2m' in c and 'member' in c]
        rh_cols = [c for c in df.columns if 'relative_humidity_2m' in c and 'member' in c]
        precip_cols = [c for c in df.columns if 'precipitation' in c and 'member' in c]
        
        # Calculate snowfall for each member
        for i, (t_col, rh_col, p_col) in enumerate(zip(temp_cols, rh_cols, precip_cols)):
            model_name = t_col.split('_')[0]  # e.g., 'ecmwf_ifs025'
            member_num = t_col.split('member')[1]
            
            # Calculate snowfall using advanced formulas
            snowfall = self.snow_calc.calculate_snowfall(
                df[t_col].values,
                df[rh_col].values,
                df[p_col].values,
                duration_h=1.0  # Hourly data
            )
            
            # Add to dataframe
            df[f'{model_name}_snowfall_calculated_member{member_num}'] = snowfall
    
    def _process_hourly_enhanced(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process hourly data with enhanced mountain features."""
        hourly_forecast = []
        
        for timestamp in df.index:
            entry = {'time': timestamp.isoformat()}
            
            # Temperature statistics
            temp_stats = self._get_variable_stats(df, 'temperature_2m', timestamp)
            if temp_stats:
                entry['temperature_2m'] = temp_stats
            
            # Precipitation statistics
            precip_stats = self._get_variable_stats(df, 'precipitation', timestamp)
            if precip_stats:
                entry['precipitation'] = precip_stats
            
            # Calculated snowfall statistics
            snow_stats = self._get_variable_stats(df, 'snowfall_calculated', timestamp)
            if snow_stats:
                entry['snowfall'] = snow_stats
                # Also calculate snow level based on temperature
                entry['snow_level'] = self._estimate_snow_level(temp_stats)
            
            # Wind handling with fallback
            wind_data = self._get_wind_data(df, timestamp)
            entry.update(wind_data)
            
            # Freezing level (only from GFS)
            fl_stats = self._get_variable_stats(df, 'freezing_level_height', timestamp)
            if fl_stats and fl_stats['mean'] > 0:
                entry['freezing_level_height'] = fl_stats['mean']
            else:
                # Estimate from temperature if not available
                entry['freezing_level_height'] = self._estimate_freezing_level(df, timestamp)
            
            # Calculate probabilities
            entry['probabilities'] = self._calculate_probabilities(df, timestamp)
            
            hourly_forecast.append(entry)
        
        return hourly_forecast
    
    def _get_variable_stats(self, df: pd.DataFrame, var_name: str, 
                           timestamp: pd.Timestamp) -> Optional[Dict[str, float]]:
        """Get statistics for a variable, handling missing data gracefully."""
        cols = [c for c in df.columns if var_name in c and 'member' in c]
        if not cols:
            return None
            
        # Get values at this timestamp
        values = df.loc[timestamp, cols].values
        
        # Filter out NaN values
        valid_values = values[~np.isnan(values)]
        if len(valid_values) == 0:
            return None
            
        return {
            'mean': round(float(np.mean(valid_values)), 1),
            'min': round(float(np.min(valid_values)), 1),
            'max': round(float(np.max(valid_values)), 1),
            'std': round(float(np.std(valid_values)), 1),
            'median': round(float(np.median(valid_values)), 1)
        }
    
    def _get_wind_data(self, df: pd.DataFrame, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Get wind data with intelligent fallback."""
        result = {}
        
        # Try 80m first
        wind_80m = self._get_variable_stats(df, 'wind_speed_80m', timestamp)
        wind_dir_80m = self._get_variable_stats(df, 'wind_direction_80m', timestamp)
        
        if wind_80m and wind_80m['mean'] > 0:
            result['wind_speed'] = wind_80m
            result['wind_height'] = '80m'
            if wind_dir_80m and wind_dir_80m['mean'] >= 0:
                result['wind_direction'] = round(wind_dir_80m['mean'])
            else:
                result['wind_direction'] = 'N/A'
        else:
            # Fall back to 10m with adjustment
            wind_10m = self._get_variable_stats(df, 'wind_speed_10m', timestamp)
            wind_dir_10m = self._get_variable_stats(df, 'wind_direction_10m', timestamp)
            
            if wind_10m:
                # Apply terrain factor
                for key in ['mean', 'min', 'max']:
                    wind_10m[key] = round(wind_10m[key] * 1.4, 1)
                result['wind_speed'] = wind_10m
                result['wind_height'] = '10m_adjusted'
                
                if wind_dir_10m and wind_dir_10m['mean'] >= 0:
                    result['wind_direction'] = round(wind_dir_10m['mean'])
                else:
                    result['wind_direction'] = 'Variable'
            else:
                result['wind_speed'] = {'mean': 0, 'min': 0, 'max': 0}
                result['wind_direction'] = 'N/A'
                result['wind_height'] = 'unavailable'
        
        return result
    
    def _estimate_snow_level(self, temp_stats: Dict[str, float]) -> float:
        """Estimate snow level from temperature using standard lapse rate."""
        if not temp_stats:
            return 0
            
        # Assume station elevation (you should pass this in location data)
        station_elevation = 920  # meters (example for Whistler)
        
        # Use mean temperature and standard lapse rate
        temp = temp_stats['mean']
        if temp <= 0:
            return station_elevation
        
        # Snow level approximately 300m above freezing level
        freezing_elevation = station_elevation + (temp / 0.0065)
        snow_level = max(station_elevation, freezing_elevation - 300)
        
        return round(snow_level)
    
    def _estimate_freezing_level(self, df: pd.DataFrame, timestamp: pd.Timestamp) -> float:
        """Estimate freezing level from temperature profile."""
        # Get surface temperature
        temp_stats = self._get_variable_stats(df, 'temperature_2m', timestamp)
        if not temp_stats:
            return 'N/A'
            
        temp_surface = temp_stats['mean']
        
        # Get 850hPa temperature if available
        temp_850 = self._get_variable_stats(df, 'temperature_850hPa', timestamp)
        
        if temp_850:
            # Use both levels to estimate
            # Approximate 850hPa height as 1500m
            height_850 = 1500
            temp_diff = temp_surface - temp_850['mean']
            lapse_rate = temp_diff / height_850 if height_850 > 0 else 0.0065
            
            if temp_surface <= 0:
                return 0  # Already below freezing at surface
            
            freezing_height = temp_surface / lapse_rate
        else:
            # Use standard lapse rate
            if temp_surface <= 0:
                return 0
            freezing_height = temp_surface / 0.0065
            
        return round(freezing_height)
    
    def _calculate_probabilities(self, df: pd.DataFrame, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Calculate comprehensive probabilities."""
        probs = {}
        
        # Precipitation probabilities
        precip_cols = [c for c in df.columns if 'precipitation' in c and 'member' in c]
        if precip_cols:
            values = df.loc[timestamp, precip_cols].values
            valid = values[~np.isnan(values)]
            if len(valid) > 0:
                probs['precipitation'] = {
                    'any': round(float(np.mean(valid > 0.1)), 2),
                    'moderate': round(float(np.mean(valid > 2.5)), 2),
                    'heavy': round(float(np.mean(valid > 10)), 2)
                }
        
        # Snow probabilities
        snow_cols = [c for c in df.columns if 'snowfall_calculated' in c and 'member' in c]
        if snow_cols:
            values = df.loc[timestamp, snow_cols].values
            valid = values[~np.isnan(values)]
            if len(valid) > 0:
                probs['snow'] = {
                    'any': round(float(np.mean(valid > 0.1)), 2),
                    'moderate': round(float(np.mean(valid > 5)), 2),
                    'heavy': round(float(np.mean(valid > 15)), 2)
                }
        
        # Wind probabilities
        wind_cols = [c for c in df.columns if 'wind_speed' in c and 'member' in c]
        if wind_cols:
            values = df.loc[timestamp, wind_cols].values
            valid = values[~np.isnan(values)]
            if len(valid) > 0:
                # Adjust thresholds if using 10m winds
                factor = 1.4 if '10m' in wind_cols[0] else 1.0
                probs['strong_winds'] = {
                    'moderate': round(float(np.mean(valid * factor > 40)), 2),
                    'strong': round(float(np.mean(valid * factor > 60)), 2),
                    'extreme': round(float(np.mean(valid * factor > 80)), 2)
                }
        
        return probs
    
    def _process_daily_enhanced(self, daily_df: pd.DataFrame, 
                               hourly_df: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
        """Process daily data with proper aggregation from hourly."""
        daily_forecast = []
        
        for date in daily_df.index:
            entry = {
                'date': date.strftime('%Y-%m-%d'),
                'day_of_week': date.strftime('%A')
            }
            
            # Temperature from daily data
            temp_min = self._get_daily_value(daily_df, date, 'temperature_2m_min')
            temp_max = self._get_daily_value(daily_df, date, 'temperature_2m_max')
            temp_mean = self._get_daily_value(daily_df, date, 'temperature_2m_mean')
            
            entry['temperature'] = {
                'min': round(temp_min, 1) if temp_min is not None else 'N/A',
                'max': round(temp_max, 1) if temp_max is not None else 'N/A',
                'mean': round(temp_mean, 1) if temp_mean is not None else 'N/A'
            }
            
            # Precipitation from daily data
            precip_sum = self._get_daily_value(daily_df, date, 'precipitation_sum')
            entry['precipitation_total'] = round(precip_sum, 1) if precip_sum is not None else 0
            
            # Calculate snowfall from hourly if available
            if hourly_df is not None:
                snow_total = self._aggregate_daily_snow(hourly_df, date)
                entry['snowfall'] = {
                    'total': round(snow_total['total'], 1),
                    'max_hourly': round(snow_total['max_hourly'], 1)
                }
            else:
                entry['snowfall'] = {'total': 0, 'max_hourly': 0}
            
            # Wind aggregation from daily or hourly
            entry['wind'] = self._get_daily_wind(daily_df, hourly_df, date)
            
            # Freezing level - aggregate from hourly if available
            if hourly_df is not None:
                fl_daily = self._aggregate_daily_freezing_level(hourly_df, date)
                entry['freezing_level'] = round(fl_daily) if fl_daily > 0 else 'N/A'
            else:
                entry['freezing_level'] = 'N/A'
            
            # Generate appropriate summary
            entry['summary'] = self._generate_daily_summary(entry)
            
            daily_forecast.append(entry)
        
        return daily_forecast
    
    def _get_daily_value(self, df: pd.DataFrame, date: pd.Timestamp, 
                        var_name: str) -> Optional[float]:
        """Get aggregated daily value across ensemble members."""
        cols = [c for c in df.columns if var_name in c and 'member' in c]
        if not cols:
            return None
            
        values = df.loc[date, cols].values
        valid = values[~np.isnan(values)]
        
        return float(np.mean(valid)) if len(valid) > 0 else None
    
    def _aggregate_daily_snow(self, hourly_df: pd.DataFrame, date: datetime.date) -> Dict[str, float]:
        """Aggregate snowfall for a specific day from hourly data."""
        # Filter hourly data for this date
        mask = hourly_df.index.date == date
        day_data = hourly_df[mask]
        
        if day_data.empty:
            return {'total': 0, 'max_hourly': 0}
        
        snow_cols = [c for c in day_data.columns if 'snowfall_calculated' in c and 'member' in c]
        if not snow_cols:
            return {'total': 0, 'max_hourly': 0}
        
        # Calculate total and max for each member, then average
        totals = []
        max_hourlys = []
        
        for col in snow_cols:
            member_data = day_data[col].values
            valid = member_data[~np.isnan(member_data)]
            if len(valid) > 0:
                totals.append(np.sum(valid))
                max_hourlys.append(np.max(valid))
        
        return {
            'total': float(np.mean(totals)) if totals else 0,
            'max_hourly': float(np.mean(max_hourlys)) if max_hourlys else 0
        }
    
    def _get_daily_wind(self, daily_df: pd.DataFrame, hourly_df: Optional[pd.DataFrame],
                       date: datetime.date) -> Dict[str, Any]:
        """Get daily wind data with proper aggregation."""
        # Try daily aggregates first
        wind_speed = self._get_daily_value(daily_df, date, 'wind_speed_10m_mean')
        wind_dir = self._get_daily_value(daily_df, date, 'wind_direction_10m_dominant')
        
        if wind_speed is not None and wind_speed > 0:
            return {
                'speed': round(wind_speed * 1.4, 1),  # Terrain adjustment
                'direction': round(wind_dir) if wind_dir is not None else 'Variable',
                'height': '10m_adjusted'
            }
        
        # Fall back to hourly aggregation
        if hourly_df is not None:
            mask = hourly_df.index.date == date
            day_data = hourly_df[mask]
            
            if not day_data.empty:
                # Try 80m first
                wind_80m_cols = [c for c in day_data.columns if 'wind_speed_80m' in c and 'member' in c]
                if wind_80m_cols:
                    max_winds = []
                    for col in wind_80m_cols:
                        valid = day_data[col].values[~np.isnan(day_data[col].values)]
                        if len(valid) > 0:
                            max_winds.append(np.max(valid))
                    
                    if max_winds:
                        return {
                            'speed': round(float(np.mean(max_winds)), 1),
                            'direction': 'Variable',
                            'height': '80m'
                        }
        
        return {
            'speed': 0,
            'direction': 'N/A',
            'height': 'unavailable'
        }
    
    def _aggregate_daily_freezing_level(self, hourly_df: pd.DataFrame, date: datetime.date) -> float:
        """Aggregate freezing level for a day."""
        mask = hourly_df.index.date == date
        day_data = hourly_df[mask]
        
        if day_data.empty:
            return 0
        
        fl_cols = [c for c in day_data.columns if 'freezing_level_height' in c and 'member' in c]
        if fl_cols:
            all_values = []
            for col in fl_cols:
                valid = day_data[col].values[~np.isnan(day_data[col].values)]
                if len(valid) > 0:
                    all_values.extend(valid)
            
            if all_values:
                return float(np.mean(all_values))
        
        # Estimate from temperature if not available
        temp_cols = [c for c in day_data.columns if 'temperature_2m' in c and 'member' in c]
        if temp_cols:
            max_temps = []
            for col in temp_cols:
                valid = day_data[col].values[~np.isnan(day_data[col].values)]
                if len(valid) > 0:
                    max_temps.append(np.max(valid))
            
            if max_temps:
                max_temp = np.mean(max_temps)
                if max_temp > 0:
                    return max_temp / 0.0065  # Standard lapse rate
        
        return 0
    
    def _generate_daily_summary(self, day_data: Dict[str, Any]) -> str:
        """Generate appropriate daily summary based on conditions."""
        temp_min = day_data['temperature']['min']
        temp_max = day_data['temperature']['max']
        precip = day_data['precipitation_total']
        snow = day_data['snowfall']['total']
        
        # Temperature summary
        temp_str = f"Temps {temp_min} to {temp_max}°C. "
        
        # Precipitation type and amount
        if precip < 0.1:
            precip_str = "Dry conditions expected."
        else:
            if temp_max < 2 or snow > 0.1:
                if snow > 20:
                    precip_str = f"Heavy snow expected ({snow:.0f}cm)."
                elif snow > 5:
                    precip_str = f"Moderate snow expected ({snow:.0f}cm)."
                else:
                    precip_str = "Light snow expected."
            else:
                if precip > 25:
                    precip_str = "Heavy rain expected."
                elif precip > 10:
                    precip_str = "Moderate rain expected."
                else:
                    precip_str = "Light rain expected."
        
        return temp_str + precip_str
    
    def _generate_mountain_summary(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mountain-specific summary."""
        summary = {
            'executive_summary': '',
            'key_concerns': [],
            'operational_conditions': {
                'rating': 'UNKNOWN',
                'rationale': ''
            }
        }
        
        # Analyze conditions
        concerns = []
        hourly = forecast.get('hourly', [])
        daily = forecast.get('daily', [])
        
        if hourly:
            # Check for heavy snow
            max_snow = max([h.get('snowfall', {}).get('max', 0) for h in hourly[:24]], default=0)
            if max_snow > 5:
                concerns.append('Heavy snowfall')
            
            # Check winds
            max_wind = max([h.get('wind_speed', {}).get('max', 0) for h in hourly[:24]], default=0)
            if max_wind > 60:
                concerns.append('Strong winds')
            
            # Check visibility (based on snow and wind)
            if max_snow > 2 and max_wind > 40:
                concerns.append('Poor visibility likely')
        
        # Determine rating
        if len(concerns) >= 2:
            rating = 'POOR'
            rationale = 'Multiple hazardous conditions'
        elif len(concerns) == 1:
            rating = 'FAIR'
            rationale = 'Some challenging conditions'
        else:
            rating = 'GOOD'
            rationale = 'Generally favorable conditions'
        
        # Build executive summary
        if daily:
            temp_range = f"{daily[0]['temperature']['min']} to {daily[0]['temperature']['max']}°C"
            snow_total = sum([d['snowfall']['total'] for d in daily[:3]])
            
            if snow_total > 30:
                summary['executive_summary'] = f"Temps {temp_range}. Significant snow accumulation ({snow_total:.0f}cm over 3 days)."
            elif snow_total > 5:
                summary['executive_summary'] = f"Temps {temp_range}. Moderate snow expected ({snow_total:.0f}cm total)."
            else:
                precip_total = sum([d['precipitation_total'] for d in daily[:3]])
                if precip_total > 10:
                    summary['executive_summary'] = f"Temps {temp_range}. Wet conditions expected."
                else:
                    summary['executive_summary'] = f"Temps {temp_range}. Generally dry conditions."
        
        summary['key_concerns'] = concerns
        summary['operational_conditions']['rating'] = rating
        summary['operational_conditions']['rationale'] = rationale
        
        return summary
    
    def _generate_mountain_alerts(self, forecast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mountain-specific weather alerts."""
        alerts = []
        hourly = forecast.get('hourly', [])
        
        if not hourly:
            return alerts
        
        # Snow accumulation alert
        next_24h_snow = sum([h.get('snowfall', {}).get('mean', 0) for h in hourly[:24]])
        if next_24h_snow > 30:
            alerts.append({
                'type': 'HEAVY_SNOW',
                'severity': 'HIGH',
                'message': f'Heavy snow warning: {next_24h_snow:.0f}cm expected in next 24 hours',
                'valid_from': hourly[0]['time'],
                'valid_to': hourly[23]['time'] if len(hourly) >= 24 else hourly[-1]['time']
            })
        
        # Wind alert
        max_wind_24h = max([h.get('wind_speed', {}).get('max', 0) for h in hourly[:24]], default=0)
        if max_wind_24h > 80:
            alerts.append({
                'type': 'HIGH_WIND',
                'severity': 'HIGH',
                'message': f'High wind warning: Gusts to {max_wind_24h:.0f} km/h expected',
                'valid_from': hourly[0]['time'],
                'valid_to': hourly[23]['time'] if len(hourly) >= 24 else hourly[-1]['time']
            })
        
        # Freezing level change alert
        if len(hourly) >= 24:
            fl_start = hourly[0].get('freezing_level_height', 0)
            fl_end = hourly[23].get('freezing_level_height', 0)
            
            if isinstance(fl_start, (int, float)) and isinstance(fl_end, (int, float)):
                fl_change = fl_end - fl_start
                if abs(fl_change) > 500:
                    alerts.append({
                        'type': 'FREEZING_LEVEL_CHANGE',
                        'severity': 'MODERATE',
                        'message': f'Significant freezing level {"rise" if fl_change > 0 else "drop"}: {abs(fl_change):.0f}m change',
                        'valid_from': hourly[0]['time'],
                        'valid_to': hourly[23]['time']
                    })
        
        return alerts
    
    def _generate_metadata(self, data: Dict[str, pd.DataFrame], 
                          location: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced metadata."""
        df = data.get('hourly', data.get('daily'))
        if df is None or df.empty:
            raise ValueError("No data available")
        
        # Identify models
        models = set()
        for col in df.columns:
            if '_member' in col:
                model = col.split('_')[0]
                if model not in ['snowfall', 'wind']:  # Skip calculated columns
                    models.add(model.upper())
        
        # Count ensemble members
        member_counts = []
        for model in models:
            model_lower = model.lower()
            cols = [c for c in df.columns if model_lower in c and 'member' in c and 'temperature' in c]
            if cols:
                member_counts.append(len(cols))
        
        return {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'location': location,
            'forecast_start': df.index[0].isoformat() if hasattr(df.index[0], 'isoformat') else str(df.index[0]),
            'forecast_end': df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1]),
            'models': sorted(list(models)),
            'ensemble_members': sum(member_counts),
            'data_source': 'Open-Meteo.com',
            'attribution': 'Weather data by Open-Meteo.com',
            'forecast_type': 'ensemble',
            'calculations_included': ['snowfall', 'wind_adjustment', 'freezing_level_estimation']
        }
    
    def to_json(self, forecast: Dict[str, Any], pretty: bool = False) -> str:
        """Convert forecast to JSON string."""
        if pretty:
            return json.dumps(forecast, indent=2, default=str)
        return json.dumps(forecast, default=str)
