"""
API Response Caching Middleware
Inspired by Open-Meteo's efficient data storage approach
"""

import hashlib
import json
import time
from functools import wraps
from flask import request, jsonify, make_response
import redis
from typing import Optional, Dict, Any

# Initialize Redis connection (optional, can use in-memory cache)
try:
    cache = redis.Redis(host='localhost', port=6379, decode_responses=True)
    CACHE_AVAILABLE = True
except:
    CACHE_AVAILABLE = False
    cache = {}  # Fallback to in-memory dict

class APICache:
    """Cache API responses to reduce Open-Meteo API calls and improve response times."""
    
    @staticmethod
    def generate_cache_key(lat: float, lon: float, days: int, simplified: bool) -> str:
        """Generate cache key based on request parameters."""
        # Round coordinates to 2 decimal places (1km resolution)
        lat_rounded = round(lat, 2)
        lon_rounded = round(lon, 2)
        
        # Create cache key
        key_parts = [
            'forecast',
            f'lat_{lat_rounded}',
            f'lon_{lon_rounded}',
            f'days_{days}',
            f'simple_{simplified}'
        ]
        
        return ':'.join(key_parts)
    
    @staticmethod
    def get_cached_response(key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired."""
        if CACHE_AVAILABLE:
            cached = cache.get(key)
            if cached:
                return json.loads(cached)
        else:
            # In-memory cache
            if key in cache:
                cached_data, expiry = cache[key]
                if time.time() < expiry:
                    return cached_data
                else:
                    del cache[key]
        return None
    
    @staticmethod
    def set_cached_response(key: str, data: Dict[str, Any], ttl: int = 600):
        """Cache response with TTL (default 10 minutes)."""
        if CACHE_AVAILABLE:
            cache.setex(key, ttl, json.dumps(data))
        else:
            # In-memory cache with expiry
            cache[key] = (data, time.time() + ttl)
    
    @staticmethod
    def cache_endpoint(ttl: int = 600):
        """Decorator to cache API endpoints."""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Only cache GET and POST requests with specific parameters
                if request.method in ['GET', 'POST']:
                    try:
                        # Extract parameters
                        data = request.json if request.method == 'POST' else request.args
                        lat = float(data.get('latitude', 0))
                        lon = float(data.get('longitude', 0))
                        days = int(data.get('forecast_days', 3))
                        simplified = data.get('simplified', False)
                        
                        # Generate cache key
                        cache_key = APICache.generate_cache_key(lat, lon, days, simplified)
                        
                        # Check cache
                        cached = APICache.get_cached_response(cache_key)
                        if cached:
                            response = make_response(jsonify(cached))
                            response.headers['X-Cache'] = 'HIT'
                            response.headers['Cache-Control'] = f'public, max-age={ttl}'
                            return response
                        
                        # Call original function
                        result = f(*args, **kwargs)
                        
                        # Cache successful responses
                        if result.status_code == 200:
                            response_data = result.get_json()
                            APICache.set_cached_response(cache_key, response_data, ttl)
                            result.headers['X-Cache'] = 'MISS'
                            result.headers['Cache-Control'] = f'public, max-age={ttl}'
                        
                        return result
                        
                    except Exception:
                        # If caching fails, just call the original function
                        pass
                
                return f(*args, **kwargs)
            return wrapped
        return decorator

# Additional optimization: Pre-warm cache for popular locations
class CacheWarmer:
    """Pre-warm cache for popular mountain locations."""
    
    POPULAR_LOCATIONS = [
        {"name": "Whistler", "lat": 50.12, "lon": -122.95},
        {"name": "Chamonix", "lat": 45.92, "lon": 6.87},
        {"name": "Zermatt", "lat": 46.02, "lon": 7.75},
        {"name": "Aspen", "lat": 39.19, "lon": -106.82},
        {"name": "St. Anton", "lat": 47.13, "lon": 10.27},
    ]
    
    @staticmethod
    def warm_cache():
        """Pre-fetch forecasts for popular locations."""
        from forecast_cli import run_forecast
        
        for location in CacheWarmer.POPULAR_LOCATIONS:
            try:
                # Generate forecast
                forecast = run_forecast(
                    location['lat'], 
                    location['lon'], 
                    3, 
                    location['name']
                )
                
                # Cache both simplified and full versions
                for simplified in [True, False]:
                    key = APICache.generate_cache_key(
                        location['lat'], 
                        location['lon'], 
                        3, 
                        simplified
                    )
                    APICache.set_cached_response(key, forecast, ttl=900)  # 15 min
                    
            except Exception as e:
                print(f"Failed to warm cache for {location['name']}: {e}")
