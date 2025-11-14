"""Model ID to name mappings for Open-Meteo API"""

# Model ID to name mapping based on Open-Meteo API response
MODEL_ID_TO_NAME = {
    60: "ecmwf_ifs025",
    17: "gem_global", 
    61: "ecmwf_aifs025",
    2: "gfs_seamless"
}

# Model name to display name mapping
MODEL_DISPLAY_NAMES = {
    "ecmwf_ifs025": "ECMWF_IFS",
    "gem_global": "GEM",
    "ecmwf_aifs025": "ECMWF_AIFS", 
    "gfs_seamless": "GFS"
}

def get_model_name(model_id: int) -> str:
    """Get model name from numeric ID."""
    return MODEL_ID_TO_NAME.get(model_id, f"model_{model_id}")

def get_display_name(model_name: str) -> str:
    """Get display name from model name."""
    return MODEL_DISPLAY_NAMES.get(model_name, model_name.upper())
