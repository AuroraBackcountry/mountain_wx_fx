import requests
import json

# Test exactly like n8n would
url = "https://mountain-wx-fx.onrender.com/api/forecast"
headers = {
    "Content-Type": "application/json",
    "User-Agent": "axios/1.12.0"  # n8n uses axios
}
body = {
    "latitude": 47.4,
    "longitude": -121.5,
    "location_name": "Snoqualmie Pass",
    "forecast_days": 5,
    "simplified": True
}

print("Sending request like n8n would...")
response = requests.post(url, json=body, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Raw Response Text (first 200 chars): {response.text[:200]}")

# Try to detect any non-JSON characters
raw_text = response.text
if raw_text and not raw_text[0] in ['{', '[']:
    print(f"❌ Response doesn't start with JSON! First char: '{raw_text[0]}' (ord: {ord(raw_text[0])})")
    
# Check for BOM or other invisible characters
if raw_text.startswith('\ufeff'):
    print("❌ Response has BOM character!")
    
# Try parsing
try:
    parsed = json.loads(raw_text)
    print("✅ Successfully parsed JSON")
    print(f"Keys: {list(parsed.keys())}")
except json.JSONDecodeError as e:
    print(f"❌ JSON parsing failed: {e}")
    print(f"Error at position: {e.pos}")
    print(f"Near: {raw_text[max(0, e.pos-20):e.pos+20]}")
