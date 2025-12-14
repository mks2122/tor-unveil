# TOR - Unveil: Technical Architecture

## System Overview

TOR - Unveil is a modular web-based analytical tool that correlates public Tor relay metadata with synthetic traffic patterns to identify probable guard nodes. The system is fully containerized and uses no real network traffic.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │          React Dashboard (TypeScript)               │    │
│  │  - Dashboard Component                              │    │
│  │  - GuardNodeTable Component                         │    │
│  │  - ProbabilityChart Component (Recharts)            │    │
│  │  - PathDiagram Component (D3.js)                    │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │ HTTP/REST API                        │
└──────────────────────┼──────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────┐
│                      ▼         Backend Layer                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │              FastAPI Application                    │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │         API Routes                        │     │    │
│  │  │  /api/relays    /api/traffic    /api/analysis  │    │
│  │  └──────────────────────────────────────────┘     │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │         Services Layer                    │     │    │
│  │  │  - RelayService                           │     │    │
│  │  │  - AnalysisService                        │     │    │
│  │  └──────────────────────────────────────────┘     │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │         Core Modules                      │     │    │
│  │  │  1. MetadataCollector                     │     │    │
│  │  │  2. TrafficGenerator                      │     │    │
│  │  │  3. FeatureExtractor                      │     │    │
│  │  │  4. CorrelationEngine (DTW)               │     │    │
│  │  │  5. ProbabilityScorer                     │     │    │
│  │  └──────────────────────────────────────────┘     │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │         Data Models (SQLAlchemy)          │     │    │
│  │  │  - Relay                                  │     │    │
│  │  │  - TrafficPattern                         │     │    │
│  │  │  - AnalysisResult                         │     │    │
│  │  └──────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────┘    │
│                       │                                      │
│                       │ SQLAlchemy ORM                       │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │            PostgreSQL Database                      │    │
│  │  Tables: relays, traffic_patterns, analysis_results│    │
│  └────────────────────────────────────────────────────┘    │
│                       ▲                                      │
│                       │ Optional: Live Data                  │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        │ HTTPS
                        ▼
            ┌───────────────────────┐
            │ Tor Onionoo API       │
            │ (onionoo.torproject.org)│
            └───────────────────────┘
