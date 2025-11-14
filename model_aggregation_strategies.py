"""
Enhanced model aggregation strategies inspired by Open-Meteo's multi-model approach
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats

class ModelAggregationStrategy:
    """Different strategies for combining multi-model ensemble data."""
    
    @staticmethod
    def weighted_ensemble(data: pd.DataFrame, variable: str, 
                         model_weights: Optional[Dict[str, float]] = None) -> pd.Series:
        """
        Weighted ensemble average based on model performance.
        
        Default weights based on general model performance:
        - ECMWF: Higher weight for temperature and general accuracy
        - GFS: Higher weight for availability of all parameters
        - GEM: Higher weight for cold weather
        - ICON: Balanced weight
        """
        if model_weights is None:
            model_weights = {
                'ecmwf': 0.35,  # Best overall accuracy
                'gfs': 0.25,    # Good coverage, all parameters
                'gem': 0.20,    # Good for Canadian/cold conditions
                'icon': 0.20    # Good for European patterns
            }
        
        # Get columns for variable
        var_cols = [col for col in data.columns if variable in col and 'member' in col]
        if not var_cols:
            return pd.Series()
        
        # Group by model
        model_means = {}
        for col in var_cols:
            model = col.split('_')[0].lower()
            if model not in model_means:
                model_means[model] = []
            model_means[model].append(data[col])
        
        # Calculate weighted average
        weighted_sum = pd.Series(0, index=data.index)
        total_weight = 0
        
        for model, weight in model_weights.items():
            if model in model_means:
                model_data = pd.concat(model_means[model], axis=1).mean(axis=1)
                weighted_sum += model_data * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else pd.Series()
    
    @staticmethod
    def consensus_forecast(data: pd.DataFrame, variable: str, 
                          threshold: float = 0.7) -> pd.Series:
        """
        Return forecast only when models agree (consensus above threshold).
        Useful for high-confidence predictions.
        """
        var_cols = [col for col in data.columns if variable in col and 'member' in col]
        if not var_cols:
            return pd.Series()
        
        # Calculate standard deviation across models
        all_values = data[var_cols]
        model_std = all_values.std(axis=1)
        model_mean = all_values.mean(axis=1)
        
        # Coefficient of variation (normalized measure of agreement)
        cv = model_std / (model_mean.abs() + 1e-6)
        
        # Return mean where models agree (low CV)
        consensus_mask = cv < (1 - threshold)
        result = model_mean.copy()
        result[~consensus_mask] = np.nan
        
        return result
    
    @staticmethod
    def smart_model_selection(data: pd.DataFrame, variable: str,
                            conditions: Dict[str, Any]) -> pd.Series:
        """
        Intelligently select model based on conditions.
        
        Example conditions:
        - Use GEM for very cold conditions
        - Use ECMWF for stable conditions
        - Use ICON for European locations
        """
        var_cols = [col for col in data.columns if variable in col and 'member' in col]
        if not var_cols:
            return pd.Series()
        
        # Get temperature for condition checking
        temp_cols = [col for col in data.columns if 'temperature_2m' in col and 'member' in col]
        temp_mean = data[temp_cols].mean(axis=1) if temp_cols else pd.Series(10, index=data.index)
        
        result = pd.Series(index=data.index)
        
        for idx in data.index:
            # Select model based on conditions
            if temp_mean[idx] < -10:  # Very cold
                # Prefer GEM for cold conditions
                gem_cols = [c for c in var_cols if 'gem' in c.lower()]
                if gem_cols:
                    result[idx] = data.loc[idx, gem_cols].mean()
                else:
                    result[idx] = data.loc[idx, var_cols].mean()
            elif conditions.get('location', {}).get('lon', 0) > -30:  # European
                # Prefer ICON for European locations
                icon_cols = [c for c in var_cols if 'icon' in c.lower()]
                if icon_cols:
                    result[idx] = data.loc[idx, icon_cols].mean()
                else:
                    result[idx] = data.loc[idx, var_cols].mean()
            else:
                # Default to ECMWF
                ecmwf_cols = [c for c in var_cols if 'ecmwf' in c.lower()]
                if ecmwf_cols:
                    result[idx] = data.loc[idx, ecmwf_cols].mean()
                else:
                    result[idx] = data.loc[idx, var_cols].mean()
        
        return result
    
    @staticmethod
    def extreme_value_analysis(data: pd.DataFrame, variable: str,
                              percentile: float = 0.95) -> Dict[str, pd.Series]:
        """
        Analyze extreme values across models for risk assessment.
        Important for mountain weather hazards.
        """
        var_cols = [col for col in data.columns if variable in col and 'member' in col]
        if not var_cols:
            return {}
        
        all_values = data[var_cols]
        
        return {
            'extreme_high': all_values.quantile(percentile, axis=1),
            'extreme_low': all_values.quantile(1 - percentile, axis=1),
            'range': all_values.max(axis=1) - all_values.min(axis=1),
            'likelihood_extreme': (all_values > all_values.quantile(0.9, axis=1).values[:, np.newaxis]).mean(axis=1)
        }

class DataQualityMonitor:
    """Monitor and report on forecast data quality."""
    
    @staticmethod
    def assess_forecast_quality(data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive forecast quality assessment."""
        quality_report = {
            'ensemble_spread': {},
            'data_completeness': {},
            'model_agreement': {},
            'confidence_score': 0
        }
        
        # Check data completeness
        for var in ['temperature_2m', 'precipitation', 'wind_speed']:
            var_cols = [col for col in data.columns if var in col and 'member' in col]
            if var_cols:
                completeness = data[var_cols].notna().mean().mean()
                quality_report['data_completeness'][var] = round(completeness, 3)
        
        # Calculate ensemble spread (uncertainty)
        for var in ['temperature_2m', 'precipitation']:
            var_cols = [col for col in data.columns if var in col and 'member' in col]
            if var_cols:
                spread = data[var_cols].std(axis=1).mean()
                quality_report['ensemble_spread'][var] = round(spread, 2)
        
        # Model agreement (correlation between models)
        model_correlations = []
        for var in ['temperature_2m']:
            var_cols = [col for col in data.columns if var in col and 'member' in col]
            if len(var_cols) > 1:
                corr_matrix = data[var_cols].corr()
                # Get average off-diagonal correlation
                mask = np.ones(corr_matrix.shape, dtype=bool)
                np.fill_diagonal(mask, 0)
                avg_correlation = corr_matrix.values[mask].mean()
                model_correlations.append(avg_correlation)
        
        if model_correlations:
            quality_report['model_agreement']['average'] = round(np.mean(model_correlations), 3)
        
        # Calculate overall confidence score
        completeness_score = np.mean(list(quality_report['data_completeness'].values()))
        agreement_score = quality_report['model_agreement'].get('average', 0.5)
        spread_penalty = 1 - min(0.5, np.mean(list(quality_report['ensemble_spread'].values())) / 10)
        
        quality_report['confidence_score'] = round(
            (completeness_score * 0.3 + agreement_score * 0.4 + spread_penalty * 0.3), 2
        )
        
        return quality_report

