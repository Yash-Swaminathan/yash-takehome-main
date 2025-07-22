# Calgary Open Data API Setup Guide

## 🚨 **Critical API Update**

Calgary's Open Data portal has upgraded to **Socrata API Version 3.0**, which requires authentication. This is why you're getting **400 Bad Request** and **403 Forbidden** errors.

## 🔧 **Required Fix: Get a Socrata App Token**

### Step 1: Register for a Socrata Developer Account
1. Go to [https://dev.socrata.com/register](https://dev.socrata.com/register)
2. Sign up for a free account
3. Verify your email address

### Step 2: Create an Application Token
1. Login to your Socrata developer account
2. Go to your developer settings
3. Create a new application token
4. Copy the token (it looks like: `aBcD3FgH1jKlMnOpQrStUvWxYz`)

### Step 3: Configure Your Environment
Create a `.env` file in the `backend/` directory:

```env
# Flask Configuration
FLASK_CONFIG=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///urban_dashboard.db

# Calgary Open Data API Configuration (Socrata v3.0)
# REQUIRED: Get your free app token at https://dev.socrata.com/register
SOCRATA_APP_TOKEN=YOUR_ACTUAL_TOKEN_HERE

# LLM Configuration (Optional)
HUGGINGFACE_API_KEY=your-huggingface-api-key-here

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://localhost:3000

# Development settings
PORT=5001
DEBUG=true
```

## 📊 **Updated Dataset Endpoints**

The corrected API endpoints are now:

### ✅ **Working Endpoints (with App Token):**
```
# Zoning Data (qe6k-p9nh)
https://data.calgary.ca/api/v3/views/qe6k-p9nh/query.json

# Building Permits (c2es-76ed) 
https://data.calgary.ca/api/v3/views/c2es-76ed/query.json

# 3D Buildings (cchr-krqg)
https://data.calgary.ca/api/v3/views/cchr-krqg/query.json

# Building Footprints (uc4c-6kbd)
https://data.calgary.ca/api/v3/views/uc4c-6kbd/query.json
```

### ❌ **Old Format (No Longer Works):**
```
# These return 400 Bad Request
https://data.calgary.ca/resource/qe6k-p9nh.json
https://data.calgary.ca/resource/c2es-76ed.json
```

## 🧪 **Test Your Setup**

After configuring your app token, test the APIs:

```bash
# Test with curl (replace YOUR_TOKEN with your actual token)
curl -H "X-App-Token: YOUR_TOKEN" \
  "https://data.calgary.ca/api/v3/views/qe6k-p9nh/query.json?$limit=2"

# Should return JSON data instead of 403 Forbidden
```

## 🔄 **What Changed in the Code**

I've updated the application to:

1. **Use v3 API endpoints**: `/api/v3/views/DATASET/query.json` format
2. **Add authentication headers**: Automatic token injection
3. **Handle new data format**: JSON instead of GeoJSON
4. **Add building permits support**: New endpoint for `c2es-76ed` dataset
5. **Improved error handling**: Clear warnings about missing tokens

## 🚀 **New API Endpoints Available**

Your application now supports:

```bash
# Get zoning data
GET /api/buildings/zoning?bounds=51.042,-114.075,51.048,-114.065&limit=100

# Get building permits  
GET /api/buildings/permits?bounds=51.042,-114.075,51.048,-114.065&limit=100

# Get 3D buildings (updated)
GET /api/buildings/3d?bounds=51.042,-114.075,51.048,-114.065&limit=100
```

## 🆘 **Still Having Issues?**

1. **Check your token**: Make sure it's correctly set in `.env`
2. **Restart the server**: Changes to `.env` require a restart
3. **Check logs**: Look for "No SOCRATA_APP_TOKEN configured" warnings
4. **Verify token**: Test the curl command above with your token

## 📝 **Rate Limits**

With an app token, you get:
- **1,000 requests per hour** (vs 100 without token)
- Higher priority in API queue
- More reliable access during peak usage

---

**🎉 This should resolve your 400/403 errors and give you access to both zoning (`qe6k-p9nh`) and building permits (`c2es-76ed`) data!** 