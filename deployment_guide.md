# Mountain Weather Forecast API - Deployment Guide

## 🏗️ Architecture Overview

### How the API Works

```
User/n8n Webhook → Flask API (Python) → Open-Meteo API → Processing → JSON Response
                         ↓
                   forecast_cli.py
                         ↓
                   Weather Models
                   Statistical Analysis
                   JSON Generation
```

The Flask API (`forecast_api.py`) is a Python web service that:
1. Listens for HTTP requests on port 5000
2. Receives location data via POST request
3. Calls the forecast generation functions
4. Returns JSON response to the client

## 🚀 Production Deployment Options

### Option 1: Cloud Platform (Recommended for Multi-User)

#### **Google Cloud Run** (Serverless, scales automatically)

1. Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask flask-cors gunicorn

# Copy application
COPY . .

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "forecast_api:app"]
```

2. Create `.gcloudignore`:
```
venv/
__pycache__/
*.pyc
.git/
.cache/
forecast_output.json
```

3. Deploy:
```bash
# Build and deploy
gcloud run deploy mountain-weather-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 120
```

**Pros:**
- Auto-scales from 0 to thousands of users
- Pay only for actual usage
- Handles HTTPS automatically
- No server maintenance

#### **AWS Lambda + API Gateway**

1. Create `lambda_handler.py`:
```python
import json
from forecast_cli import run_forecast

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        
        forecast = run_forecast(
            lat=body['latitude'],
            lon=body['longitude'],
            days=body.get('forecast_days', 3),
            location_name=body.get('location_name')
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(forecast)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

2. Package and deploy:
```bash
# Create deployment package
pip install -r requirements.txt -t package/
cp *.py package/
cd package && zip -r ../deployment.zip .

# Deploy via AWS CLI or Console
aws lambda create-function \
  --function-name mountain-weather-forecast \
  --runtime python3.11 \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://deployment.zip
```

### Option 2: VPS with Process Manager (Traditional)

#### **Using systemd (Ubuntu/Debian)**

1. Create `gunicorn_config.py`:
```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

2. Create systemd service `/etc/systemd/system/weather-api.service`:
```ini
[Unit]
Description=Mountain Weather Forecast API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/mountain_weather
Environment="PATH=/opt/mountain_weather/venv/bin"
ExecStart=/opt/mountain_weather/venv/bin/gunicorn \
    --config gunicorn_config.py \
    forecast_api:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Install and start:
```bash
# Install on server
cd /opt
sudo git clone [repo] mountain_weather
cd mountain_weather
sudo ./setup.sh

# Install production dependencies
source venv/bin/activate
pip install gunicorn flask-cors

# Start service
sudo systemctl enable weather-api
sudo systemctl start weather-api
```

4. Add Nginx reverse proxy `/etc/nginx/sites-available/weather-api`:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

### Option 3: Docker Container (Flexible)

1. Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  weather-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - WORKERS=4
    restart: unless-stopped
    volumes:
      - ./cache:/app/.cache
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - weather-api
    restart: unless-stopped

  redis:
    image: redis:alpine
    restart: unless-stopped
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

2. Create production `app.py` wrapper:
```python
#!/usr/bin/env python3
"""Production wrapper with caching and rate limiting"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_caching import Cache
import redis
from forecast_cli import run_forecast

app = Flask(__name__)
CORS(app)

# Redis caching
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://redis:6379/0'
})

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"],
    storage_uri="redis://redis:6379/1"
)

@app.route('/api/forecast', methods=['POST'])
@limiter.limit("10 per minute")
@cache.cached(timeout=3600, key_prefix='forecast', 
              query_string=True, make_cache_key=lambda: str(request.json))
def get_forecast():
    # Same forecast logic but with caching
    ...
```

### Option 4: Platform-as-a-Service (Easiest)

#### **Heroku**

1. Create `Procfile`:
```
web: gunicorn forecast_api:app --timeout 120
```

2. Create `runtime.txt`:
```
python-3.11.0
```

3. Deploy:
```bash
heroku create mountain-weather-api
git push heroku main
heroku config:set FLASK_ENV=production
```

#### **Railway.app or Render.com**
- Even simpler - just connect GitHub repo
- Auto-deploys on push
- Built-in SSL, scaling, monitoring

## 🔧 Production Considerations

### 1. **Caching Strategy**
```python
# Add to forecast_api.py
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_forecast(lat_lon_days_hash):
    # Cache forecasts for 1 hour
    ...

# In API endpoint:
cache_key = hashlib.md5(f"{lat}{lon}{days}".encode()).hexdigest()
forecast = cached_forecast(cache_key)
```

### 2. **Rate Limiting**
- Protect against abuse
- Ensure fair usage
- Prevent API quota exhaustion

### 3. **Monitoring**
```python
# Add health metrics
@app.route('/health')
def health():
    return {
        "status": "healthy",
        "cache_size": cache.cache._cache.currsize,
        "requests_today": get_request_count()
    }
```

### 4. **Error Handling**
```python
# Add retry logic for Open-Meteo
@retry(tries=3, delay=2, backoff=2)
def fetch_weather_data(...):
    # API call with exponential backoff
```

### 5. **Security**
- Use environment variables for sensitive data
- Implement API keys if needed
- Enable CORS only for trusted domains
- Use HTTPS in production

## 📊 Scaling Strategies

### For n8n Integration:
1. **Single Instance**: VPS with systemd (up to 100 users)
2. **Multi-Region**: Cloud Run or Lambda (unlimited scale)
3. **High-Volume**: Kubernetes cluster with caching layer

### Cost Estimates:
- **Cloud Run**: ~$0-10/month for moderate usage
- **VPS**: $5-20/month fixed cost
- **Lambda**: Pay-per-request, very cheap for low volume

## 🚨 Quick Start Commands

### Local Development:
```bash
cd /path/to/mountain_Wx_Fx
source venv/bin/activate
python forecast_api.py
```

### Production (Docker):
```bash
docker-compose up -d
# API available at http://localhost:5000
```

### Production (Cloud Run):
```bash
gcloud run deploy --source .
# Get URL from output
```

The best approach depends on your specific needs:
- **Few users, simple setup**: VPS with systemd
- **Variable load, auto-scaling**: Cloud Run or Lambda
- **Full control, complex setup**: Kubernetes
- **Quick prototype**: Heroku or Railway
