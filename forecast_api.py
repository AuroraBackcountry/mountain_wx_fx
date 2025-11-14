#!/usr/bin/env python3
"""
Flask API for Mountain Weather Point Forecast
Enhanced with mountain-focused response format

Endpoints:
    POST /api/forecast - Get mountain-focused forecast
    GET /              - Serve HTML dashboard
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
from datetime import datetime
from forecast_cli import run_forecast
from mountain_focused_response import create_mountain_focused_response
from improved_simplified_response import create_simplified_response
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
    Mountain-focused weather forecast endpoint.
    Now returns enhanced format with trends, hazards, and accurate snow calculations.
    
    Expected POST data:
    {
        "latitude": 50.06,
        "longitude": -123.15,
        "location_name": "Whistler",
        "forecast_days": 3,
        "simplified": true,
        "elevation": 2181  // Optional
    }
    """
    try:
        data = request.json
        app.logger.info(f"Received request data: {data}")
        
        # Validate required fields
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({"error": "Missing latitude or longitude"}), 400
        
        # Convert and validate data types
        try:
            lat = float(data['latitude'])
            lon = float(data['longitude'])
            days = int(data.get('forecast_days', 3))
            elevation = data.get('elevation', None)
            if elevation is not None:
                elevation = int(elevation)
            
            # Handle boolean conversion for simplified parameter
            simplified_param = data.get('simplified', True)  # Default to True
            if isinstance(simplified_param, str):
                simplified = simplified_param.lower() == 'true'
            else:
                simplified = bool(simplified_param)
        except (ValueError, TypeError) as e:
            return jsonify({
                "error": "Invalid data type",
                "details": "Latitude/longitude must be numbers, forecast_days and elevation must be integers"
            }), 400
            
        location_name = data.get('location_name', f"{lat}, {lon}")
        
        # Validate ranges
        if not -90 <= lat <= 90:
            return jsonify({"error": "Latitude must be between -90 and 90"}), 400
        if not -180 <= lon <= 180:
            return jsonify({"error": "Longitude must be between -180 and 180"}), 400
        if not 1 <= days <= 16:
            return jsonify({"error": "Forecast days must be between 1 and 16"}), 400
        
        # Run forecast (this automatically uses EnhancedForecastGenerator)
        forecast = run_forecast(lat, lon, days, location_name)
        
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
        
        # Always return mountain-focused response
        response = create_mountain_focused_response(
            forecast_dict,
            location_name,
            elevation=elevation
        )
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        app.logger.error(f"Forecast generation failed: {str(e)}")
        return jsonify({"error": f"Forecast generation failed: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Mountain Weather Forecast API",
        "version": "2.0"
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
