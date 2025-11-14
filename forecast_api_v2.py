#!/usr/bin/env python3
"""
Enhanced Flask API for Mountain Weather Point Forecast
Version 2.0 - Incorporating Open-Meteo inspired improvements

Key improvements:
- Response caching for performance
- Compression for bandwidth efficiency
- Monitoring and metrics endpoints
- Rate limiting for stability
- Enhanced error handling
- Data quality metrics
"""

from flask import Flask, request, jsonify, render_template_string, Response
from flask_cors import CORS
import json
from datetime import datetime
import os

# Import original functionality
from forecast_cli import run_forecast
from enhanced_forecast_generator import EnhancedForecastGenerator
from improved_simplified_response import create_simplified_response

# Import new improvements
from api_caching_middleware import APICache, CacheWarmer
from api_improvements import (
    setup_compression, APIMonitoring, RateLimiter,
    create_monitoring_endpoints, ErrorHandler,
    add_timing_middleware, ResponseOptimizer
)
from model_aggregation_strategies import (
    DataQualityMonitor, VersionedDataFormat
)

# Initialize Flask app with improvements
app = Flask(__name__)
CORS(app)

# Setup compression
setup_compression(app)

# Initialize monitoring
monitor = APIMonitoring()
create_monitoring_endpoints(app, monitor)
add_timing_middleware(app, monitor)

# Initialize rate limiter
rate_limiter = RateLimiter(requests_per_minute=60)

# Setup error handling
ErrorHandler.handle_api_errors(app)

