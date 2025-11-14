#!/usr/bin/env python3
"""
Flask API for Mountain Weather Point Forecast
Designed for webhook integration and web dashboard

Usage:
    python forecast_api.py
    
Endpoints:
    POST /api/forecast - Get forecast for a specific point
    GET /            - Serve HTML dashboard
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
from datetime import datetime
from forecast_cli import run_forecast
from forecast_generator import ForecastGenerator
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for webhook access

# HTML Dashboard Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mountain Weather Forecast</title>
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
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        .input-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        
        .input-wrapper {
            flex: 1;
            min-width: 200px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .button-wrapper {
            text-align: center;
            margin: 30px 0;
        }
        
        button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 50px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        #loading {
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
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        #results {
            display: none;
        }
        
        .summary-box {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .summary-box h2 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .rating {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .rating.GOOD { background: #4caf50; color: white; }
        .rating.FAIR { background: #ff9800; color: white; }
        .rating.POOR { background: #f44336; color: white; }
        
        .forecast-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .forecast-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #e0e0e0;
        }
        
        .forecast-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #666;
        }
        
        .metric-value {
            font-weight: 600;
            color: #333;
        }
        
        .probability-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .probability-fill {
            height: 100%;
            background: #667eea;
            transition: width 0.5s ease;
        }
        
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }
        
        .icon {
            width: 24px;
            height: 24px;
            display: inline-block;
            vertical-align: middle;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏔️ Mountain Weather Point Forecast</h1>
            <p>Ensemble forecast analysis for any mountain location</p>
            <p style="font-size: 0.9em; opacity: 0.8;">Weather data by <a href="https://open-meteo.com" style="color: white;">Open-Meteo.com</a></p>
        </div>
        
        <div class="card">
            <div class="input-group">
                <div class="input-wrapper">
                    <label for="location">Location Name</label>
                    <input type="text" id="location" placeholder="e.g., Squamish, BC" value="Squamish, BC">
                </div>
                <div class="input-wrapper">
                    <label for="latitude">Latitude</label>
                    <input type="number" id="latitude" placeholder="50.06" value="50.06" step="0.01" min="-90" max="90">
                </div>
                <div class="input-wrapper">
                    <label for="longitude">Longitude</label>
                    <input type="number" id="longitude" placeholder="-123.15" value="-123.15" step="0.01" min="-180" max="180">
                </div>
                <div class="input-wrapper">
                    <label for="days">Forecast Days</label>
                    <input type="number" id="days" value="3" min="1" max="16">
                </div>
            </div>
            
            <div class="button-wrapper">
                <button onclick="getForecast()">Get Forecast</button>
            </div>
            
            <div id="loading">
                <div class="spinner"></div>
                <p>Fetching ensemble forecast data...</p>
            </div>
            
            <div id="error" class="error"></div>
            
            <div id="results">
                <div class="summary-box">
                    <h2>Forecast Summary</h2>
                    <p id="summary-text"></p>
                    <div id="rating" class="rating"></div>
                </div>
                
                <h2>Next 24 Hours</h2>
                <div id="hourly-forecast" class="forecast-grid"></div>
                
                <h2 style="margin-top: 30px;">Daily Forecast</h2>
                <div id="daily-forecast" class="forecast-grid"></div>
            </div>
        </div>
    </div>
    
    <script>
        async function getForecast() {
            const location = document.getElementById('location').value;
            const latitude = parseFloat(document.getElementById('latitude').value);
            const longitude = parseFloat(document.getElementById('longitude').value);
            const days = parseInt(document.getElementById('days').value);
            
            // Validation
            if (!location || isNaN(latitude) || isNaN(longitude)) {
                showError('Please fill in all location fields');
                return;
            }
            
            // UI state
            document.querySelector('button').disabled = true;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            
            try {
                const response = await fetch('/api/forecast', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        location_name: location,
                        latitude: latitude,
                        longitude: longitude,
                        forecast_days: days
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to fetch forecast');
                }
                
                displayForecast(data);
                
            } catch (error) {
                showError(error.message);
            } finally {
                document.querySelector('button').disabled = false;
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function displayForecast(data) {
            // Summary
            document.getElementById('summary-text').textContent = data.summary.executive_summary;
            const rating = document.getElementById('rating');
            rating.textContent = data.summary.operational_conditions.rating;
            rating.className = 'rating ' + data.summary.operational_conditions.rating;
            
            // Hourly forecast (next 24 hours)
            const hourlyContainer = document.getElementById('hourly-forecast');
            hourlyContainer.innerHTML = '';
            
            // Display every 3rd hour for the next 24 hours
            for (let i = 0; i < Math.min(24, data.hourly.length); i += 3) {
                const hour = data.hourly[i];
                const time = new Date(hour.time);
                const card = createHourlyCard(time, hour);
                hourlyContainer.appendChild(card);
            }
            
            // Daily forecast
            const dailyContainer = document.getElementById('daily-forecast');
            dailyContainer.innerHTML = '';
            
            data.daily.forEach(day => {
                const date = new Date(day.date);
                const card = createDailyCard(date, day);
                dailyContainer.appendChild(card);
            });
            
            document.getElementById('results').style.display = 'block';
        }
        
        function createHourlyCard(time, data) {
            const card = document.createElement('div');
            card.className = 'forecast-card';
            
            const temp = data.temperature_2m;
            const precip = data.precipitation;
            const wind = data.wind_speed_80m;
            const probs = data.probabilities;
            
            card.innerHTML = `
                <h3>
                    <span class="icon">🕐</span>
                    ${time.toLocaleString('en-US', { hour: 'numeric', hour12: true })}
                </h3>
                <div class="metric">
                    <span class="metric-label">Temperature</span>
                    <span class="metric-value">${temp.mean.toFixed(1)}°C</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Range</span>
                    <span class="metric-value">${temp.min.toFixed(1)} - ${temp.max.toFixed(1)}°C</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Precipitation</span>
                    <span class="metric-value">${precip.mean.toFixed(1)} mm</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Wind Speed</span>
                    <span class="metric-value">${wind ? wind.mean.toFixed(1) : 'N/A'} km/h</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Rain Probability</span>
                    <span class="metric-value">${(probs.precipitation.measurable * 100).toFixed(0)}%</span>
                    <div class="probability-bar">
                        <div class="probability-fill" style="width: ${probs.precipitation.measurable * 100}%"></div>
                    </div>
                </div>
            `;
            
            return card;
        }
        
        function createDailyCard(date, data) {
            const card = document.createElement('div');
            card.className = 'forecast-card';
            
            const temp = data.temperature_2m || data.temperature_2m_mean || {};
            const precip = data.precipitation || data.precipitation_sum || {};
            
            card.innerHTML = `
                <h3>
                    <span class="icon">📅</span>
                    ${date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
                </h3>
                <div class="metric">
                    <span class="metric-label">Temperature Range</span>
                    <span class="metric-value">${temp.min ? temp.min.toFixed(1) : 'N/A'} - ${temp.max ? temp.max.toFixed(1) : 'N/A'}°C</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Precipitation</span>
                    <span class="metric-value">${precip.mean ? precip.mean.toFixed(1) : 'N/A'} mm</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Summary</span>
                    <span class="metric-value">${data.summary || 'No summary available'}</span>
                </div>
            `;
            
            return card;
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = 'Error: ' + message;
            errorDiv.style.display = 'block';
        }
        
        // Get user's location if available
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    document.getElementById('latitude').value = position.coords.latitude.toFixed(4);
                    document.getElementById('longitude').value = position.coords.longitude.toFixed(4);
                    document.getElementById('location').value = 'Current Location';
                },
                error => {
                    console.log('Geolocation not available:', error);
                }
            );
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Serve the HTML dashboard"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/forecast', methods=['POST'])
def get_forecast():
    """
    API endpoint for point forecast
    
    Expected POST data:
    {
        "latitude": 50.06,
        "longitude": -123.15,
        "location_name": "Squamish, BC",
        "forecast_days": 3,
        "simplified": true
    }
    """
    try:
        data = request.json
        app.logger.info(f"Received request data: {data}")  # Log incoming data
        
        # Validate required fields
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({"error": "Missing latitude or longitude"}), 400
        
        # Convert and validate data types
        try:
            lat = float(data['latitude'])
            lon = float(data['longitude'])
            days = int(data.get('forecast_days', 3))  # Ensure it's an integer
            
            # Handle boolean conversion for simplified parameter
            simplified_param = data.get('simplified', False)
            if isinstance(simplified_param, str):
                simplified = simplified_param.lower() == 'true'
            else:
                simplified = bool(simplified_param)
        except (ValueError, TypeError) as e:
            return jsonify({
                "error": "Invalid data type",
                "details": "Latitude and longitude must be numbers, forecast_days must be an integer",
                "received": {
                    "latitude": f"{type(data.get('latitude')).__name__}: {data.get('latitude')}",
                    "longitude": f"{type(data.get('longitude')).__name__}: {data.get('longitude')}",
                    "forecast_days": f"{type(data.get('forecast_days')).__name__}: {data.get('forecast_days')}"
                }
            }), 400
            
        location_name = data.get('location_name', f"{lat}, {lon}")
        
        # Validate ranges
        if not -90 <= lat <= 90:
            return jsonify({"error": "Latitude must be between -90 and 90"}), 400
        if not -180 <= lon <= 180:
            return jsonify({"error": "Longitude must be between -180 and 180"}), 400
        if not 1 <= days <= 16:
            return jsonify({"error": "Forecast days must be between 1 and 16"}), 400
        
        # Run forecast
        forecast = run_forecast(lat, lon, days, location_name)
        
        # Add readable timestamp
        forecast['metadata']['generated_at_readable'] = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
        
        # Convert numpy/pandas types to Python native types
        def convert_to_native(obj):
            """Convert numpy/pandas types to native Python types"""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_to_native(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            else:
                return obj
        
        # Convert the forecast to native types
        forecast_dict = convert_to_native(forecast)
        
        # If simplified response requested, reduce data size
        if simplified:
            # Helper function to round values to 1 decimal place
            def round_value(val):
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    return round(float(val), 1)
                return val
            
            # Helper to process numeric fields in a dict
            def round_dict_values(d):
                if isinstance(d, dict):
                    return {k: round_dict_values(v) for k, v in d.items()}
                elif isinstance(d, list):
                    return [round_dict_values(item) for item in d]
                else:
                    return round_value(d)
            
            # Process hourly data for next 6 hours with additional fields
            next_6_hours = []
            for hour in forecast_dict.get("hourly", [])[:6]:
                # Handle wind data with fallback to 10m if 80m not available
                wind_80m = hour.get("wind_speed_80m", {})
                wind_10m = hour.get("wind_speed_10m", {})
                wind_dir_80m = hour.get("wind_direction_80m", {})
                wind_dir_10m = hour.get("wind_direction_10m", {})
                
                # Use 80m if available, otherwise fall back to 10m with adjustment
                if isinstance(wind_80m, dict) and wind_80m.get("mean") is not None:
                    wind_speed = round_dict_values(wind_80m)
                    wind_height = "80m"
                elif isinstance(wind_10m, dict) and wind_10m.get("mean") is not None:
                    # Apply terrain factor for 10m to approximate ridge winds
                    adjusted_wind = {}
                    for key, value in wind_10m.items():
                        if isinstance(value, (int, float)):
                            adjusted_wind[key] = round_value(value * 1.4)  # 40% increase for ridge exposure
                        else:
                            adjusted_wind[key] = value
                    wind_speed = adjusted_wind
                    wind_height = "10m_adjusted"
                else:
                    wind_speed = {"mean": 0, "min": 0, "max": 0}
                    wind_height = "unavailable"
                
                # Same for wind direction
                if isinstance(wind_dir_80m, dict) and wind_dir_80m.get("mean") is not None:
                    wind_direction = round_value(wind_dir_80m.get("mean", 0))
                elif isinstance(wind_dir_10m, dict) and wind_dir_10m.get("mean") is not None:
                    wind_direction = round_value(wind_dir_10m.get("mean", 0))
                else:
                    wind_direction = "N/A"
                
                hour_data = {
                    "time": hour.get("time"),
                    "temperature_2m": round_dict_values(hour.get("temperature_2m", {})),
                    "precipitation": round_dict_values(hour.get("precipitation", {})),
                    "wind_speed": wind_speed,
                    "wind_direction": wind_direction,
                    "wind_height": wind_height,
                    "freezing_level_height": round_value(hour.get("freezing_level_height", {}).get("mean", "N/A")) if isinstance(hour.get("freezing_level_height"), dict) and hour.get("freezing_level_height", {}).get("mean") is not None else "N/A",
                    "probabilities": round_dict_values(hour.get("probabilities", {}))
                }
                
                # Add snowfall data if available
                snowfall = hour.get("snowfall", {})
                if isinstance(snowfall, dict) and snowfall:
                    hour_data["snowfall"] = round_value(snowfall.get("mean", 0))
                elif "snow_calculations" in hour:
                    snow_calc = hour["snow_calculations"]
                    if isinstance(snow_calc, dict) and "snow_depth" in snow_calc:
                        snow_depth = snow_calc["snow_depth"]
                        hour_data["snowfall"] = round_value(snow_depth.get("expected", 0)) if isinstance(snow_depth, dict) else 0
                
                # Add units for clarity
                hour_data["units"] = {
                    "temperature": "°C",
                    "precipitation": "mm",
                    "snowfall": "cm",
                    "wind_speed": "km/h",
                    "wind_direction": "degrees",
                    "freezing_level": "m"
                }
                    
                next_6_hours.append(hour_data)
            
            # Process daily summaries with additional fields
            daily_summaries = []
            for day in forecast_dict.get("daily", [])[:3]:
                # Extract temperature values
                temp_data = day.get('temperature_2m', {})
                temp_min = round_value(temp_data.get('min', 'N/A'))
                temp_max = round_value(temp_data.get('max', 'N/A'))
                
                # Get snow data - check both snowfall and snow_calculations
                snowfall_data = day.get('snowfall', {})
                snow_calc_data = day.get('snow_calculations', {})
                
                # Try to get snowfall min/max from ensemble stats
                if isinstance(snowfall_data, dict) and 'min' in snowfall_data:
                    snow_min = round_value(snowfall_data.get('min', 0))
                    snow_max = round_value(snowfall_data.get('max', 0))
                elif isinstance(snow_calc_data, dict) and 'snow_depth' in snow_calc_data:
                    # Use snow depth calculations if available
                    snow_depth = snow_calc_data.get('snow_depth', {})
                    snow_min = round_value(snow_depth.get('low', 0))
                    snow_max = round_value(snow_depth.get('high', 0))
                else:
                    snow_min = 0
                    snow_max = 0
                
                # Get wind data with fallback to 10m
                wind_80m_data = day.get('wind_speed_80m', {})
                wind_10m_data = day.get('wind_speed_10m', day.get('wind_speed_10m_mean', {}))
                
                # Check for 80m wind first, then fall back to 10m
                if isinstance(wind_80m_data, dict) and (wind_80m_data.get('max') is not None or wind_80m_data.get('mean') is not None):
                    wind_speed = round_value(wind_80m_data.get('max', wind_80m_data.get('mean', 0)))
                    wind_height = "80m"
                elif isinstance(wind_10m_data, dict) and (wind_10m_data.get('max') is not None or wind_10m_data.get('mean') is not None):
                    # Apply terrain factor for ridge exposure
                    base_speed = wind_10m_data.get('max', wind_10m_data.get('mean', 0))
                    wind_speed = round_value(base_speed * 1.4)  # 40% increase
                    wind_height = "10m_adjusted"
                else:
                    wind_speed = 0
                    wind_height = "unavailable"
                
                # Get wind direction with fallback
                wind_dir_80m = day.get('wind_direction_80m', {})
                wind_dir_10m = day.get('wind_direction_10m', day.get('wind_direction_10m_dominant', {}))
                
                if isinstance(wind_dir_80m, dict) and wind_dir_80m.get('mean') is not None:
                    wind_direction = round_value(wind_dir_80m.get('mean', 0))
                elif isinstance(wind_dir_10m, dict) and (wind_dir_10m.get('mean') is not None or wind_dir_10m.get('dominant') is not None):
                    wind_direction = round_value(wind_dir_10m.get('mean', wind_dir_10m.get('dominant', 0)))
                else:
                    wind_direction = 'Variable'
                
                # Get freezing level - handle missing data
                freezing_data = day.get('freezing_level_height', {})
                if isinstance(freezing_data, dict) and freezing_data.get('mean') is not None:
                    freezing_level = round_value(freezing_data.get('mean', freezing_data.get('max', "N/A")))
                else:
                    freezing_level = "N/A"
                
                daily_summary = {
                    "date": day.get("date"),
                    "summary": day.get("summary", ""),
                    "temperature_range": f"{temp_min} to {temp_max}°C",
                    "temperature": {
                        "min": temp_min,
                        "max": temp_max,
                        "units": "°C"
                    },
                    "precipitation_total": round_value(day.get('precipitation', {}).get('mean', 0)),
                    "snowfall": {
                        "min": snow_min,
                        "max": snow_max,
                        "units": "cm"
                    },
                    "wind": {
                        "speed": wind_speed,
                        "direction": wind_direction,
                        "height": wind_height,
                        "speed_units": "km/h",
                        "direction_units": "degrees"
                    },
                    "freezing_level": {
                        "height": freezing_level,
                        "units": "m"
                    }
                }
                daily_summaries.append(daily_summary)
            
            # Build simplified response with rounded values
            simplified_response = {
                "metadata": forecast_dict.get("metadata", {}),
                "summary": round_dict_values(forecast_dict.get("summary", {})),
                "current": round_dict_values(next_6_hours[0] if next_6_hours else {}),
                "next_6_hours": next_6_hours,
                "daily_summary": daily_summaries
            }
            return jsonify(simplified_response)
        
        return jsonify(forecast_dict)
        
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Forecast generation failed: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Mountain Weather Forecast API",
        "version": "1.0"
    })

@app.route('/api/test-forecast', methods=['POST'])
def test_forecast():
    """Test endpoint to debug forecast generation"""
    import time
    start_time = time.time()
    
    try:
        data = request.json
        app.logger.info(f"Test forecast request: {data}")
        
        # Step 1: Parse parameters
        lat = float(data.get('latitude', 47.4))
        lon = float(data.get('longitude', -121.5))
        days = int(data.get('forecast_days', 3))
        location_name = data.get('location_name', 'Test Location')
        
        step1_time = time.time()
        app.logger.info(f"Step 1 (parse params) took: {step1_time - start_time:.2f}s")
        
        # Step 2: Run forecast
        try:
            forecast = run_forecast(lat, lon, days, location_name)
            step2_time = time.time()
            app.logger.info(f"Step 2 (run forecast) took: {step2_time - step1_time:.2f}s")
        except Exception as e:
            app.logger.error(f"Forecast generation error: {e}")
            return jsonify({"error": f"Forecast generation failed: {str(e)}"}), 500
        
        # Step 3: Simple response (no complex serialization)
        simple_response = {
            "success": True,
            "location": location_name,
            "coordinates": {"lat": lat, "lon": lon},
            "forecast_days": days,
            "summary": forecast.get('summary', {}).get('executive_summary', 'No summary'),
            "generation_time": f"{time.time() - start_time:.2f} seconds"
        }
        
        return jsonify(simple_response)
        
    except Exception as e:
        app.logger.error(f"Test forecast error: {e}")
        return jsonify({
            "error": str(e),
            "type": type(e).__name__,
            "elapsed_time": f"{time.time() - start_time:.2f} seconds"
        }), 500

if __name__ == '__main__':
    # Run the server
    print("Starting Mountain Weather Forecast API...")
    print("Dashboard available at: http://localhost:5000")
    print("API endpoint: POST http://localhost:5000/api/forecast")
    app.run(host='0.0.0.0', port=5000, debug=True)
