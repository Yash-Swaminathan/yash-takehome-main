# Urban Design 3D City Dashboard with LLM Querying

A full-stack web application that visualizes Calgary building data in 3D and allows users to query buildings using natural language, powered by LLM integration.

## 🌟 Features

### Core Functionality
- **3D Building Visualization**: Interactive Three.js-based 3D city view of Calgary buildings
- **Natural Language Queries**: Ask questions like "buildings over 100 feet" or "commercial buildings"
- **Smart Building Filtering**: LLM-powered query interpretation with fallback rule-based parsing
- **Interactive Building Details**: Click any building to see detailed information
- **Project Persistence**: Save and load your map analyses for future reference

### Technical Highlights
- **Full-Stack Architecture**: Flask backend with React frontend
- **Real-time Data**: Fetches building data from Calgary Open Data API
- **3D Rendering**: Buildings rendered as extruded shapes based on actual footprint data
- **User Management**: Simple username-based identification system
- **Responsive Design**: Modern UI with glassmorphism design elements

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

# Copy environment template and configure
cp .env.example .env
# Edit .env file with your settings (see Configuration section)
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

### Environment Variables (.env)

Create a `.env` file in the backend directory:

```env
# Flask Configuration
FLASK_CONFIG=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///urban_dashboard.db

# Hugging Face LLM API (Optional - fallback parsing will be used without it)
HUGGINGFACE_API_KEY=your-huggingface-api-key-here

# Calgary Open Data API (No key required)
CALGARY_OPEN_DATA_BASE_URL=https://data.calgary.ca/resource

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://localhost:3000
```

### Getting Hugging Face API Key (Optional)

1. Sign up at [huggingface.co](https://huggingface.co)
2. Go to Settings → Access Tokens
3. Create a new token
4. Add it to your `.env` file

**Note**: The application works without the Hugging Face API key using rule-based query parsing.

## 📊 Data Sources

### Calgary Open Data
The application fetches building data from Calgary's Open Data portal:
- **Building Footprints**: Geometric shapes of buildings
- **Property Assessments**: Building values and characteristics
- **Zoning Data**: Land use classifications

### Sample Data
When the Calgary API is unavailable, the application uses sample data representing downtown Calgary buildings.

## 🎮 How to Use

### 1. User Login
- Enter any username to identify yourself
- No password required for this demo

### 2. Explore Buildings
- **Navigate**: Drag to rotate, scroll to zoom, right-click to pan
- **Select Buildings**: Click any building to see details
- **Building Colors**: Different types have different colors:
  - 🔵 Blue: Commercial
  - 🟢 Green: Residential  
  - 🟣 Purple: Industrial
  - 🟠 Orange: Mixed Use
  - ⚪ Gray: Unknown/Other

### 3. Query Buildings
Use natural language to filter buildings:

**Height Queries:**
- "buildings over 100 feet"
- "buildings taller than 50 meters"
- "buildings under 200 feet"

**Type Queries:**
- "commercial buildings"
- "residential buildings" 
- "mixed use buildings"

**Value Queries:**
- "buildings worth more than $1,000,000"
- "buildings valued under $500,000"

**Zoning Queries:**
- "RC-G zoning"
- "CC-X buildings"

### 4. Save & Load Projects
- Apply filters to buildings
- Click "Projects" → "Save Current Analysis"
- Give your project a name and description
- Load saved projects anytime to restore filters

## 🔧 API Endpoints

### Building Data
- `GET /api/buildings/area?bounds=lat1,lng1,lat2,lng2` - Get buildings in area
- `GET /api/buildings/{id}` - Get building details
- `POST /api/buildings/filter` - Filter buildings
- `POST /api/buildings/refresh` - Refresh data from Calgary API

### LLM Query Processing
- `POST /api/query/process` - Process natural language query
- `GET /api/query/suggestions` - Get query examples
- `POST /api/query/validate` - Validate filter format

### Project Management
- `POST /api/projects/save` - Save project
- `GET /api/projects/user/{user_id}` - Get user projects
- `POST /api/projects/{id}/load` - Load project
- `DELETE /api/projects/{id}` - Delete project

### User Management
- `POST /api/users/login` - User login/registration
- `GET /api/users/{id}` - Get user info

## 🚀 Deployment

### Backend Deployment (Heroku)

1. Create `Procfile`:
```
web: gunicorn run:app
```

2. Deploy:
```bash
heroku create your-app-name
heroku config:set FLASK_CONFIG=production
heroku config:set SECRET_KEY=your-production-secret
# Add other environment variables
git push heroku main
```

### Frontend Deployment (Vercel)

1. Add build script to `package.json`:
```json
{
  "scripts": {
    "build": "react-scripts build"
  }
}
```

2. Set environment variable:
```bash
REACT_APP_API_URL=https://your-backend-app.herokuapp.com/api
```

3. Deploy to Vercel:
```bash
npm install -g vercel
vercel --prod
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🛠️ Development

### Code Structure
- **Models**: SQLAlchemy models with relationships
- **Services**: Business logic separated from routes
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Type Safety**: Type hints in Python, PropTypes in React
- **Code Quality**: ESLint, Prettier, and Python formatting

### Adding New Features

1. **New Query Types**: Add patterns to `LLMService._fallback_query_parsing()`
2. **New Building Properties**: Add fields to `Building` model and update processors
3. **New Visualizations**: Extend `Building.js` component in Three.js
4. **New Data Sources**: Add fetchers in `DataFetcher` service

## 📋 System Requirements

### Minimum
- Python 3.8+
- Node.js 16+
- 4GB RAM
- Modern browser with WebGL support

### Recommended
- Python 3.10+
- Node.js 18+
- 8GB RAM
- Chrome/Firefox/Safari latest versions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**3D Scene Not Loading**
- Check browser WebGL support
- Update graphics drivers
- Try in a different browser

**API Errors**
- Check backend is running on port 5000
- Verify environment variables
- Check Calgary Open Data API status

**Slow Performance**
- Reduce building count by narrowing geographic bounds
- Close other browser tabs
- Check system resources

### Support
For issues and questions:
1. Check the troubleshooting section
2. Review API documentation
3. Open an issue on GitHub

## 🎯 Roadmap

### Short Term
- [ ] Real-time collaboration features
- [ ] Additional data sources (Vancouver, Toronto)
- [ ] Enhanced mobile support
- [ ] Performance optimizations

### Long Term
- [ ] Machine learning for building type prediction
- [ ] Virtual reality support
- [ ] Advanced spatial analysis tools
- [ ] Integration with urban planning software

---

**Built with ❤️ for urban design and data visualization** 