```

## Component Details

### 1. Frontend (React + TypeScript)

**Location:** `/frontend/src/`

**Key Components:**
- **Dashboard.tsx**: Main orchestrator component
- **GuardNodeTable.tsx**: Displays ranked guard nodes
- **ProbabilityChart.tsx**: Recharts-based visualizations
- **PathDiagram.tsx**: D3.js circuit path visualization

**API Integration:**
- **api.ts**: Axios-based API client with typed interfaces

**Styling:**
- Custom CSS with gradient themes
- Responsive design for mobile/desktop
- Material design principles

### 2. Backend (Python 3.10+ FastAPI)

**Location:** `/backend/app/`

#### API Routes

**Relay Routes** (`/api/relays`)
- `POST /refresh` - Refresh relay metadata
- `GET /` - Get all relays (filterable)
- `GET /guards` - Get guard relays
- `GET /stats` - Get relay statistics
- `GET /{fingerprint}` - Get specific relay

**Traffic Routes** (`/api/traffic`)
- `POST /generate` - Generate synthetic pattern
- `POST /generate-correlated` - Generate correlated entry/exit patterns

**Analysis Routes** (`/api/analysis`)
- `POST /run` - Execute full analysis
- `GET /{id}` - Get analysis result
- `GET /` - Get recent analyses

#### Core Modules

**MetadataCollector** (`modules/metadata_collector.py`)
- Fetches relay data from Tor Onionoo API
- Parses and structures relay metadata
- Supports filtering by relay type (Guard/Exit/Middle)

**TrafficGenerator** (`modules/traffic_generator.py`)
- Generates synthetic Tor-like traffic bursts
- Seed-based randomization for reproducibility
- Creates correlated entry/exit patterns with configurable jitter

**FeatureExtractor** (`modules/feature_extractor.py`)
- Extracts timing features (inter-packet delays)
- Calculates burst characteristics
- Creates normalized feature vectors for comparison

**CorrelationEngine** (`modules/correlation_engine.py`)
- DTW (Dynamic Time Warping) for time-series similarity
- Cosine similarity for feature vectors
- Euclidean distance-based similarity
- Weighted combination of metrics

**ProbabilityScorer** (`modules/probability_scorer.py`)
- Combines similarity scores with relay metadata
- Weights: similarity (60%), bandwidth (20%), uptime (10%), consensus (10%)
- Produces ranked list with confidence percentages

#### Services Layer

**RelayService** (`services/relay_service.py`)
- Manages relay data CRUD operations
- Handles sample vs live data loading
- Provides filtering and statistics

**AnalysisService** (`services/analysis_service.py`)
- Orchestrates complete analysis workflow
- Manages traffic generation and correlation
- Stores results in database

### 3. Database (PostgreSQL)

**Tables:**

**relays**
- Stores Tor relay metadata
- Fields: fingerprint, nickname, flags, bandwidth, uptime, country, etc.
- Indexed on: fingerprint, relay_type, country

**traffic_patterns**
- Stores generated traffic patterns
- Fields: pattern_id, timestamps, packet_sizes, features
- Used for analysis history

**analysis_results**
- Stores completed analysis results
- Fields: analysis_id, ranked_guards, statistics, configuration
- Queryable analysis history

### 4. External Dependencies

**Tor Onionoo API** (Optional)
- Public Tor relay directory API
- Endpoint: https://onionoo.torproject.org/details
- Used only in "live" or "both" data modes
- No authentication required

## Data Flow

### Analysis Workflow

1. **User Trigger**
   - User configures parameters in Dashboard
   - Clicks "Run Analysis"

2. **Relay Retrieval**
   - Backend fetches guard relays from database
   - If empty, loads sample data or fetches from Onionoo API

3. **Traffic Generation**
   - TrafficGenerator creates synthetic entry/exit patterns
   - Configurable bursts, delays, and jitter
   - Patterns are correlated to simulate real circuits

4. **Feature Extraction**
   - FeatureExtractor processes patterns
   - Extracts timing, burst, and volume features
   - Creates comparable feature vectors

5. **Correlation**
   - CorrelationEngine computes similarity scores
   - Uses DTW for time-series comparison
   - Combines multiple similarity metrics

6. **Scoring & Ranking**
   - ProbabilityScorer weighs similarity with relay metadata
   - Produces confidence scores (0-100%)
   - Ranks guards by probability

7. **Results Storage**
   - AnalysisResult stored in database
   - Generates unique analysis ID
   - Tracks execution time and statistics

8. **Visualization**
   - Frontend receives ranked results
   - Displays in table, charts, and diagrams
   - Shows confidence scores and explanations

## Configuration

### Environment Variables

**Database:**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

**Backend:**
- `BACKEND_HOST`, `BACKEND_PORT`, `DEBUG`

**Data Source:**
- `DATA_SOURCE`: `sample` | `live` | `both`

**Analysis:**
- `DEFAULT_TOP_N`, `DEFAULT_SIMULATION_COUNT`, `DEFAULT_RANDOM_SEED`

**Frontend:**
- `REACT_APP_API_URL`

## Docker Architecture

### Services

1. **postgres** - PostgreSQL 15 database
2. **backend** - Python FastAPI application
3. **frontend** - React development server (production: nginx)

### Volumes

- `postgres_data` - Persistent database storage
- Backend and frontend source code mounted for development

### Networks

- `tor-unveil-network` - Bridge network for inter-service communication

### Health Checks

- PostgreSQL health check ensures database ready before backend starts
- Backend depends on healthy postgres

## Security Considerations

### What This Tool Does NOT Do

❌ Capture real network traffic
❌ Connect to live Tor network
❌ Perform packet inspection
❌ Attempt cryptographic attacks
❌ Deanonymize Tor users
❌ Store personal data

### What This Tool DOES Do

✅ Uses public relay metadata only
✅ Generates synthetic traffic patterns
✅ Performs statistical analysis
✅ Educational demonstration
✅ Research purposes only

### Data Privacy

- No real IP addresses stored
- No user traffic analyzed
- All traffic patterns are synthetic
- Relay data is public information

## Performance

### Expected Performance

- **Relay Metadata Fetch**: 5-10 seconds (live mode)
- **Sample Data Load**: < 1 second
- **Traffic Generation**: < 1 second per 100 simulations
- **Analysis Execution**: 10-30 seconds for 100 simulations
- **Database Queries**: < 100ms

### Scalability

- Current design: Single-node deployment
- Database can handle 10,000+ relays
- Analysis limited by CPU for DTW calculations
- Frontend handles up to 50 ranked results efficiently

### Optimization Opportunities

- Parallel traffic generation
- Cached correlation results
- Pre-computed feature vectors
- Materialized views for relay statistics

## Technology Stack Summary

**Frontend:**
- React 18.2
- TypeScript 4.9
- D3.js 7.8 (visualizations)
- Recharts 2.10 (charts)
- Axios 1.6 (HTTP client)

**Backend:**
- Python 3.10+
- FastAPI 0.104
- SQLAlchemy 2.0
- Pandas 2.1
- NumPy 1.26
- FastDTW 0.3

**Database:**
- PostgreSQL 15

**DevOps:**
- Docker
- Docker Compose

## Development Workflow

1. **Local Development**: Mount source volumes, use hot reload
2. **Testing**: Run unit tests for modules
3. **Production Build**: Use multi-stage Docker builds
4. **Deployment**: Docker Compose or Kubernetes

## Extension Points

### Adding New Correlation Algorithms

Implement in `CorrelationEngine` class:
```python
def new_similarity_method(self, entry, exit):
    # Your algorithm here
    return similarity_score
```

### Adding New Relay Filters

Extend `RelayService`:
```python
def get_relays_by_custom_criteria(self, criteria):
    return self.db.query(Relay).filter(...).all()
```

### Custom Scoring Weights

Modify `ProbabilityScorer` initialization:
```python
scorer = ProbabilityScorer(
    similarity_weight=0.7,
    bandwidth_weight=0.3,
    ...
)
```

## Maintenance

### Regular Tasks

- Update sample relay data quarterly
- Monitor Onionoo API changes
- Update dependencies for security patches
- Review and optimize database indices

### Monitoring

- Check Docker container health: `docker-compose ps`
- View logs: `docker-compose logs -f`
- Database connections: PostgreSQL monitoring tools
- API response times: FastAPI `/docs` built-in metrics

## Troubleshooting

See [QUICKSTART.md](./QUICKSTART.md) for common issues and solutions.

## License

MIT License - See LICENSE file
