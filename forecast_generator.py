"""
Forecast Generator for Ensemble Weather Forecasts
Produces structured JSON forecasts from ensemble data.
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from statistics_calculator import StatisticsCalculator
from probability_analyzer import ProbabilityAnalyzer
from model_comparison import ModelComparison


class ForecastGenerator:
    """Generate structured JSON forecasts from ensemble data."""
    
    def __init__(self):
        self.stats_calc = StatisticsCalculator()
        self.prob_analyzer = ProbabilityAnalyzer()
        self.model_comp = ModelComparison()
    
    def generate_forecast(self, 
                         data: Dict[str, pd.DataFrame],
                         location: Dict[str, Any],
                         variables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate complete forecast from ensemble data.
        
        Args:
            data: Dictionary with 'hourly' and/or 'daily' DataFrames
            location: Dictionary with location info (lat, lon, name)
            variables: List of variables to process (or None for defaults)
            
        Returns:
            Complete forecast dictionary
        """
        if variables is None:
            variables = ['temperature_2m', 'precipitation', 'wind_speed_80m', 
                        'wind_direction_80m', 'wind_speed_10m', 'wind_direction_10m',
                        'freezing_level_height', 'snowfall']
        
        forecast = {
            'metadata': self._generate_metadata(data, location),
            'summary': {},
            'hourly': [],
            'daily': [],
            'model_comparison': []
        }
        
        # Process hourly data
        if 'hourly' in data and data['hourly'] is not None:
            forecast['hourly'] = self._process_hourly(data['hourly'], variables)
        
        # Process daily data
        if 'daily' in data and data['daily'] is not None:
            forecast['daily'] = self._process_daily(data['daily'], variables)
        
        # Generate model comparisons
        df = data.get('hourly')
        if df is None:
            df = data.get('daily')
        if df is not None:
            forecast['model_comparison'] = self._generate_model_comparison(df, variables)
        
        # Generate summary
        forecast['summary'] = self._generate_summary(forecast)
        
        return forecast
    
    def _generate_metadata(self, data: Dict[str, pd.DataFrame], 
                          location: Dict[str, Any]) -> Dict[str, Any]:
        """Generate forecast metadata."""
        # Get dataframe for time info
        df = data.get('hourly')
        if df is None:
            df = data.get('daily')
        
        if df is None or df.empty:
            raise ValueError("No data available")
        
        # Identify models
        models = self._identify_models(df)
        
        # Count ensemble members
        member_count = self._count_ensemble_members(df)
        
        return {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'location': location,
            'forecast_start': df.index[0].isoformat(),
            'forecast_end': df.index[-1].isoformat(),
            'models': models,
            'ensemble_members': member_count
        }
    
    def _process_hourly(self, df: pd.DataFrame, 
                       variables: List[str]) -> List[Dict[str, Any]]:
        """Process hourly data into forecast entries."""
        hourly_forecast = []
        
        for timestamp in df.index:
            entry = {'time': timestamp.isoformat()}
            
            for var in variables:
                # Check if variable exists in data
                cols = [col for col in df.columns if var in col and 'member' in col]
                if not cols:
                    continue
                
                # Calculate statistics
                stats_df = self.stats_calc.calculate_statistics(df, var)
                stats = self.stats_calc.get_statistics_dict(stats_df, var, timestamp)
                
                # Add trend
                trend_series = self.stats_calc.calculate_trend(stats_df['mean'])
                idx = df.index.get_loc(timestamp)
                stats['trend'] = trend_series[idx]
                
                entry[var] = stats
            
            # Calculate probabilities
            if 'precipitation' in [col for col in df.columns if 'member' in col]:
                precip_probs = self.prob_analyzer.calculate_precipitation_probabilities(df)
                entry['probabilities'] = {
                    'precipitation': {
                        'measurable': float(precip_probs.loc[timestamp, 'p_measurable']),
                        'heavy': float(precip_probs.loc[timestamp, 'p_heavy'])
                    }
                }
            
            if 'temperature_2m' in [col for col in df.columns if 'member' in col]:
                temp_probs = self.prob_analyzer.calculate_temperature_probabilities(df)
                if 'probabilities' not in entry:
                    entry['probabilities'] = {}
                entry['probabilities']['freezing'] = float(temp_probs.loc[timestamp, 'p_freezing'])
            
            if 'wind' in str(df.columns):
                wind_probs = self.prob_analyzer.calculate_wind_probabilities(df)
                if 'probabilities' not in entry:
                    entry['probabilities'] = {}
                entry['probabilities']['strong_winds'] = float(wind_probs.loc[timestamp, 'p_windy'])
            
            hourly_forecast.append(entry)
        
        return hourly_forecast
    
    def _process_daily(self, df: pd.DataFrame,
                      variables: List[str]) -> List[Dict[str, Any]]:
        """Process daily data into forecast entries."""
        daily_forecast = []
        
        for timestamp in df.index:
            entry = {
                'date': timestamp.date().isoformat(),
                'day_of_week': timestamp.strftime('%A')
            }
            
            for var in variables:
                # Check if variable exists
                cols = [col for col in df.columns if var in col and 'member' in col]
                if not cols:
                    continue
                
                # Calculate statistics
                stats_df = self.stats_calc.calculate_statistics(df, var)
                stats = self.stats_calc.get_statistics_dict(stats_df, var, timestamp)
                
                entry[var] = stats
            
            # Generate daily summary
            entry['summary'] = self._generate_daily_summary(entry)
            
            daily_forecast.append(entry)
        
        return daily_forecast
    
    def _generate_model_comparison(self, df: pd.DataFrame,
                                   variables: List[str]) -> List[Dict[str, Any]]:
        """Generate model comparison results."""
        comparisons = []
        
        for var in variables:
            # Check if variable exists
            cols = [col for col in df.columns if var in col and 'member' in col]
            if not cols:
                continue
            
            try:
                # Compare models
                comparison_df, model_means = self.model_comp.compare_models(df, var)
                outliers = self.model_comp.identify_outliers(model_means)
                
                # Get first timestamp as example
                timestamp = df.index[0]
                comp_dict = self.model_comp.get_comparison_dict(
                    comparison_df, model_means, outliers, var, timestamp
                )
                
                comparisons.append(comp_dict)
            except ValueError:
                # Not enough models for comparison
                continue
        
        return comparisons
    
    def _generate_summary(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary."""
        summary = {
            'executive_summary': '',
            'key_concerns': [],
            'operational_conditions': {}
        }
        
        # Get first day data for summary
        if forecast.get('daily') and len(forecast['daily']) > 0:
            first_day = forecast['daily'][0]
            
            # Generate text summary
            summary['executive_summary'] = self._generate_executive_summary(first_day)
            
            # Identify concerns
            summary['key_concerns'] = self._identify_concerns(first_day)
            
            # Rate conditions
            summary['operational_conditions'] = self._rate_operational_conditions(first_day)
        
        return summary
    
    def _generate_executive_summary(self, day_data: Dict[str, Any]) -> str:
        """Generate brief text summary for a day."""
        parts = []
        
        # Temperature
        if 'temperature_2m' in day_data:
            temp = day_data['temperature_2m']
            parts.append(f"Temps {temp['min']:.0f} to {temp['max']:.0f}°C")
        
        # Precipitation
        if 'precipitation' in day_data:
            precip = day_data['precipitation']
            if precip['mean'] > 10:
                parts.append("Heavy rain expected")
            elif precip['mean'] > 2:
                parts.append("Rain expected")
        
        # Wind
        if 'wind_speed_80m' in day_data:
            wind = day_data['wind_speed_80m']
            if wind['mean'] > 40:
                parts.append("Strong winds")
        
        return ". ".join(parts) + "." if parts else "Conditions variable."
    
    def _identify_concerns(self, day_data: Dict[str, Any]) -> List[str]:
        """Identify key concerns for the day."""
        concerns = []
        
        if 'temperature_2m' in day_data:
            temp = day_data['temperature_2m']
            if temp['min'] < -10:
                concerns.append("extreme cold")
            elif temp['max'] > 35:
                concerns.append("extreme heat")
        
        if 'precipitation' in day_data:
            precip = day_data['precipitation']
            if precip['mean'] > 20:
                concerns.append("heavy precipitation")
        
        if 'wind_speed_80m' in day_data:
            wind = day_data['wind_speed_80m']
            if wind['mean'] > 50:
                concerns.append("high winds")
        
        return concerns
    
    def _rate_operational_conditions(self, day_data: Dict[str, Any]) -> Dict[str, str]:
        """Rate operational conditions."""
        issues = []
        
        if 'precipitation' in day_data:
            if day_data['precipitation']['mean'] > 15:
                issues.append("heavy precipitation")
        
        if 'wind_speed_80m' in day_data:
            if day_data['wind_speed_80m']['mean'] > 40:
                issues.append("strong winds")
        
        if 'temperature_2m' in day_data:
            temp = day_data['temperature_2m']
            if -2 < temp['max'] < 2:
                issues.append("near-freezing temps")
        
        if not issues:
            return {'rating': 'GOOD', 'rationale': 'Favorable conditions'}
        elif len(issues) == 1:
            return {'rating': 'FAIR', 'rationale': f"Watch for {issues[0]}"}
        else:
            return {'rating': 'POOR', 'rationale': f"Multiple concerns: {', '.join(issues)}"}
    
    def _generate_daily_summary(self, day_data: Dict[str, Any]) -> str:
        """Generate brief summary for a single day."""
        return self._generate_executive_summary(day_data)
    
    @staticmethod
    def _identify_models(df: pd.DataFrame) -> List[str]:
        """Identify which models are present in the data."""
        models = set()
        for col in df.columns:
            if 'ecmwf_ifs025' in col:
                models.add('ECMWF_IFS')
            elif 'ecmwf_aifs025' in col:
                models.add('ECMWF_AIFS')
            elif 'gem_global' in col:
                models.add('GEM')
            elif 'gfs_seamless' in col:
                models.add('GFS')
        return sorted(list(models))
    
    @staticmethod
    def _count_ensemble_members(df: pd.DataFrame) -> int:
        """Count total ensemble members."""
        member_cols = [col for col in df.columns if 'member' in col and 'temperature_2m' in col]
        return len(member_cols)
    
    def to_json(self, forecast: Dict[str, Any], pretty: bool = True) -> str:
        """
        Convert forecast to JSON string.
        
        Args:
            forecast: Forecast dictionary
            pretty: If True, format with indentation
            
        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(forecast, indent=2, default=str)
        else:
            return json.dumps(forecast, default=str)
