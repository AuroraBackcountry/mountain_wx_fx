# n8n Integration Guide for Mountain Weather Forecast System

## 📊 Input/Output Overview

### Input Parameters
The system accepts configuration through Python code variables:

```python
{
    "latitude": 50.06,              # Location latitude
    "longitude": -123.15,           # Location longitude
    "hourly": [...],                # List of hourly variables to fetch
    "daily": [...],                 # List of daily variables to fetch
    "models": [...],                # Weather models to use
    "timezone": "auto",             # Timezone setting
    "forecast_days": 3              # Number of days to forecast
}
```

### Output Structure
The system generates a JSON file (`forecast_output.json`) with this structure:

```json
{
  "metadata": {
    "generated_at": "2025-11-14T17:36:00.743363Z",
    "location": {"lat": 50.06, "lon": -123.15, "name": "Squamish, BC"},
    "forecast_start": "2025-11-14T08:00:00+00:00",
    "forecast_end": "2025-11-17T07:00:00+00:00",
    "models": ["ECMWF_AIFS", "ECMWF_IFS", "GEM", "GFS"],
    "ensemble_members": 154
  },
  "summary": {
    "executive_summary": "Temps -4 to 5°C. Rain expected.",
    "key_concerns": [],
    "operational_conditions": {
      "rating": "GOOD",
      "rationale": "Favorable conditions"
    }
  },
  "hourly": [
    {
      "time": "2025-11-14T08:00:00+00:00",
      "temperature_2m": {
        "min": -1.45,
        "max": 3.8,
        "mean": 1.48,
        "median": 1.55,
        "std_dev": 0.95,
        "percentiles": {"p10": 0.17, "p25": 0.9, "p75": 2.19, "p90": 2.53},
        "trend": "stable"
      },
      "precipitation": {...},
      "wind_speed_80m": {...},
      "probabilities": {
        "precipitation": {"measurable": 0.06, "heavy": 0.0},
        "freezing": 0.14,
        "strong_winds": 0.0
      }
    }
    // ... more hourly entries
  ],
  "daily": [...],
  "model_comparison": [...]
}
```

## 🔌 n8n Integration Methods

### Method 1: Command Line Execution (Easiest)

Create a wrapper script `forecast_api.py`:

```python
#!/usr/bin/env python3
"""
Command-line wrapper for n8n integration
Usage: python forecast_api.py --lat 50.06 --lon -123.15 --days 3
"""
import argparse
import json
import sys
from main import main  # Import existing main function

def run_forecast(lat, lon, days, location_name=None):
    """Run forecast with custom parameters"""
    # Monkey-patch the params in main.py
    import main as main_module
    
    # Override the params
    original_main = main_module.main
    
    def custom_main():
        # Backup original params
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": [
                "temperature_2m", 
                "relative_humidity_2m",
                "precipitation", 
                "snowfall",
                "wind_speed_80m",
                "wind_direction_80m"
            ],
            "daily": [
                "temperature_2m_min", 
                "temperature_2m_max",
                "temperature_2m_mean",
                "precipitation_sum",
                "wind_speed_10m_mean"
            ],
            "models": ["ecmwf_ifs025", "gem_global", "ecmwf_aifs025", "gfs_seamless"],
            "timezone": "auto",
            "forecast_days": days
        }
        
        # Temporarily replace params in main
        main_module.params = params
        
        # Run the original main
        return original_main()
    
    # Execute
    forecast = custom_main()
    
    # Output JSON to stdout for n8n
    print(json.dumps(forecast, indent=2))
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate weather forecast')
    parser.add_argument('--lat', type=float, required=True, help='Latitude')
    parser.add_argument('--lon', type=float, required=True, help='Longitude')
    parser.add_argument('--days', type=int, default=3, help='Forecast days (1-16)')
    parser.add_argument('--name', type=str, help='Location name')
    
    args = parser.parse_args()
    run_forecast(args.lat, args.lon, args.days, args.name)
```

**n8n Setup:**
1. Use the **Execute Command** node
2. Command: `cd /path/to/mountain_Wx_Fx && source venv/bin/activate && python forecast_api.py --lat {{$json.latitude}} --lon {{$json.longitude}} --days 3`
3. Output will be JSON that n8n can parse

### Method 2: HTTP API Wrapper

Create `api_server.py`:

