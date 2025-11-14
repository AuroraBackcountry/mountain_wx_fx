"""
Data Processor for Open-Meteo Ensemble Forecasts
Processes Open-Meteo API responses directly.
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from openmeteo_sdk.Variable import Variable
from openmeteo_sdk.Aggregation import Aggregation
from model_mappings import get_model_name


class DataProcessor:
    """Process Open-Meteo ensemble forecast responses."""
    
    @staticmethod
    def process_responses(responses) -> Dict[str, pd.DataFrame]:
        """
        Process Open-Meteo API responses into DataFrames.
        
        Args:
            responses: List of response objects from openmeteo.weather_api()
            
        Returns:
            Dictionary with keys 'hourly' and 'daily', each containing a DataFrame
        """
        all_hourly_data = []
        all_daily_data = []
        
        for response in responses:
            model_id = response.Model()
            model_name = get_model_name(model_id)
            
            # Process hourly data
            if response.Hourly():
                hourly_df = DataProcessor._process_hourly(response, model_name)
                all_hourly_data.append(hourly_df)
            
            # Process daily data
            if response.Daily():
                daily_df = DataProcessor._process_daily(response, model_name)
                all_daily_data.append(daily_df)
        
        # Combine all models
        result = {}
        if all_hourly_data:
            result['hourly'] = pd.concat(all_hourly_data, axis=1)
            result['hourly'] = result['hourly'].loc[:, ~result['hourly'].columns.duplicated()]
        
        if all_daily_data:
            result['daily'] = pd.concat(all_daily_data, axis=1)
            result['daily'] = result['daily'].loc[:, ~result['daily'].columns.duplicated()]
        
        return result
    
    @staticmethod
    def _process_hourly(response, model_name: str) -> pd.DataFrame:
        """Process hourly data from a single response."""
        hourly = response.Hourly()
        hourly_variables = list(map(lambda i: hourly.Variables(i), range(0, hourly.VariablesLength())))
        
        # Create date range
        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            )
        }
        
        # Map variables to extract
        variable_map = {
            'temperature_2m': lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2,
            'relative_humidity_2m': lambda x: x.Variable() == Variable.relative_humidity and x.Altitude() == 2,
            'dew_point_2m': lambda x: x.Variable() == Variable.dew_point and x.Altitude() == 2,
            'precipitation': lambda x: x.Variable() == Variable.precipitation,
            'snowfall': lambda x: x.Variable() == Variable.snowfall,
            'surface_pressure': lambda x: x.Variable() == Variable.surface_pressure,
            'cloud_cover': lambda x: x.Variable() == Variable.cloud_cover,
            'temperature_850hPa': lambda x: x.Variable() == Variable.temperature and x.PressureLevel() == 850,
            'freezing_level_height': lambda x: x.Variable() == Variable.freezing_level_height,
            'wind_direction_80m': lambda x: x.Variable() == Variable.wind_direction and x.Altitude() == 80,
            'wind_speed_80m': lambda x: x.Variable() == Variable.wind_speed and x.Altitude() == 80,
        }
        
        # Extract each variable
        for var_name, filter_func in variable_map.items():
            filtered_vars = filter(filter_func, hourly_variables)
            for variable in filtered_vars:
                member = variable.EnsembleMember()
                col_name = f"{model_name}_{var_name}_member{member}"
                hourly_data[col_name] = variable.ValuesAsNumpy()
        
        df = pd.DataFrame(data=hourly_data)
        df.set_index('date', inplace=True)
        return df
    
    @staticmethod
    def _process_daily(response, model_name: str) -> pd.DataFrame:
        """Process daily data from a single response."""
        daily = response.Daily()
        daily_variables = list(map(lambda i: daily.Variables(i), range(0, daily.VariablesLength())))
        
        # Create date range
        daily_data = {
            "date": pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )
        }
        
        # Map variables to extract
        variable_map = {
            'temperature_2m_min': lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2 and x.Aggregation() == Aggregation.minimum,
            'temperature_2m_max': lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2 and x.Aggregation() == Aggregation.maximum,
            'temperature_2m_mean': lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2 and x.Aggregation() == Aggregation.mean,
            'precipitation_sum': lambda x: x.Variable() == Variable.precipitation and x.Aggregation() == Aggregation.sum,
            'wind_speed_10m_mean': lambda x: x.Variable() == Variable.wind_speed and x.Altitude() == 10 and x.Aggregation() == Aggregation.mean,
            'wind_direction_10m_dominant': lambda x: x.Variable() == Variable.wind_direction and x.Altitude() == 10 and x.Aggregation() == Aggregation.dominant,
            'wind_gusts_10m_mean': lambda x: x.Variable() == Variable.wind_gusts and x.Altitude() == 10 and x.Aggregation() == Aggregation.mean,
            'cloud_cover_min': lambda x: x.Variable() == Variable.cloud_cover and x.Aggregation() == Aggregation.minimum,
            'cloud_cover_max': lambda x: x.Variable() == Variable.cloud_cover and x.Aggregation() == Aggregation.maximum,
            'relative_humidity_2m_mean': lambda x: x.Variable() == Variable.relative_humidity and x.Altitude() == 2 and x.Aggregation() == Aggregation.mean,
            'dew_point_2m_mean': lambda x: x.Variable() == Variable.dew_point and x.Altitude() == 2 and x.Aggregation() == Aggregation.mean,
        }
        
        # Extract each variable
        for var_name, filter_func in variable_map.items():
            filtered_vars = filter(filter_func, daily_variables)
            for variable in filtered_vars:
                member = variable.EnsembleMember()
                col_name = f"{model_name}_{var_name}_member{member}"
                daily_data[col_name] = variable.ValuesAsNumpy()
        
        df = pd.DataFrame(data=daily_data)
        df.set_index('date', inplace=True)
        return df
    
    @staticmethod
    def get_variable_columns(df: pd.DataFrame, variable: str) -> List[str]:
        """
        Get all columns for a specific variable across all models.
        
        Args:
            df: Input DataFrame
            variable: Variable name (e.g., 'temperature_2m')
            
        Returns:
            List of column names
        """
        return [col for col in df.columns if variable in col and 'member' in col]
    
    @staticmethod
    def get_model_columns(df: pd.DataFrame, model: str) -> List[str]:
        """
        Get all columns for a specific model.
        
        Args:
            df: Input DataFrame
            model: Model name (e.g., 'ecmwf_ifs025')
            
        Returns:
            List of column names
        """
        return [col for col in df.columns if col.startswith(model)]
    
    @staticmethod
    def filter_time_range(df: pd.DataFrame, 
                         start: Optional[str] = None,
                         end: Optional[str] = None) -> pd.DataFrame:
        """
        Filter data to specific time range.
        
        Args:
            df: Input DataFrame
            start: Start datetime (ISO format)
            end: End datetime (ISO format)
            
        Returns:
            Filtered DataFrame
        """
        filtered = df.copy()
        
        if start:
            filtered = filtered[filtered.index >= pd.to_datetime(start)]
        if end:
            filtered = filtered[filtered.index <= pd.to_datetime(end)]
        
        return filtered
