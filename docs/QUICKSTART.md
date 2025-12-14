# TOR - Unveil: Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Docker Desktop installed and running
- Git (optional, for version control)

### Installation Steps

1. **Navigate to project directory**
   ```powershell
   cd e:\personalProjects\tor-unveil
   ```

2. **Start the application with Docker Compose**
   ```powershell
   docker-compose up -d
   ```

   This will:
   - Start PostgreSQL database
   - Build and start the FastAPI backend
   - Build and start the React frontend
   - Initialize the database with sample data

3. **Wait for services to be ready** (usually 30-60 seconds)

4. **Access the application**
   - Frontend Dashboard: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### First Run

1. Open http://localhost:3000 in your browser
2. The dashboard will automatically load sample relay data
3. Configure analysis parameters:
   - **Simulation Count**: Number of traffic simulations (default: 100)
   - **Top N Results**: Number of guard nodes to display (default: 10)
   - **Random Seed**: Seed for reproducibility (default: 42)
4. Click **"▶ Run Analysis"** to start the analysis
5. View results in the dashboard:
   - **Guard Node Table**: Ranked probable entry nodes
   - **Probability Chart**: Visual confidence scores
   - **Circuit Path Diagram**: Conceptual Tor path visualization

### Configuration Options

Edit the `.env` file to change configuration:

**Data Source Options:**
- `DATA_SOURCE=sample` - Use offline sample data (default)
- `DATA_SOURCE=live` - Fetch live data from Tor Onionoo API
- `DATA_SOURCE=both` - Try live, fallback to sample

### Stopping the Application

```powershell
docker-compose down
```

To stop and remove all data:
```powershell
docker-compose down -v
```

### Viewing Logs

```powershell
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Troubleshooting

**Services not starting:**
- Ensure Docker Desktop is running
- Check if ports 3000, 8000, 5432 are available
- Run: `docker-compose down -v` then `docker-compose up -d`

**Database connection errors:**
- Wait 30 seconds for PostgreSQL to initialize
- Check logs: `docker-compose logs postgres`

**No relays in database:**
- Click "Refresh Relay Data" button in the dashboard
- Check DATA_SOURCE setting in `.env`

**Frontend can't connect to backend:**
- Verify REACT_APP_API_URL in `.env` is `http://localhost:8000`
- Check backend is running: `docker-compose ps`

### Development Mode

**Backend development:**
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend development:**
```powershell
cd frontend
npm install
npm start
```

### API Endpoints

**Relays:**
- `POST /api/relays/refresh` - Refresh relay metadata
- `GET /api/relays/` - Get all relays
- `GET /api/relays/guards` - Get guard relays
- `GET /api/relays/stats` - Get relay statistics

**Analysis:**
- `POST /api/analysis/run` - Run traffic analysis
- `GET /api/analysis/{id}` - Get analysis result
- `GET /api/analysis/` - Get recent analyses

**Traffic:**
- `POST /api/traffic/generate` - Generate synthetic traffic
- `POST /api/traffic/generate-correlated` - Generate correlated patterns

### Architecture Overview

```
Frontend (React) → Backend API (FastAPI) → Database (PostgreSQL)
                         ↓
                   Tor Onionoo API
                   (optional, live mode)
```

**Modules:**
1. **Metadata Collector** - Fetches Tor relay data
2. **Traffic Generator** - Creates synthetic patterns
3. **Feature Extractor** - Extracts comparable features
4. **Correlation Engine** - DTW-based pattern matching
5. **Probability Scorer** - Ranks guard nodes
6. **Dashboard** - Visual analytics interface

### Sample Data

The application includes sample data for 8 Tor relays:
- 5 Guard nodes (moria1, tor26, dannenberg, maatuska, TorLand1)
- 2 Exit nodes (Unnamed, fiedlerRelay)
- 1 Middle node (zwiebelfreund)

### Next Steps

- Experiment with different simulation counts
- Try different random seeds for reproducibility
- Switch to live data mode for real Tor network analysis
- Review probability scores and correlation metrics
- Examine the API documentation at http://localhost:8000/docs

### Support

For issues or questions:
- Check application logs
- Review the main README.md
- Verify Docker containers are healthy: `docker-compose ps`

---

**⚠️ Ethical Use Reminder**

This tool is for research and educational purposes only. It:
- Uses only public Tor relay metadata
- Generates synthetic traffic (no real capture)
- Does not deanonymize users
- Does not perform attacks on the Tor network
