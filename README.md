# TOR - Unveil: Peel the Onion

A web-based analytical tool that ingests public Tor relay metadata and synthetic Tor-like traffic patterns, correlates them, and outputs a ranked list of probable Tor entry (guard) nodes with confidence scores.

## ⚠️ Ethical Disclaimer

This tool is designed for **research and educational purposes only**. It:
- Uses only **public Tor relay metadata**
- Generates **synthetic traffic patterns** (no real traffic capture)
- Does **not** connect to the live Tor network
- Does **not** perform user deanonymization
- Does **not** inspect real packets or perform cryptographic attacks

## Features

- 🌐 **Public Tor Relay Metadata Collection** - Fetches relay information from Tor Onionoo API
- 🔄 **Synthetic Traffic Generation** - Generates configurable Tor-like traffic patterns
- 🔗 **Correlation Engine** - Uses Dynamic Time Warping (DTW) for pattern matching
- 📊 **Probability Scoring** - Ranks probable guard nodes with confidence scores
- 📈 **Interactive Dashboard** - Visual analytics and explanatory visualizations
- 🔀 **Dual Data Mode** - Supports both sample data and live API data

## Architecture

```
┌─────────────────────┐
│ Tor Onionoo API     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Metadata Collector  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Relay Database      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Traffic Simulator   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Correlation Engine  │
│    (DTW-based)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Probability Scorer  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Visualization       │
│ Dashboard (React)   │
└─────────────────────┘
```

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **Frontend**: React + TypeScript, D3.js, Recharts
- **Database**: PostgreSQL
- **Containerization**: Docker, Docker Compose
- **Correlation**: Dynamic Time Warping (DTW)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tor-unveil
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Start the application:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Data Source Configuration

Edit `.env` to choose data source:

```env
# Use sample data (offline)
DATA_SOURCE=sample

# Use live Tor API data
DATA_SOURCE=live

# Use both (fetch live, fallback to sample)
DATA_SOURCE=both
```

## Usage

1. Open the dashboard at http://localhost:3000
2. Configure analysis parameters:
   - Number of simulations
   - Top-N guard nodes to display
   - Random seed for reproducibility
3. Click "Run Analysis"
4. View ranked probable entry nodes with:
   - Confidence scores
   - Relay metadata (country, bandwidth, uptime)
   - Probability distributions
   - Conceptual path diagrams

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Database Migrations

```bash
cd database/migrations
# Run migrations as needed
```

## Project Structure

```
tor-unveil/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── modules/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── database/
│   ├── migrations/
│   └── seeds/
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Modules

### Module 1: Tor Relay Metadata Collector
Fetches and stores public Tor relay information from Onionoo API.

### Module 2: Relay Metadata Store
Persists relay data with filtering capabilities (Guard/Exit/Middle nodes).

### Module 3: Synthetic Traffic Pattern Generator
Generates configurable Tor-like traffic patterns with randomization.

### Module 4: Traffic Feature Extractor
Converts traffic patterns into comparable feature vectors.

### Module 5: Correlation Engine
Measures similarity between entry and exit traffic using DTW.

### Module 6: Guard Node Probability Scorer
Estimates likelihood of each guard node being an entry point.

### Module 7: Visualization Dashboard
Interactive web interface with ranked results and visual explanations.

## License

MIT License - See LICENSE file for details

## Contributing

This is a research project. Contributions are welcome but must maintain ethical standards.

## Acknowledgments

- Tor Project for public relay metadata
- Research community for traffic analysis techniques
