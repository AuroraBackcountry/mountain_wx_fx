"""
Probability Analyzer for Ensemble Weather Forecasts
Calculates event probabilities from ensemble spread.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class ProbabilityAnalyzer:
    """Calculate weather event probabilities from ensemble data."""
    
    @staticmethod
    def calculate_probability(df: pd.DataFrame, variable: str, 
                             condition: callable) -> pd.Series:
        """
        Calculate probability of a condition being met.
        
        Args:
            df: DataFrame with ensemble data
            variable: Variable name
            condition: Function that returns True/False for each value
            
        Returns:
            Series with probabilities (0-1) for each timestamp
        """
        cols = [col for col in df.columns if variable in col and 'member' in col]
        
        if not cols:
            raise ValueError(f"No columns found for variable: {variable}")
        
        # Apply condition to all members
        meets_condition = df[cols].apply(lambda x: condition(x))
        
        # Calculate probability as fraction of members meeting condition
        probability = meets_condition.sum(axis=1) / len(cols)
        
        return probability
    
    @staticmethod
    def calculate_precipitation_probabilities(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate precipitation event probabilities.
        
        Args:
            df: DataFrame with precipitation data
            
        Returns:
            DataFrame with probability columns
        """
        probs = pd.DataFrame(index=df.index)
        
        # P(measurable precip) - any amount > 0.1mm
        probs['p_measurable'] = ProbabilityAnalyzer.calculate_probability(
            df, 'precipitation', lambda x: x > 0.1
        )
        
        # P(>5mm) - significant precipitation
        probs['p_heavy'] = ProbabilityAnalyzer.calculate_probability(
            df, 'precipitation', lambda x: x > 5.0
        )
        
        # P(>10mm) - very heavy precipitation
        probs['p_very_heavy'] = ProbabilityAnalyzer.calculate_probability(
            df, 'precipitation', lambda x: x > 10.0
        )
        
        return probs
    
    @staticmethod
    def calculate_temperature_probabilities(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate temperature event probabilities.
        
        Args:
            df: DataFrame with temperature data
            
        Returns:
            DataFrame with probability columns
        """
        probs = pd.DataFrame(index=df.index)
        
        # P(freezing) - temperature below 0°C
        probs['p_freezing'] = ProbabilityAnalyzer.calculate_probability(
            df, 'temperature_2m', lambda x: x < 0
        )
        
        # P(hard freeze) - temperature below -5°C
        probs['p_hard_freeze'] = ProbabilityAnalyzer.calculate_probability(
            df, 'temperature_2m', lambda x: x < -5
        )
        
        # P(hot) - temperature above 30°C
        probs['p_hot'] = ProbabilityAnalyzer.calculate_probability(
            df, 'temperature_2m', lambda x: x > 30
        )
        
        return probs
    
    @staticmethod
    def calculate_wind_probabilities(df: pd.DataFrame, 
                                    wind_var: str = 'wind_speed_80m') -> pd.DataFrame:
        """
        Calculate wind event probabilities.
        
        Args:
            df: DataFrame with wind data
            wind_var: Wind variable name
            
        Returns:
            DataFrame with probability columns
        """
        probs = pd.DataFrame(index=df.index)
        
        # P(breezy) - wind > 25 km/h
        probs['p_breezy'] = ProbabilityAnalyzer.calculate_probability(
            df, wind_var, lambda x: x > 25
        )
        
        # P(windy) - wind > 40 km/h
        probs['p_windy'] = ProbabilityAnalyzer.calculate_probability(
            df, wind_var, lambda x: x > 40
        )
        
        # P(very windy) - wind > 60 km/h
        probs['p_very_windy'] = ProbabilityAnalyzer.calculate_probability(
            df, wind_var, lambda x: x > 60
        )
        
        return probs
    
    @staticmethod
    def calculate_snow_probabilities(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate snow event probabilities.
        
        Args:
            df: DataFrame with snowfall data
            
        Returns:
            DataFrame with probability columns
        """
        probs = pd.DataFrame(index=df.index)
        
        # P(any snow)
        probs['p_snow'] = ProbabilityAnalyzer.calculate_probability(
            df, 'snowfall', lambda x: x > 0.1
        )
        
        # P(>5cm)
        probs['p_moderate_snow'] = ProbabilityAnalyzer.calculate_probability(
            df, 'snowfall', lambda x: x > 5.0
        )
        
        # P(>10cm)
        probs['p_heavy_snow'] = ProbabilityAnalyzer.calculate_probability(
            df, 'snowfall', lambda x: x > 10.0
        )
        
        return probs
    
    @staticmethod
    def get_probabilities_dict(probs_df: pd.DataFrame, 
                              timestamp: pd.Timestamp) -> Dict[str, float]:
        """
        Get probabilities as dictionary for a specific timestamp.
        
        Args:
            probs_df: DataFrame with probabilities
            timestamp: Timestamp to extract
            
        Returns:
            Dictionary with probabilities
        """
        if timestamp not in probs_df.index:
            raise ValueError(f"Timestamp {timestamp} not in data")
        
        row = probs_df.loc[timestamp]
        
        return {col: float(row[col]) for col in probs_df.columns}
