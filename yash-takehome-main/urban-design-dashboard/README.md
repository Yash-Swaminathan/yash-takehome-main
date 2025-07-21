# Urban Design 3D City Dashboard with Calgary Open Data Integration

A full-stack web application that visualizes Calgary building data in 3D using real Calgary Open Data APIs and allows users to query buildings using natural language, powered by LLM integration.

## 🌟 Features

### Core Functionality
- **Real Calgary Open Data**: Direct integration with Calgary's Open Data APIs
- **3D Building Visualization**: Interactive Three.js-based 3D city view with actual building heights
- **Multiple Data Sources**: Building footprints, 3D buildings, zoning, and property assessments
- **Natural Language Queries**: Ask questions like "buildings over 100 feet" or "commercial buildings"
- **Smart Building Filtering**: LLM-powered query interpretation with fallback rule-based parsing
- **Interactive Building Details**: Click any building to see detailed information including assessed value
- **Value-Based Visualization**: Buildings colored by assessed value or building type
- **Project Persistence**: Save and load your map analyses for future reference

### Calgary Open Data Integration
- **Building Roof Outlines** (Dataset: `uc4c-6kbd`): Detailed building footprints
- **3D Buildings** (Dataset: `cchr-krqg`): Buildings with height information  
- **Land-Use Districts** (Dataset: `qe6k-p9nh`): Zoning information
- **Property Assessments** (Dataset: `4bsw-nn7w`): Current year assessed values
- **Real-time Data**: Fetches fresh data from Calgary's Socrata API
- **Intelligent Fallback**: Graceful degradation to sample data when APIs are unavailable

## 🏗️ Architecture

### Backend (Flask)
```
backend/
├── app/
│   ├── models/          # Database models (User, Project, Building)
│   ├── services/        # Business logic (DataFetcher, LLMService, BuildingProcessor)
│   ├── routes/          # API endpoints
│   └── utils/           # Utilities and exceptions
├── config.py            # Configuration management
└── run.py              # Application entry point
```

### Frontend (React + Three.js)
```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── Map3D/       # 3D visualization components
│   │   ├── QueryInterface/ # Natural language query UI
│   │   ├── BuildingPopup/  # Building detail modal
│   │   ├── ProjectManager/ # Save/load projects
│   │   └── UserLogin/   # User identification
│   └── services/        # API client and utilities
└── public/             # Static assets
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- npm or yarn
- (Optional) Socrata App Token for higher API rate limits

### 1. Clone and Setup Backend

```bash
# Clone the repository
git clone <repository-url>
cd urban-design-dashboard

# Setup Python virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Create environment configuration
# Create .env file with the following content:
```

**Backend .env file:**
```env
# Flask Configuration
FLASK_CONFIG=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///urban_dashboard.db

# Calgary Open Data API Configuration
# Get your free app token at: https://dev.socrata.com/register
# This is optional but recommended for higher rate limits (1000 requests/hour vs 100)
SOCRATA_APP_TOKEN=your-socrata-app-token-here

# LLM Configuration (Optional)
HUGGINGFACE_API_KEY=your-huggingface-api-key-here

# Development settings
PORT=5001
```

### 2. Setup Frontend

```bash
cd ../frontend
npm install
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## ⚙️ Configuration

### Calgary Open Data API Setup

The application integrates with Calgary's Open Data portal using the Socrata API:

