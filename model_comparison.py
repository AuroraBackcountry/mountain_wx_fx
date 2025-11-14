"""
Model Comparison for Ensemble Weather Forecasts
Compares forecast models to identify agreement/disagreement.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from model_mappings import MODEL_DISPLAY_NAMES


class ModelComparison:
    """Compare forecast models to identify agreement and outliers."""
    
    @staticmethod
    def compare_models(df: pd.DataFrame, variable: str) -> pd.DataFrame:
        """
        Compare models for a specific variable.
        
        Args:
            df: DataFrame with ensemble data
            variable: Variable name (e.g., 'temperature_2m')
            
        Returns:
            DataFrame with comparison metrics
        """
        # Identify unique models
        models = ModelComparison._identify_models(df, variable)
        
        if len(models) < 2:
            raise ValueError("Need at least 2 models for comparison")
        
        # Calculate mean for each model at each timestamp
        model_means = {}
        for model in models:
            model_cols = [col for col in df.columns 
                         if model in col and variable in col and 'member' in col]
            if model_cols:
                model_means[model] = df[model_cols].mean(axis=1)
        
        # Calculate comparison metrics
        comparison_df = pd.DataFrame(index=df.index)
        
        # Overall mean across all models
        all_means = pd.DataFrame(model_means)
        comparison_df['mean'] = all_means.mean(axis=1)
        comparison_df['std'] = all_means.std(axis=1)
        comparison_df['min'] = all_means.min(axis=1)
        comparison_df['max'] = all_means.max(axis=1)
        comparison_df['range'] = comparison_df['max'] - comparison_df['min']
        
        # Coefficient of variation (normalized spread)
        comparison_df['cv'] = comparison_df['std'] / comparison_df['mean'].abs()
        
        return comparison_df, model_means
    
    @staticmethod
    def identify_outliers(model_means: Dict[str, pd.Series], 
                         threshold: float = 1.5) -> pd.DataFrame:
        """
        Identify which models are outliers at each timestamp.
        
        Args:
            model_means: Dictionary of model names to mean series
            threshold: Standard deviation threshold for outlier (default: 1.5)
            
        Returns:
            DataFrame with outlier flags for each model
        """
        all_means = pd.DataFrame(model_means)
        
        # Calculate z-scores for each model
        overall_mean = all_means.mean(axis=1)
        overall_std = all_means.std(axis=1)
        
        outliers = pd.DataFrame(index=all_means.index)
        
        for model in all_means.columns:
            z_scores = (all_means[model] - overall_mean) / overall_std
            outliers[f'{model}_outlier'] = z_scores.abs() > threshold
            outliers[f'{model}_z_score'] = z_scores
        
        return outliers
    
    @staticmethod
    def calculate_agreement_level(cv: float) -> str:
        """
        Classify agreement level based on coefficient of variation.
        
        Args:
            cv: Coefficient of variation
            
        Returns:
            Agreement level string
        """
        if cv < 0.1:
            return 'high'
        elif cv < 0.3:
            return 'moderate'
        else:
            return 'low'
    
    @staticmethod
    def get_comparison_dict(comparison_df: pd.DataFrame,
                           model_means: Dict[str, pd.Series],
                           outliers: pd.DataFrame,
                           variable: str,
                           timestamp: pd.Timestamp) -> Dict:
        """
        Get comparison results as dictionary for a specific timestamp.
        
        Args:
            comparison_df: DataFrame with comparison metrics
            model_means: Dictionary of model means
            outliers: DataFrame with outlier flags
            variable: Variable name
            timestamp: Timestamp to extract
            
        Returns:
            Dictionary with comparison results
        """
        if timestamp not in comparison_df.index:
            raise ValueError(f"Timestamp {timestamp} not in data")
        
        cv = float(comparison_df.loc[timestamp, 'cv'])
        agreement_level = ModelComparison.calculate_agreement_level(cv)
        
        # Identify which models are outliers
        outlier_models = []
        agreeing_models = []
        
        for model in model_means.keys():
            outlier_col = f'{model}_outlier'
            if outlier_col in outliers.columns:
                if outliers.loc[timestamp, outlier_col]:
                    outlier_models.append(model)
                else:
                    agreeing_models.append(model)
        
        result = {
            'variable': variable,
            'agreement_level': agreement_level,
            'models_in_agreement': agreeing_models,
            'outlier_models': outlier_models,
            'spread': float(comparison_df.loc[timestamp, 'range']),
            'coefficient_variation': cv,
            'model_values': {
                model: float(series.loc[timestamp]) 
                for model, series in model_means.items()
            }
        }
        
        return result
    
    @staticmethod
    def _identify_models(df: pd.DataFrame, variable: str) -> List[str]:
        """Identify which models are present for a variable."""
        models = set()
        
        for col in df.columns:
            if variable in col and 'member' in col:
                # Extract model name (part before the variable)
                parts = col.split('_')
                if len(parts) >= 2:
                    # Assume model name is first part(s) before variable
                    if 'ecmwf_ifs025' in col:
                        models.add('ecmwf_ifs025')
                    elif 'ecmwf_aifs025' in col:
                        models.add('ecmwf_aifs025')
                    elif 'gem_global' in col:
                        models.add('gem_global')
                    elif 'gfs_seamless' in col:
                        models.add('gfs_seamless')
        
        return sorted(list(models))
