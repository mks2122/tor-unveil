# TOR - Unveil: Peel the Onion

TOR - Unveil is a containerized research and educational tool that ingests **public Tor relay metadata** (Onionoo API or provided samples), generates **synthetic Tor-like entry/exit traffic**, correlates patterns via **Dynamic Time Warping (DTW)** and complementary metrics, and produces a **ranked list of probable guard (entry) nodes with confidence scores**. The project contains a FastAPI backend, a React + TypeScript dashboard, and PostgreSQL storage orchestrated with Docker Compose.

## ⚠️ Ethical Boundaries (What This Project Does and Does NOT Do)

- ✅ Uses **public relay metadata only** (no private data).
- ✅ Generates **synthetic** traffic; **never** captures real packets.
- ✅ Provides analytics and visualizations for **education and research**.
- ❌ Does **not** deanonymize Tor users or connect to live Tor circuits.
- ❌ Does **not** inspect real packets or attempt cryptographic/network attacks.
- ❌ Stores no personal data. See `docs/ARCHITECTURE.md` and `docs/TROUBLESHOOTING.md` for further context.

---

## Table of Contents
- [What the project does](#tor---unveil-peel-the-onion)
- [Repository map (every file & directory)](#repository-map-every-file--directory)
- [Runtime services & Docker Compose](#runtime-services--docker-compose)
- [Configuration & environment variables](#configuration--environment-variables)
- [Backend (FastAPI) anatomy](#backend-fastapi-anatomy)
- [API surface](#api-surface)
- [Frontend (React + TypeScript) anatomy](#frontend-react--typescript-anatomy)
- [Data & storage](#data--storage)
- [How analysis works (end-to-end pipeline)](#how-analysis-works-end-to-end-pipeline)
- [Local development & commands](#local-development--commands)
- [Testing/verification status](#testingverification-status)
- [Additional documentation](#additional-documentation)
- [License & contributing](#license--contributing)

---

## Repository Map (every file & directory)

| Path | Purpose |
| --- | --- |
| `docker-compose.yml` | Defines services: `postgres`, `backend` (FastAPI), `frontend` (React). Ports 5432/8000/3000; mounts volumes and health checks. |
| `start.bat` / `stop.bat` | Windows helpers to build/up/down containers, wait for readiness, and open the dashboard. |
| `.env.example` | Complete environment template for backend, database, and frontend (`REACT_APP_API_URL`). |
| `DEPLOYMENT_SUCCESS.md` | Deployment runbook + status snapshot describing resolved issues and management commands. |
| `docs/` | In-depth docs: `ARCHITECTURE.md`, `IMPLEMENTATION_SUMMARY.md`, `TECHNOLOGIES.md`, `COMMANDS.md`, `QUICKSTART.md`, `TROUBLESHOOTING.md`. |
| `database/migrations/init.sql` | Placeholder enabling `uuid-ossp`; SQLAlchemy normally creates tables. |
| `database/seeds/sample_relays.json` | Sample relay dataset (guards/exits/middles) with bandwidth, uptime, geo, probabilities. |
| `backend/` | FastAPI app, core analysis modules, SQLAlchemy models, requirements, Dockerfile. |
| `frontend/` | React + TypeScript dashboard, components, services, Dockerfile, CSS assets. |
| `LICENSE` | MIT license. |
| `README.md` | This document. |

---

## Runtime Services & Docker Compose

- **postgres** (`postgres:15-alpine`)  
  - Env: `DB_NAME`, `DB_USER`, `DB_PASSWORD` (defaults from `.env.example`).  
  - Ports: `5432:5432`.  
  - Volumes: `postgres_data` → `/var/lib/postgresql/data`, `./database/migrations` → `/docker-entrypoint-initdb.d` (auto-runs `init.sql`).  
  - Healthcheck: `pg_isready`.
- **backend** (FastAPI)  
  - Built from `backend/Dockerfile`; command `uvicorn app.main:app --reload`.  
  - Env: database settings, `DATA_SOURCE` (`sample|live|both`), `TOR_ONIONOO_API`, analysis defaults.  
  - Ports: `8000:8000`. Volumes: `./backend:/app`, `./database:/database`.
- **frontend** (React dev server)  
  - Built from `frontend/Dockerfile`; command `npm start`.  
  - Env: `REACT_APP_API_URL` (defaults to `http://localhost:8000`).  
  - Ports: `3000:3000`; mounts source with `node_modules` kept in-container.
- **Network/volumes**: bridge network `tor-unveil-network`; volume `postgres_data`.

Quick commands:
```bash
docker-compose up -d        # start all services
docker-compose down         # stop (add -v to drop volumes)
docker-compose logs -f      # tail logs
```
Windows shortcuts: `start.bat` (builds, starts, opens dashboard) and `stop.bat` (compose down).

---

## Configuration & Environment Variables

Backed by `pydantic_settings.BaseSettings` in `backend/app/config.py` and `.env.example`:

| Variable | Default | Where used |
| --- | --- | --- |
| `DB_HOST` | `postgres` | `config.Settings.DATABASE_URL` -> SQLAlchemy engine |
| `DB_PORT` | `5432` | Database connection |
| `DB_NAME` | `tor_unveil` | Database name |
| `DB_USER` | `tor_user` | Database user |
| `DB_PASSWORD` | `tor_password` | Database password |
| `BACKEND_HOST` | `0.0.0.0` | Uvicorn host |
| `BACKEND_PORT` | `8000` | Uvicorn port |
| `DEBUG` | `True` | FastAPI debug toggle |
| `DATA_SOURCE` | `sample` | Relay loading mode: `sample`, `live`, or `both` |
| `TOR_ONIONOO_API` | `https://onionoo.torproject.org` | Metadata collector endpoint base |
| `DEFAULT_TOP_N` | `10` | Default guard ranking length |
| `DEFAULT_SIMULATION_COUNT` | `100` | Default simulations |
| `DEFAULT_RANDOM_SEED` | `42` | Deterministic random seed |
| `REACT_APP_API_URL` | `http://localhost:8000` | Frontend Axios base URL (`frontend/src/services/api.ts`) |

To configure: copy `.env.example` → `.env`, adjust values, restart containers.

---

## Backend (FastAPI) Anatomy

### Entry & infrastructure
- `app/main.py`: creates `FastAPI` app, applies permissive CORS, creates tables (`Base.metadata.create_all`), mounts routers (`/api/relays`, `/api/traffic`, `/api/analysis`), and exposes `GET /` (metadata) + `GET /health`.
- `app/config.py`: `Settings` class with all environment-backed fields plus `DATABASE_URL` property.
- `app/database.py`: SQLAlchemy engine/session (`SessionLocal`), declarative `Base`, and dependency `get_db()` generator.

### Data models (SQLAlchemy)
- `models/relay.py` (`relays` table): `fingerprint` (unique), `nickname`, flags (`is_guard`, `is_exit`, `is_middle`), `relay_type`, bandwidth/uptime/country/geo, OR addresses, exit policy, `first_seen`, `last_seen`, probabilities, `consensus_weight`, `data_source`, timestamps.
- `models/traffic_pattern.py` (`traffic_patterns`): `pattern_id`, `pattern_type` (`entry|exit`), raw `timestamps`/`packet_sizes`, derived `feature_vector`, burst/volume stats, `generation_params`, `random_seed`, timestamps.
- `models/analysis_result.py` (`analysis_results`): `analysis_id`, configuration (`top_n`, `simulation_count`, `random_seed`), `ranked_guards`, `correlation_scores`, counts, `avg_confidence_score`, `execution_time_seconds`, timestamps.

### Core modules (algorithms)
- `modules/metadata_collector.py` (`MetadataCollector`):
  - `fetch_all_relays()`, `fetch_guard_relays()`, `fetch_exit_relays()` -> Onionoo `/details` with optional flag filters.
  - `parse_relay_data()` -> normalizes flags, relay type, uptime, geo, probabilities.
  - `fetch_and_parse_relays(relay_type)` -> orchestrates fetch + parse.
- `modules/traffic_generator.py` (`TrafficGenerator`, seed-aware):
  - `generate_burst()`, `generate_pattern()`, `generate_entry_pattern()`, `generate_exit_pattern()`.
  - `generate_correlated_patterns(num_bursts, time_jitter)` -> entry/exit pair with jittered timestamps.
- `modules/feature_extractor.py` (`FeatureExtractor`):
  - `extract_features(pattern)` -> inter-packet delays, burst detection, stats, feature_vector.
  - `normalize_features(features)` -> min-max normalization.
  - `extract_timestamp_series(pattern)` -> inter-packet delays as ndarray.
- `modules/correlation_engine.py` (`CorrelationEngine`):
  - `dtw_similarity(entry_series, exit_series)` (fastdtw + euclidean).
  - `vector_similarity(entry_features, exit_features)` (cosine).
  - `euclidean_similarity(entry_features, exit_features)` (inverse exponential).
  - `correlation_score(entry_pattern, exit_pattern, entry_features, exit_features, weights)` -> weighted overall + detailed scores.
  - `batch_correlate(entry_pattern, exit_patterns, entry_features, exit_features_list)`.
- `modules/probability_scorer.py` (`ProbabilityScorer`):
  - Weighted constructor (default weights normalize to similarity 0.6, bandwidth 0.2, uptime 0.1, consensus 0.1).
  - `normalize_value()`, `calculate_relay_score(similarity_score, relay_metadata, all_relays_metadata)`.
  - `rank_guards(guard_relays, similarity_scores, top_n)` -> adds probability/confidence, component weights.
  - `calculate_statistics(ranked_results)` -> count, avg/max/min/std/median confidence.

### Services (business logic)
- `services/relay_service.py` (`RelayService`):
  - `load_sample_data()` reads `database/seeds/sample_relays.json` using multiple fallback paths; inserts with `data_source="sample"`.
  - `fetch_live_data(relay_type=None)` uses `MetadataCollector`, upserts relays, marks `data_source="live"`.
  - `refresh_relays()` respects `DATA_SOURCE` (`sample`, `live`, `both` with live-first fallback).
  - Query helpers: `get_all_relays()`, `get_guard_relays()`, `get_exit_relays()`, `get_relay_by_fingerprint()`, `get_relays_by_country()`, `get_relay_count()`.
- `services/analysis_service.py` (`AnalysisService`):
  - `run_analysis(simulation_count, top_n, random_seed)` pipeline:
    1) fetch guard relays (refresh if empty), 2) generate correlated entry/exit patterns (looping up to `simulation_count`), 3) extract features, 4) correlate via `CorrelationEngine`, 5) aggregate similarity per fingerprint, 6) rank via `ProbabilityScorer`, 7) compute statistics, 8) persist `AnalysisResult`, 9) return shaped response with execution time.
  - `get_analysis_result(analysis_id)` -> returns stored result with configuration and timestamps.
  - `get_recent_analyses(limit)` -> newest analyses summary.

### API routes (FastAPI routers)
- `routes/relays.py` (`/api/relays`):
  - `POST /refresh` -> trigger relay load; returns count & source.
  - `GET /` -> list relays (filters: `relay_type`, `country`, `limit`).
  - `GET /stats` -> totals by type.
  - `GET /guards` -> guard-only list (limit).
  - `GET /{fingerprint}` -> single relay or 404.
- `routes/traffic.py` (`/api/traffic`):
  - `POST /generate` body `{num_bursts, random_seed, pattern_type}` -> returns pattern + extracted features.
  - `POST /generate-correlated` query params `{num_bursts, random_seed, time_jitter}` -> paired entry/exit with features.
- `routes/analysis.py` (`/api/analysis`):
  - `POST /run` body `{simulation_count, top_n, random_seed}` -> orchestrates full analysis (returns `analysis_id`, `ranked_guards`, `statistics`, `configuration`, `execution_time`).
  - `GET /{analysis_id}` -> fetch stored result or 404.
  - `GET /` -> recent analyses (limit).

### Backend dependencies & container
- `backend/requirements.txt`: FastAPI, Uvicorn, SQLAlchemy, psycopg2-binary, alembic, pydantic/settings, python-dotenv, requests, aiohttp, pandas, numpy, scipy, fastdtw, python-multipart.
- `backend/Dockerfile`: Python 3.10 slim, installs gcc + `postgresql-client`, installs requirements, copies app, exposes 8000, runs Uvicorn.

---

## API Surface

FastAPI automatically documents endpoints at `http://localhost:8000/docs`. Summary:

| Method & Path | Request model/body | Response highlights |
| --- | --- | --- |
| `GET /` | – | API metadata + docs link |
| `GET /health` | – | `{status:"healthy"}` |
| `POST /api/relays/refresh` | none | message, count, source |
| `GET /api/relays` | query: `relay_type?`, `country?`, `limit` | List of relays (pydantic `RelayResponse`) |
| `GET /api/relays/stats` | – | `{total, guard, exit, middle}` |
| `GET /api/relays/guards` | `limit` | guard list |
| `GET /api/relays/{fingerprint}` | path fingerprint | single relay or 404 |
| `POST /api/traffic/generate` | JSON `{num_bursts, random_seed, pattern_type}` | `{pattern, features}` |
| `POST /api/traffic/generate-correlated` | query `{num_bursts, random_seed, time_jitter}` | `{entry:{pattern,features}, exit:{pattern,features}}` |
| `POST /api/analysis/run` | JSON `{simulation_count, top_n, random_seed}` | `{analysis_id, ranked_guards[], statistics, configuration, execution_time}` |
| `GET /api/analysis/{analysis_id}` | path `analysis_id` | stored result or 404 |
| `GET /api/analysis` | query `limit` | recent analyses list |

Data contracts are also typed on the frontend in `frontend/src/services/api.ts`.

---

## Frontend (React + TypeScript) Anatomy

### Entry & bootstrapping
- `src/index.tsx`: mounts `<App />` into `public/index.html`; imports `index.css`.
- `src/App.tsx`: wraps `<Dashboard />`; imports `App.css`.

### Components (UI + logic)
- `components/Dashboard.tsx`: main orchestrator. Manages state for analysis config/results, relay stats, loading/error flags. Calls API helpers (`runAnalysis`, `getRelayStats`, `refreshRelays`). Renders controls, stats tiles, error messages, results, and empty-state guidance.
- `components/GuardNodeTable.tsx`: renders ranked guard table with confidence bars, similarity %, country, bandwidth (formatted), uptime (days).
- `components/ProbabilityChart.tsx`: Recharts bar chart comparing confidence vs similarity; uses palette cycling.
- `components/PathDiagram.tsx`: D3 conceptual Tor circuit (User→Guard→Middle→Exit) with arrows and captions.

### API client & types
- `services/api.ts`: Axios instance (`API_URL` from `REACT_APP_API_URL`), typed interfaces:
  - `AnalysisRequest`, `AnalysisResult`, `GuardNode`, `RelayStats`.
  - Functions: `runAnalysis`, `getRelayStats`, `refreshRelays`, `getRecentAnalyses`.

### Styling & assets
- `index.css`, `App.css`: layout, gradients, tables, cards, buttons, responsive adjustments.
- `public/index.html`: CRA template. `react-app-env.d.ts`, `tsconfig.json`, `package.json` scripts (`start`, `build`, `test`, `eject`).

### Frontend container
- `frontend/Dockerfile`: Node 18 alpine, installs dependencies, exposes 3000, runs `npm start`.

---

## Data & Storage

- **Database tables** (created via SQLAlchemy `Base.metadata.create_all`):
  - `relays`: all relay metadata with flags, geo, weights, probabilities, source, timestamps.
  - `traffic_patterns`: generated patterns with timestamps, packet sizes, features, generation params.
  - `analysis_results`: persisted analysis outputs, scores, statistics, execution time.
- **Seeds**: `database/seeds/sample_relays.json` contains guard, exit, middle examples with `fingerprint`, `nickname`, flags, `relay_type`, `bandwidth`, `uptime`, geo fields, OR addresses, exit policies, `first_seen`/`last_seen`, `consensus_weight`, and guard/middle/exit probabilities.
- **Migrations**: `database/migrations/init.sql` (extension enablement); Alembic is available in dependencies for future migrations.

---

## How Analysis Works (end-to-end pipeline)

1. **Relay acquisition** (`RelayService.refresh_relays`): load from sample JSON or fetch live Onionoo data (live-first fallback when `both`).
2. **Simulation loop** (`AnalysisService.run_analysis`):
   - Instantiate `TrafficGenerator` with `random_seed`.
   - For each simulation: `generate_correlated_patterns` → `FeatureExtractor.extract_features` for entry/exit.
   - `CorrelationEngine.correlation_score` computes DTW + cosine + euclidean similarities; aggregate per guard fingerprint.
3. **Scoring** (`ProbabilityScorer.rank_guards`): normalize bandwidth/uptime/consensus across guards, weight with similarity, emit probability + confidence.
4. **Statistics**: avg/max/min/std/median confidence, guards analyzed, execution time.
5. **Persistence**: store `AnalysisResult` row; return response to client.
6. **Visualization**: frontend tables + charts display ranked guards, statistics, and circuit diagram.

---

## Local Development & Commands

### Docker (recommended)
```bash
cp .env.example .env
docker-compose up -d          # build + start postgres, backend, frontend
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000 (docs at /docs)
```
Stop/clean:
```bash
docker-compose down           # stop
docker-compose down -v        # stop + remove data
```

### Backend only (hot reload)
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend only (CRA dev server)
```bash
cd frontend
npm install
npm start   # opens at http://localhost:3000
```

### Database access (from container)
```bash
docker-compose exec tor-unveil-postgres psql -U ${DB_USER:-tor_user} -d ${DB_NAME:-tor_unveil}
# (Service name alias also works: `docker-compose exec postgres ...`)
```

---

## Testing/Verification Status

- No automated tests are present in the repository today (no `tests/` suites in backend or frontend).  
- Manual verification: start stack, click **Refresh Relay Data**, then **Run Analysis** with defaults and observe ranked guards, stats, and charts. FastAPI docs at `/docs` allow exercising each endpoint.

---

## Additional Documentation

- `docs/ARCHITECTURE.md`: detailed system diagram, module explanations, performance notes, security boundaries.  
- `docs/IMPLEMENTATION_SUMMARY.md`: implementation highlights.  
- `docs/TECHNOLOGIES.md`: stack versions and rationale.  
- `docs/COMMANDS.md`: operational commands.  
- `docs/QUICKSTART.md`: abbreviated setup.  
- `docs/TROUBLESHOOTING.md`: common issues.  
- `DEPLOYMENT_SUCCESS.md`: deployment health summary and resolved issues.  
- `LICENSE`: MIT. `CONTRIBUTING` guidance is in this README; follow ethical constraints above.

---

## License & Contributing

- **License**: MIT (see `LICENSE`).
- **Contributing**: Research-focused contributions welcome. Preserve ethical boundaries (no deanonymization attempts, no real-traffic capture) and keep changes minimal/safe. Use sample data or public Onionoo sources only.