1. **No API Key Required**: Basic functionality works without any keys
2. **Optional App Token**: Get higher rate limits (1000 vs 100 requests/hour)
   - Sign up at [Socrata Developer Portal](https://dev.socrata.com/register)
   - Create an app to get your token
   - Add `SOCRATA_APP_TOKEN=your-token` to your `.env` file

### Environment Variables (.env)

Create a `.env` file in the backend directory:

```env
# Flask Configuration
FLASK_CONFIG=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///urban_dashboard.db

# Calgary Open Data API Configuration
SOCRATA_APP_TOKEN=your-socrata-app-token-here  # Optional but recommended

# Hugging Face LLM API (Optional - fallback parsing will be used without it)
HUGGINGFACE_API_KEY=your-huggingface-api-key-here

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://localhost:3000
```

## 📊 Data Sources

### Calgary Open Data APIs

The application uses four main Calgary Open Data datasets:

#### 1. Building Roof Outlines (`uc4c-6kbd`)
- **URL**: `https://data.calgary.ca/resource/uc4c-6kbd.geojson`
- **Contains**: Detailed building footprint polygons
- **Usage**: Building shapes and outlines

#### 2. 3D Buildings Citywide (`cchr-krqg`) 
- **URL**: `https://data.calgary.ca/resource/cchr-krqg.geojson`
- **Contains**: Building footprints with height attributes
- **Usage**: 3D building visualization with accurate heights

#### 3. Land-Use Districts (`qe6k-p9nh`)
- **URL**: `https://data.calgary.ca/resource/qe6k-p9nh.geojson` 
- **Contains**: Zoning classifications and land use districts
- **Usage**: Zoning-based building categorization

#### 4. Current-Year Property Assessments (`4bsw-nn7w`)
- **URL**: `https://data.calgary.ca/resource/4bsw-nn7w.json`
- **Contains**: Property assessed values, zoning, use classifications
- **Usage**: Value-based building visualization and filtering

### Data Processing Features
- **Spatial Filtering**: Query buildings within specific geographic bounds
- **Data Combination**: Automatically merges data from multiple sources
- **Error Handling**: Graceful fallback to sample data when APIs are unavailable
- **Caching**: Intelligent caching to reduce API calls

## 🎮 How to Use

### 1. Data Source Selection
Choose your preferred data source from the header dropdown:
- **Combined (Recommended)**: Uses 3D buildings + footprints + zoning data
- **3D Buildings Only**: Height-accurate buildings from the 3D dataset
- **Building Footprints**: Basic building outlines

### 2. Explore Buildings
- **Navigate**: Drag to rotate, scroll to zoom, right-click to pan
- **Select Buildings**: Click any building to see details including assessed value
- **Building Colors**: 
  - **Value-Based** (when assessment data available):
    - 🔴 Red: Very high value (>$5M)
    - 🟠 Orange: High value ($2-5M)
    - 🟡 Yellow: Medium-high value ($1-2M)
    - 🟢 Light Green: Medium value ($500k-1M)
    - 🔵 Blue: Lower value (<$500k)
  - **Type-Based** (fallback):
    - 🔵 Blue: Commercial
    - 🟢 Green: Residential  
    - 🟣 Purple: Industrial
    - 🟠 Orange: Mixed Use
    - ⚪ Gray: Unknown/Other

### 3. Test Calgary Open Data APIs
Use the header buttons to test API connectivity:
- **Test 3D API**: Verifies connection to 3D buildings dataset
- **Test Assessments**: Checks property assessment data availability

### 4. Query Buildings
Enhanced natural language queries with Calgary data:

**Height Queries** (using real building heights):
- "buildings over 100 feet"
- "buildings taller than 50 meters"
- "tallest buildings in the area"

**Value Queries** (using assessment data):
- "buildings worth more than $1,000,000"
- "most expensive buildings"
- "properties under $500,000"

**Zoning Queries** (using Calgary zoning codes):
- "RC-G zoning" (Residential - Grade-Oriented Infill)
- "CC-X buildings" (Centre City)
- "commercial zoned properties"

## 🔧 Enhanced API Endpoints

### Calgary Open Data Specific
- `GET /api/buildings/3d?bounds=lat1,lng1,lat2,lng2&limit=500` - Get 3D buildings with height data
- `GET /api/buildings/zoning?bounds=lat1,lng1,lat2,lng2&limit=1000` - Get zoning information
- `GET /api/buildings/assessments?parcel_ids=id1,id2&limit=1000` - Get property assessments

### Enhanced Building Data
- `GET /api/buildings/area?bounds=lat1,lng1,lat2,lng2&source=combined&refresh=false` - Get buildings with data source selection
  - `source`: `combined`, `3d`, `footprints`
  - `refresh`: Force fresh API call vs cached data

### Original Endpoints (Enhanced)
- `GET /api/buildings/area?bounds=lat1,lng1,lat2,lng2` - Get buildings in area
- `GET /api/buildings/{id}` - Get building details
- `POST /api/buildings/filter` - Filter buildings
- `POST /api/buildings/refresh` - Refresh data from Calgary API

## 🌐 Example API Usage

### Fetch 3D Buildings in Downtown Calgary
```bash
curl "http://localhost:5001/api/buildings/3d?bounds=51.042,-114.075,51.048,-114.065&limit=100"
```

### Get Zoning Data for Area
```bash
curl "http://localhost:5001/api/buildings/zoning?bounds=51.042,-114.075,51.048,-114.065"
```

### Combined Data with Different Sources
```bash
# Get combined 3D + footprint data
curl "http://localhost:5001/api/buildings/area?bounds=51.042,-114.075,51.048,-114.065&source=combined&refresh=true"

# Get only 3D buildings
curl "http://localhost:5001/api/buildings/area?bounds=51.042,-114.075,51.048,-114.065&source=3d"
```

## 🎯 Calgary-Specific Features

### Geographic Bounds
- **Default Area**: Downtown Calgary (approximately 3-4 blocks)
- **Coordinates**: 51.042°N to 51.048°N, -114.075°W to -114.065°W
- **Customizable**: Modify bounds in the frontend to explore different areas

### Building Types (Calgary-Specific)
The application recognizes Calgary's building classification system:
- Commercial office buildings
- Residential condominiums and apartments  
- Mixed-use developments
- Industrial facilities
- Institutional buildings

### Zoning Integration
Supports Calgary's zoning codes:
- **R-C1 to R-C2**: Residential contexts
- **CC-X**: Centre City District
- **M-CG**: Mixed use commercial/residential
- **I-**: Industrial districts

### Assessment Data
- Current year property assessments
- Land and building values
- Property use classifications
- Assessment methodology alignment with Calgary practices

## 🚀 Deployment

### Environment Variables for Production

**Backend (.env for production):**
```env
FLASK_CONFIG=production
SECRET_KEY=your-secure-production-secret
DATABASE_URL=postgresql://user:pass@host:port/db  # For production database
SOCRATA_APP_TOKEN=your-production-socrata-token
HUGGINGFACE_API_KEY=your-production-hf-key  # Optional
```

**Frontend (Vercel/Netlify environment variables):**
```env
REACT_APP_API_URL=https://your-backend-domain.com/api
```

## 🛠️ Development

### Testing Calgary Open Data Integration

1. **Test API Connectivity**:
```bash
# Test 3D buildings endpoint
curl "https://data.calgary.ca/resource/cchr-krqg.geojson?$limit=5"

# Test building footprints
curl "https://data.calgary.ca/resource/uc4c-6kbd.geojson?$limit=5"
```

2. **Verify Data Processing**:
```python
# In Python shell
from app.services.data_fetcher import DataFetcher
fetcher = DataFetcher()
buildings = fetcher.fetch_3d_buildings(bounds=(51.042, -114.075, 51.048, -114.065), limit=10)
print(f"Fetched {len(buildings)} buildings")
```

### Adding New Data Sources

1. **Add new fetcher method** in `DataFetcher`:
```python
def fetch_new_dataset(self, bounds=None, limit=1000):
    url = f"{self.base_url}/your-dataset-id.geojson"
    # Implementation
```

2. **Update building processor** to handle new data format
3. **Add new API endpoint** in routes
4. **Update frontend** to use new data

## 🤝 Calgary Open Data Attribution

This application uses data from the City of Calgary's Open Data portal:
- **Source**: [data.calgary.ca](https://data.calgary.ca)
- **License**: Open Government License - Calgary
- **Attribution**: City of Calgary Open Data
- **Last Updated**: Data is fetched in real-time from Calgary APIs

For questions about the data itself, please contact the City of Calgary Open Data team.

## 🎯 Roadmap

### Calgary-Specific Enhancements
- [ ] Historical building data trends
- [ ] Development permit integration
- [ ] Building permit tracking
- [ ] Demographic data overlay
- [ ] Transit accessibility analysis
- [ ] Climate and energy efficiency data

### Short Term
- [ ] Additional Calgary datasets (parking, permits, etc.)
- [ ] Enhanced spatial analysis tools
- [ ] Performance optimizations for large datasets
- [ ] Mobile-responsive 3D controls

### Long Term
- [ ] Other Canadian cities integration (Vancouver, Toronto)
- [ ] Machine learning for property value prediction
- [ ] Advanced urban planning analytics
- [ ] Integration with GTFS transit data

---

**Built with ❤️ for Calgary and urban data visualization**

*Using real data from Calgary's Open Data initiative to create meaningful urban insights.* 