# Enhanced HTML Dashboard Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mountain Weather Forecast v2.0</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            animation: fadeIn 0.5s ease-in;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            background: #4caf50;
            color: white;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .main-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            margin-bottom: 30px;
            animation: slideUp 0.6s ease-out;
        }
        
        .input-group {
            margin-bottom: 25px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        .input-group input, .input-group select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .input-group input:focus, .input-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .input-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .button:active {
            transform: translateY(0);
        }
        
        .results {
            margin-top: 30px;
            display: none;
        }
        
        .section-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .forecast-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .forecast-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            border: 1px solid #e9ecef;
        }
        
        .forecast-card h3 {
            margin-bottom: 15px;
            color: #495057;
            font-size: 1.3em;
        }
        
        .data-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }
        
        .data-row:last-child {
            border-bottom: none;
        }
        
        .label {
            color: #6c757d;
            font-weight: 500;
        }
        
        .value {
            font-weight: 600;
            color: #333;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            display: inline-block;
        }
        
        .meta-info {
            background: #e7f3ff;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #b3d9ff;
        }
        
        .quality-indicator {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .quality-high {
            background: #d4edda;
            color: #155724;
        }
        
        .quality-moderate {
            background: #fff3cd;
            color: #856404;
        }
        
        .quality-low {
            background: #f8d7da;
            color: #721c24;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .input-row {
                grid-template-columns: 1fr;
            }
            .forecast-grid {
                grid-template-columns: 1fr;
            }
        }
        
        footer {
            text-align: center;
            padding: 20px;
            color: white;
            opacity: 0.8;
        }
        
        footer a {
            color: white;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Mountain Weather Forecast</h1>
            <p>Enhanced with caching, compression, and quality metrics</p>
            <div class="status-badge" id="apiStatus">API Status: Loading...</div>
        </div>
        
        <div class="main-card">
            <form id="forecastForm">
                <div class="input-group">
                    <label for="location">Location Name</label>
                    <input type="text" id="location" name="location" placeholder="e.g., Whistler Blackcomb" required>
                </div>
                
                <div class="input-row">
                    <div class="input-group">
                        <label for="latitude">Latitude</label>
                        <input type="number" id="latitude" name="latitude" step="0.0001" placeholder="49.6507" required>
                    </div>
                    
                    <div class="input-group">
                        <label for="longitude">Longitude</label>
                        <input type="number" id="longitude" name="longitude" step="0.0001" placeholder="-123.0748" required>
                    </div>
                </div>
                
                <div class="input-row">
                    <div class="input-group">
                        <label for="days">Forecast Days</label>
                        <select id="days" name="days">
                            <option value="1">1 Day</option>
                            <option value="3" selected>3 Days</option>
                            <option value="7">7 Days</option>
                        </select>
                    </div>
                    
                    <div class="input-group">
                        <label for="simplified">Response Format</label>
                        <select id="simplified" name="simplified">
                            <option value="true" selected>Simplified (Recommended)</option>
                            <option value="false">Full Detail</option>
                        </select>
                    </div>
                </div>
                
                <button type="submit" class="button">Get Forecast</button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Fetching forecast data...</p>
            </div>
            
            <div id="error" class="error" style="display: none;"></div>
            
            <div id="results" class="results">
                <!-- Results will be inserted here -->
            </div>
        </div>
        
        <footer>
            <p>Weather data by <a href="https://open-meteo.com">Open-Meteo.com</a> | 
               <a href="/api/status">API Status</a> | 
               <a href="/api/metrics">Metrics</a></p>
        </footer>
    </div>
    
    <script>
        // Check API status on load
        fetch('/api/status')
            .then(res => res.json())
            .then(data => {
                const badge = document.getElementById('apiStatus');
                badge.textContent = `API Status: ${data.status.toUpperCase()}`;
                badge.style.background = data.status === 'healthy' ? '#4caf50' : '#ff9800';
            })
            .catch(() => {
                document.getElementById('apiStatus').textContent = 'API Status: Error';
            });
        
        document.getElementById('forecastForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            const error = document.getElementById('error');
            
            loading.style.display = 'block';
            results.style.display = 'none';
            error.style.display = 'none';
            
            const formData = new FormData(e.target);
            const data = {
                latitude: parseFloat(formData.get('latitude')),
                longitude: parseFloat(formData.get('longitude')),
                location_name: formData.get('location'),
                forecast_days: parseInt(formData.get('days')),
                simplified: formData.get('simplified') === 'true'
            };
            
            try {
                const response = await fetch('/api/forecast', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.message || 'Failed to fetch forecast');
                }
                
                // Check if response was cached
                const cacheStatus = response.headers.get('X-Cache');
                
                displayResults(result, cacheStatus);
                loading.style.display = 'none';
                results.style.display = 'block';
                
            } catch (err) {
                loading.style.display = 'none';
                error.style.display = 'block';
                error.textContent = `Error: ${err.message}`;
            }
        });
        
        function displayResults(data, cacheStatus) {
            const results = document.getElementById('results');
            
            if (data.simplified === false) {
                // Full response - show JSON
                results.innerHTML = `
                    <h2 class="section-title">📊 Full Forecast Data</h2>
                    <div class="meta-info">
                        <strong>Cache Status:</strong> ${cacheStatus || 'MISS'} | 
                        <strong>Response Format:</strong> Full | 
                        <strong>Data Quality:</strong> ${data.data_quality?.confidence || 'N/A'}
                    </div>
                    <pre style="background: #f5f5f5; padding: 20px; border-radius: 10px; overflow: auto;">
${JSON.stringify(data, null, 2)}
                    </pre>
                `;
            } else {
                // Simplified response - show formatted view
                let html = `
                    <h2 class="section-title">🏔️ ${data.location} Forecast</h2>
                    <div class="meta-info">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>Last Updated:</strong> ${new Date(data.updated).toLocaleString()} | 
                                <strong>Cache:</strong> ${cacheStatus || 'MISS'}
                            </div>
                            <div class="quality-indicator quality-${data.data_quality?.confidence || 'moderate'}">
                                Confidence: ${data.data_quality?.confidence || 'Moderate'}
                            </div>
                        </div>
                    </div>
                `;
                
                // Current conditions
                if (data.current) {
                    html += `
                        <div class="forecast-card">
                            <h3>Current Conditions</h3>
                            <div class="data-row">
                                <span class="label">Temperature</span>
                                <span class="value">${data.current.temperature.value}°C</span>
                            </div>
                            <div class="data-row">
                                <span class="label">Wind</span>
                                <span class="value">${data.current.wind.speed} km/h ${data.current.wind.direction}</span>
                            </div>
                            <div class="data-row">
                                <span class="label">Precipitation</span>
                                <span class="value">${data.current.precipitation.amount}mm (${data.current.precipitation.type})</span>
                            </div>
                            <div class="data-row">
                                <span class="label">Freezing Level</span>
                                <span class="value">${data.current.freezing_level}m</span>
                            </div>
                            <div class="data-row">
                                <span class="label">Conditions</span>
                                <span class="value">${data.conditions}</span>
                            </div>
                        </div>
                    `;
                }
                
                // Mountain specific
                if (data.mountain) {
                    html += `
                        <div class="forecast-card">
                            <h3>Mountain Summary</h3>
                            <div class="data-row">
                                <span class="label">24h Snow</span>
                                <span class="value">${data.mountain.snow_24h}cm</span>
                            </div>
                            <div class="data-row">
                                <span class="label">48h Snow</span>
                                <span class="value">${data.mountain.snow_48h}cm</span>
                            </div>
                            <div class="data-row">
                                <span class="label">Max Wind 24h</span>
                                <span class="value">${data.mountain.max_wind_24h} km/h</span>
                            </div>
                            <div class="data-row">
                                <span class="label">Freezing Trend</span>
                                <span class="value">${data.mountain.freezing_trend}</span>
                            </div>
                        </div>
                    `;
                }
                
                // Daily forecast
                if (data.daily_3d && data.daily_3d.length > 0) {
                    html += '<h3 style="margin-top: 30px;">Daily Forecast</h3>';
                    html += '<div class="forecast-grid">';
                    
                    data.daily_3d.forEach(day => {
                        html += `
                            <div class="forecast-card">
                                <h4>${day.day} - ${day.date}</h4>
                                <div class="data-row">
                                    <span class="label">Temperature</span>
                                    <span class="value">${day.temps.min}°C to ${day.temps.max}°C</span>
                                </div>
                                <div class="data-row">
                                    <span class="label">Precipitation</span>
                                    <span class="value">${day.precipitation.total}mm (${day.precipitation.type})</span>
                                </div>
                                <div class="data-row">
                                    <span class="label">Snow</span>
                                    <span class="value">${day.precipitation.snow}cm</span>
                                </div>
                                <p style="margin-top: 10px; font-style: italic;">${day.summary}</p>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                }
                
                // Alerts
                if (data.alerts && data.alerts.length > 0) {
                    html += '<h3 style="margin-top: 30px;">⚠️ Weather Alerts</h3>';
                    data.alerts.forEach(alert => {
                        html += `
                            <div class="error" style="background: #fff3cd; color: #856404;">
                                <strong>${alert.type}:</strong> ${alert.message}
                            </div>
                        `;
                    });
                }
                
                results.innerHTML = html;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    """Serve the enhanced dashboard"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/forecast', methods=['POST'])
@APICache.cache_endpoint(ttl=600)  # Cache for 10 minutes
def get_forecast():
    """
    Enhanced forecast endpoint with caching, quality metrics, and rate limiting
    """
    try:
        # Check rate limit
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if not rate_limiter.is_allowed(client_ip):
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'retry_after': 60
            }), 429
        
        # Parse request data
        data = request.json
        
        # Extract and validate parameters
        try:
            lat = float(data.get('latitude'))
            lon = float(data.get('longitude'))
            days = int(data.get('forecast_days', 3))
            location_name = str(data.get('location_name', f'{lat}, {lon}'))
            simplified = data.get('simplified', False)
            
            # Handle string boolean values
            if isinstance(simplified, str):
                simplified = simplified.lower() == 'true'
                
        except (TypeError, ValueError) as e:
            return jsonify({
                'error': 'Invalid parameters',
                'message': f'Invalid parameter type: {str(e)}',
                'expected': {
                    'latitude': 'number (-90 to 90)',
                    'longitude': 'number (-180 to 180)',
                    'forecast_days': 'integer (1-16)',
                    'location_name': 'string',
                    'simplified': 'boolean'
                }
            }), 400
        
        # Validate ranges
        if not -90 <= lat <= 90:
            return jsonify({'error': 'Latitude must be between -90 and 90'}), 400
        if not -180 <= lon <= 180:
            return jsonify({'error': 'Longitude must be between -180 and 180'}), 400
        if not 1 <= days <= 16:
            return jsonify({'error': 'Forecast days must be between 1 and 16'}), 400
        
        # Log request
        app.logger.info(f"Forecast request: lat={lat}, lon={lon}, days={days}, simplified={simplified}")
        
        # Get forecast with enhanced generator
        forecast = run_forecast(lat, lon, days, location_name)
        
        # Add data quality assessment
        if 'hourly' in forecast:
            quality = DataQualityMonitor.assess_forecast_quality(
                forecast.get('hourly_dataframe', forecast['hourly'])
            )
            forecast['data_quality'] = quality
        
        # Add version information
        forecast = VersionedDataFormat.add_version_info(forecast)
        
        # Return appropriate response format
        if simplified:
            response = create_simplified_response(forecast, location_name)
        else:
            # Optimize full response
            response = ResponseOptimizer.optimize_forecast(forecast)
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Forecast generation failed: {str(e)}")
        return jsonify({
            'error': 'Forecast generation failed',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

@app.route('/api/warmup', methods=['POST'])
def warmup_cache():
    """Endpoint to pre-warm cache for popular locations"""
    try:
        # This could be protected with an API key in production
        CacheWarmer.warm_cache()
        return jsonify({
            'status': 'success',
            'message': 'Cache warming initiated',
            'locations': len(CacheWarmer.POPULAR_LOCATIONS)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Get configuration from environment
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'
    
    # Warm cache on startup (optional)
    if os.environ.get('WARM_CACHE_ON_STARTUP', 'false').lower() == 'true':
        try:
            CacheWarmer.warm_cache()
            print("Cache pre-warmed for popular locations")
        except Exception as e:
            print(f"Cache warming failed: {e}")
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug)