class VersionedDataFormat:
    """Handle API versioning for backward compatibility."""
    
    VERSION = "2.0"
    
    @staticmethod
    def add_version_info(response: Dict[str, Any]) -> Dict[str, Any]:
        """Add version information to response."""
        response['_meta'] = {
            'version': VersionedDataFormat.VERSION,
            'format': 'ensemble_forecast',
            'compatibility': ['1.0', '2.0']
        }
        return response
    
    @staticmethod
    def convert_to_v1(response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v2 response to v1 format for backward compatibility."""
        v1_response = response.copy()
        
        # Remove v2-specific fields
        if '_meta' in v1_response:
            del v1_response['_meta']
        
        # Simplify structure
        if 'hourly' in v1_response:
            for hour in v1_response['hourly']:
                # Remove advanced fields not in v1
                for field in ['snow_level', 'quality_metrics']:
                    hour.pop(field, None)
        
        return v1_response

class PerformanceOptimizer:
    """Performance optimizations inspired by Open-Meteo's efficiency."""
    
    @staticmethod
    def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
        """Reduce memory usage of DataFrames."""
        for col in df.columns:
            col_type = df[col].dtype
            
            # Downcast numeric types
            if col_type != 'object':
                c_min = df[col].min()
                c_max = df[col].max()
                
                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                else:
                    # Use float32 instead of float64 for weather data
                    df[col] = df[col].astype(np.float32)
        
        return df
    
    @staticmethod
    def parallel_process_models(data: Dict[str, pd.DataFrame], 
                               process_func, **kwargs) -> Dict[str, Any]:
        """
        Process multiple models in parallel for faster computation.
        Note: Simplified version - real implementation would use multiprocessing.
        """
        import concurrent.futures
        
        results = {}
        
        # In production, this would use ProcessPoolExecutor
        # For now, sequential processing
        for key, df in data.items():
            results[key] = process_func(df, **kwargs)
        
        return results
