"""
API Improvements inspired by Open-Meteo's production architecture
"""

from flask import Flask, request, jsonify, Response
from flask_compress import Compress
from datetime import datetime
import time
import psutil
import os
from collections import deque
from typing import Dict, Any
import gzip
import json

class APIMonitoring:
    """Monitor API health and performance metrics."""
    
    def __init__(self, window_size: int = 1000):
        self.request_times = deque(maxlen=window_size)
        self.error_counts = {'4xx': 0, '5xx': 0}
        self.request_counts = {'total': 0, 'cached': 0}
        self.start_time = time.time()
    
    def record_request(self, duration_ms: float, status_code: int, cached: bool = False):
        """Record request metrics."""
        self.request_times.append(duration_ms)
        self.request_counts['total'] += 1
        
        if cached:
            self.request_counts['cached'] += 1
        
        if 400 <= status_code < 500:
            self.error_counts['4xx'] += 1
        elif 500 <= status_code < 600:
            self.error_counts['5xx'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        uptime = time.time() - self.start_time
        
        if self.request_times:
            avg_response = sum(self.request_times) / len(self.request_times)
            p95_response = sorted(self.request_times)[int(len(self.request_times) * 0.95)]
        else:
            avg_response = 0
            p95_response = 0
        
        return {
            'uptime_seconds': round(uptime, 1),
            'requests': {
                'total': self.request_counts['total'],
                'cached': self.request_counts['cached'],
                'cache_hit_rate': round(self.request_counts['cached'] / max(1, self.request_counts['total']), 3)
            },
            'response_times_ms': {
                'average': round(avg_response, 1),
                'p95': round(p95_response, 1)
            },
            'errors': self.error_counts,
            'system': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent
            }
        }

class RateLimiter:
    """Simple rate limiter for API protection."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # IP -> list of timestamps
    
    def is_allowed(self, ip: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if ip in self.requests:
            self.requests[ip] = [t for t in self.requests[ip] if t > minute_ago]
        
        # Check rate limit
        if ip not in self.requests:
            self.requests[ip] = []
        
        if len(self.requests[ip]) >= self.requests_per_minute:
            return False
        
        self.requests[ip].append(now)
        return True

def setup_compression(app: Flask):
    """Enable response compression like Open-Meteo."""
    Compress(app)
    app.config['COMPRESS_ALGORITHM'] = ['gzip', 'br', 'deflate']
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIN_SIZE'] = 500
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html', 'text/css', 'text/xml',
        'application/json', 'application/javascript'
    ]

def create_monitoring_endpoints(app: Flask, monitor: APIMonitoring):
    """Add monitoring endpoints similar to production APIs."""
    
    @app.route('/api/metrics', methods=['GET'])
    def metrics():
        """Prometheus-compatible metrics endpoint."""
        metrics = monitor.get_metrics()
        
        # Format as Prometheus metrics
        output = []
        output.append(f'# HELP api_uptime_seconds API uptime in seconds')
        output.append(f'api_uptime_seconds {metrics["uptime_seconds"]}')
        
        output.append(f'# HELP api_requests_total Total number of API requests')
        output.append(f'api_requests_total {metrics["requests"]["total"]}')
        
        output.append(f'# HELP api_cache_hit_rate Cache hit rate')
        output.append(f'api_cache_hit_rate {metrics["requests"]["cache_hit_rate"]}')
        
        output.append(f'# HELP api_response_time_ms Response time in milliseconds')
        output.append(f'api_response_time_ms{{quantile="0.95"}} {metrics["response_times_ms"]["p95"]}')
        output.append(f'api_response_time_ms{{quantile="avg"}} {metrics["response_times_ms"]["average"]}')
        
        return Response('\n'.join(output), mimetype='text/plain')
    
    @app.route('/api/status', methods=['GET'])
    def status():
        """Detailed status endpoint."""
        metrics = monitor.get_metrics()
        
        # Determine health status
        if metrics['errors']['5xx'] > 10:
            health_status = 'degraded'
        elif metrics['system']['cpu_percent'] > 90 or metrics['system']['memory_percent'] > 90:
            health_status = 'stressed'
        else:
            health_status = 'healthy'
        
        return jsonify({
            'status': health_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': '2.0',
            'metrics': metrics,
            'features': {
                'caching': True,
                'compression': True,
                'rate_limiting': True,
                'ensemble_models': 4,
                'snowfall_calculation': True
            }
        })

class ErrorHandler:
    """Improved error handling with detailed messages."""
    
    @staticmethod
    def handle_api_errors(app: Flask):
        """Register error handlers for better API responses."""
        
        @app.errorhandler(400)
        def bad_request(error):
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid request parameters',
                'details': str(error),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        
        @app.errorhandler(429)
        def rate_limit_exceeded(error):
            return jsonify({
                'error': 'Rate Limit Exceeded',
                'message': 'Too many requests. Please try again later.',
                'retry_after': 60,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 429
        
        @app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'reference_id': str(int(time.time()))  # For log correlation
            }), 500
        
        @app.errorhandler(503)
        def service_unavailable(error):
            return jsonify({
                'error': 'Service Temporarily Unavailable',
                'message': 'The weather data service is temporarily unavailable',
                'retry_after': 300,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503

# Middleware for request timing
def add_timing_middleware(app: Flask, monitor: APIMonitoring):
    """Add request timing middleware."""
    
    @app.before_request
    def before_request():
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000
            monitor.record_request(
                duration, 
                response.status_code,
                response.headers.get('X-Cache') == 'HIT'
            )
        return response

# GeoDNS-like location routing suggestion
class LocationRouter:
    """Suggest optimal API endpoints based on user location."""
    
    REGIONS = {
        'us-west': {'lat_range': (30, 50), 'lon_range': (-130, -100)},
        'us-east': {'lat_range': (25, 50), 'lon_range': (-100, -65)},
        'eu': {'lat_range': (35, 70), 'lon_range': (-10, 40)},
        'asia': {'lat_range': (-10, 55), 'lon_range': (60, 150)}
    }
    
    @staticmethod
    def get_optimal_region(lat: float, lon: float) -> str:
        """Determine optimal region for a given location."""
        for region, bounds in LocationRouter.REGIONS.items():
            if (bounds['lat_range'][0] <= lat <= bounds['lat_range'][1] and
                bounds['lon_range'][0] <= lon <= bounds['lon_range'][1]):
                return region
        return 'global'  # Default

# Response optimization
class ResponseOptimizer:
    """Optimize response payload size."""
    
    @staticmethod
    def optimize_forecast(forecast: Dict[str, Any], aggressive: bool = False) -> Dict[str, Any]:
        """Remove unnecessary precision and redundant data."""
        import copy
        optimized = copy.deepcopy(forecast)
        
        def round_numbers(obj, precision=1):
            """Recursively round all numbers in object."""
            if isinstance(obj, dict):
                return {k: round_numbers(v, precision) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [round_numbers(item, precision) for item in obj]
            elif isinstance(obj, float):
                return round(obj, precision)
            return obj
        
        # Round all numbers to 1 decimal
        optimized = round_numbers(optimized)
        
        if aggressive:
            # Remove some statistical fields for smaller payload
            for hour in optimized.get('hourly', []):
                for var in ['temperature_2m', 'precipitation', 'wind_speed']:
                    if var in hour and isinstance(hour[var], dict):
                        # Keep only essential stats
                        hour[var] = {
                            'mean': hour[var].get('mean'),
                            'min': hour[var].get('min'),
                            'max': hour[var].get('max')
                        }
        
        return optimized
