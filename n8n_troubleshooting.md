# n8n Integration Troubleshooting Guide

## ✅ Fixed Issues

### 1. Type Conversion Error
**Error**: `'<=' not supported between instances of 'int' and 'str'`
**Solution**: API now properly converts string inputs to correct types

### 2. JSON Serialization Error
**Error**: `Invalid JSON in response body`
**Solution**: 
- Fixed numpy/pandas type serialization
- Added `simplified` response option for smaller payloads

## 🔧 Updated n8n Configuration

### For Standard Use:
```json
{
  "method": "POST",
  "url": "https://mountain-wx-fx.onrender.com/api/forecast",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "latitude": {{$json.latitude}},
    "longitude": {{$json.longitude}},
    "location_name": "{{$json.location_name}}",
    "forecast_days": {{$json.forecast_days || 3}},
    "simplified": true
  }
}
```

### Key Changes:
1. **Add `"simplified": true`** - This reduces response from ~65KB to ~5KB
2. **No quotes around numbers** in the body
3. **30-second timeout** recommended

## 📊 Response Formats

### Simplified Response (Recommended for n8n):
```json
{
  "metadata": {...},
  "summary": {
    "executive_summary": "Temps -4 to 5°C. Rain expected.",
    "operational_conditions": {
      "rating": "GOOD",
      "rationale": "Favorable conditions"
    }
  },
  "current": {
    "time": "2025-11-14T18:00:00Z",
    "temperature_2m": {...},
    "precipitation": {...}
  },
  "next_6_hours": [...],
  "daily_summary": [...]
}
```

### Full Response:
- Contains all 72 hourly entries
- All ensemble statistics
- Model comparisons
- Can be 60KB+ in size

## 🚨 Common Issues & Solutions

### 1. Response Too Large
**Symptom**: n8n hangs or errors with large responses
**Solution**: Always use `"simplified": true`

### 2. Invalid Data Types
**Symptom**: 500 error about type conversion
**Solution**: Ensure latitude/longitude are numbers in your n8n data

### 3. Timeout Errors
**Symptom**: Request times out
**Solution**: 
- Increase timeout to 30000ms
- API can take 5-15 seconds for complex forecasts

### 4. CORS Errors
**Symptom**: Browser console shows CORS error
**Solution**: API has CORS enabled, check your n8n configuration

## 🧪 Testing Your Integration

### 1. Test with cURL:
```bash
curl -X POST https://mountain-wx-fx.onrender.com/api/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 50.06,
    "longitude": -123.15,
    "simplified": true
  }' | jq .
```

### 2. Test Data Extraction in n8n:
- Temperature: `{{$json.current.temperature_2m.mean}}`
- Summary: `{{$json.summary.executive_summary}}`
- Rating: `{{$json.summary.operational_conditions.rating}}`

### 3. Error Handling in n8n:
Add an IF node after HTTP Request:
- Condition: `{{$json.error}} is empty`
- True: Process forecast data
- False: Handle error

## 🔍 Debug Information

If you still have issues, check:

1. **Render Logs**: https://dashboard.render.com
2. **API Health**: https://mountain-wx-fx.onrender.com/api/health
3. **Test with simplified=false** to see full response

## 💡 Pro Tips

1. **Cache Results**: Weather doesn't change minute-by-minute
2. **Batch Locations**: Process multiple in a loop
3. **Schedule Updates**: Run every few hours, not continuously
4. **Monitor API**: Set up health check in n8n

## 📞 Need Help?

- Check GitHub Issues: https://github.com/AuroraBackcountry/mountain_wx_fx/issues
- API Status: Check Render dashboard
- n8n Community: https://community.n8n.io/
