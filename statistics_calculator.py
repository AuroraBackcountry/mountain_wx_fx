"""
Statistics Calculator for Ensemble Weather Forecasts
Calculates comprehensive statistics across ensemble members.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Union


class StatisticsCalculator:
    """Calculate ensemble statistics for weather variables."""
    
    @staticmethod
    def calculate_statistics(df: pd.DataFrame, variable: str) -> pd.DataFrame:
        """
        Calculate comprehensive statistics for a variable across all ensemble members.
        
        Args:
            df: DataFrame with ensemble data
            variable: Variable name (e.g., 'temperature_2m')
            
        Returns:
            DataFrame with statistics (min, max, mean, median, std, percentiles)
        """
        # Get all columns for this variable
        cols = [col for col in df.columns if variable in col and 'member' in col]
        
        if not cols:
            raise ValueError(f"No columns found for variable: {variable}")
        
        # Calculate statistics
        stats_df = pd.DataFrame(index=df.index)
        stats_df['min'] = df[cols].min(axis=1)
        stats_df['max'] = df[cols].max(axis=1)
        stats_df['mean'] = df[cols].mean(axis=1)
        stats_df['median'] = df[cols].median(axis=1)
        stats_df['std'] = df[cols].std(axis=1)
        stats_df['p10'] = df[cols].quantile(0.10, axis=1)
        stats_df['p25'] = df[cols].quantile(0.25, axis=1)
        stats_df['p75'] = df[cols].quantile(0.75, axis=1)
        stats_df['p90'] = df[cols].quantile(0.90, axis=1)
        
        return stats_df
    
    @staticmethod
    def calculate_trend(series: pd.Series, window: int = 3) -> List[str]:
        """
        Calculate trend for a time series.
        
        Args:
            series: Time series data
            window: Window size for trend calculation
            
        Returns:
            List of trend labels for each point
        """
        trends = []
        
        for i in range(len(series)):
            if i < window:
                trends.append('stable')
                continue
            
            # Calculate rate of change
            recent_vals = series.iloc[i-window:i+1]
            change = recent_vals.iloc[-1] - recent_vals.iloc[0]
            rate = change / window
            
            # Classify trend
            if abs(rate) < 0.5:
                trends.append('stable')
            elif rate > 2.0:
                trends.append('rapidly_rising')
            elif rate > 0.5:
                trends.append('rising')
            elif rate < -2.0:
                trends.append('rapidly_falling')
            else:
                trends.append('falling')
        
        return trends
    
    @staticmethod
    def get_statistics_dict(df: pd.DataFrame, variable: str, 
                          timestamp: pd.Timestamp) -> Dict[str, float]:
        """
        Get statistics as a dictionary for a specific timestamp.
        
        Args:
            df: DataFrame with statistics
            variable: Variable name
            timestamp: Timestamp to extract
            
        Returns:
            Dictionary with statistics
        """
        if timestamp not in df.index:
            raise ValueError(f"Timestamp {timestamp} not in data")
        
        row = df.loc[timestamp]
        
        return {
            'min': float(row['min']),
            'max': float(row['max']),
            'mean': float(row['mean']),
            'median': float(row['median']),
            'std_dev': float(row['std']),
            'percentiles': {
                'p10': float(row['p10']),
                'p25': float(row['p25']),
                'p75': float(row['p75']),
                'p90': float(row['p90'])
            }
        }