```python
#!/usr/bin/env python3
"""
Flask API wrapper for HTTP integration
"""
from flask import Flask, request, jsonify
import threading
import time
from main import main
import json
import os

app = Flask(__name__)

# Cache to prevent API spam
cache = {}
CACHE_DURATION = 3600  # 1 hour

@app.route('/forecast', methods=['POST'])
def get_forecast():
    """
    POST endpoint expecting:
    {
        "latitude": 50.06,
        "longitude": -123.15,
        "forecast_days": 3,
        "location_name": "Squamish, BC"
    }
    """
    data = request.json
    
    # Validate input
    if not data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({"error": "Missing latitude or longitude"}), 400
    
    lat = float(data['latitude'])
    lon = float(data['longitude'])
    days = data.get('forecast_days', 3)
    name = data.get('location_name', f"{lat},{lon}")
    
    # Check cache
    cache_key = f"{lat},{lon},{days}"
    if cache_key in cache:
        cached_data, timestamp = cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return jsonify(cached_data)
    
    # Run forecast (you'd need to modify main.py to accept params)
    # For now, we'll use the file-based approach
    os.system(f"python forecast_api.py --lat {lat} --lon {lon} --days {days}")
    
    # Read the output file
    with open('forecast_output.json', 'r') as f:
        forecast = json.load(f)
    
    # Cache the result
    cache[cache_key] = (forecast, time.time())
    
    return jsonify(forecast)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**n8n Setup:**
1. Use the **HTTP Request** node
2. Method: POST
3. URL: `http://your-server:5000/forecast`
4. Body:
```json
{
  "latitude": {{$json.latitude}},
  "longitude": {{$json.longitude}},
  "forecast_days": 3,
  "location_name": "{{$json.location}}"
}
```

### Method 3: Direct File Integration

The simplest approach for local n8n:

1. **Execute Command** node runs: `cd /path/to/mountain_Wx_Fx && source venv/bin/activate && python main.py`
2. **Read Binary File** node reads: `/path/to/mountain_Wx_Fx/forecast_output.json`
3. **Move Binary Data** node converts to JSON
4. Use the JSON data in subsequent nodes

## 📝 n8n Workflow Examples

### Example 1: Weather Alert Workflow
```yaml
Trigger (Cron - Daily) 
  → Execute Command (Run forecast)
  → Read File (forecast_output.json)
  → Function (Check for alerts)
  → IF (Bad weather?)
    → Send Email/Slack notification
```

### Example 2: Multi-Location Forecast
```yaml
Webhook (Receives locations)
  → Loop over locations
    → Execute Command (forecast_api.py with lat/lon)
    → Store in Database
  → Aggregate Results
  → Send Report
```

### Example 3: Dashboard Integration
```yaml
HTTP Webhook (Dashboard request)
  → Execute Command (Get forecast)
  → Transform Data (Format for charts)
  → Respond to Webhook (Return JSON)
```

## 🚀 Quick Start for n8n

1. **Install the system on your n8n server:**
```bash
cd /opt
git clone [your-repo] mountain_Wx_Fx
cd mountain_Wx_Fx
./setup.sh
```

2. **Test the command line:**
```bash
source venv/bin/activate
python main.py
cat forecast_output.json  # Verify output
```

3. **Create n8n workflow:**
   - Add **Cron** node (trigger)
   - Add **Execute Command** node:
     ```
     cd /opt/mountain_Wx_Fx && \
     source venv/bin/activate && \
     python main.py
     ```
   - Add **Read Binary File** node:
     - File Path: `/opt/mountain_Wx_Fx/forecast_output.json`
   - Add **Move Binary Data** node:
     - Mode: JSON Parse
   - Now you have the forecast data to use!

## 🔧 Advanced Integration

For production use, consider:

1. **Environment Variables** for API keys (if needed)
2. **Error handling** for API failures
3. **Logging** for debugging
4. **Rate limiting** to respect API limits
5. **Caching** to reduce API calls
6. **Monitoring** for system health

## 📊 Data Processing in n8n

Once you have the JSON data, you can:
- Extract specific values: `{{$json.hourly[0].temperature_2m.mean}}`
- Check probabilities: `{{$json.hourly[0].probabilities.precipitation.heavy}}`
- Get summaries: `{{$json.summary.executive_summary}}`
- Compare models: `{{$json.model_comparison[0].agreement_level}}`
