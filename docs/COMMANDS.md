# TOR - Unveil: Command Reference

Quick reference for all commonly used commands.

## 🚀 Starting & Stopping

### Start Application
```powershell
# Option 1: Windows batch script (easiest)
.\start.bat

# Option 2: Docker Compose
docker-compose up -d

# Option 3: With rebuild
docker-compose up -d --build

# Option 4: View logs while starting
docker-compose up
```

### Stop Application
```powershell
# Option 1: Windows batch script
.\stop.bat

# Option 2: Docker Compose (preserves data)
docker-compose down

# Option 3: Remove volumes (deletes all data)
docker-compose down -v

# Option 4: Remove images too
docker-compose down --rmi all -v
```

### Restart Services
```powershell
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
docker-compose restart postgres
```

## 📊 Service Management

### Check Service Status
```powershell
# All services
docker-compose ps

# Detailed status
docker ps -a

# Check if services are healthy
docker-compose ps | findstr healthy
```

### View Logs
```powershell
# All services (follow mode)
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Last 50 lines
docker-compose logs --tail=50 backend

# Since specific time
docker-compose logs --since 5m backend
```

### Resource Monitoring
```powershell
# Live resource usage
docker stats

# Specific container
docker stats tor-unveil-backend

# No streaming (one-time)
docker stats --no-stream
```

## 🔧 Development Commands

### Backend Development

#### Enter Backend Container
```powershell
docker-compose exec backend /bin/bash
```

#### Run Python Commands
```powershell
# Check Python version
docker-compose exec backend python --version

# Install new package
docker-compose exec backend pip install package-name

# List installed packages
docker-compose exec backend pip list

# Run Python script
docker-compose exec backend python -m app.main
```

#### Backend Rebuild
```powershell
# Rebuild backend only
docker-compose build backend

# Force rebuild (no cache)
docker-compose build --no-cache backend

# Rebuild and restart
docker-compose up -d --build backend
```

### Frontend Development

#### Enter Frontend Container
```powershell
docker-compose exec frontend /bin/sh
```

#### Run NPM Commands
```powershell
# Check Node version
docker-compose exec frontend node --version

# Install new package
docker-compose exec frontend npm install package-name

# List installed packages
docker-compose exec frontend npm list

# Run build
docker-compose exec frontend npm run build
```

#### Frontend Rebuild
```powershell
# Rebuild frontend only
docker-compose build frontend

# Force rebuild (no cache)
docker-compose build --no-cache frontend

# Rebuild and restart
docker-compose up -d --build frontend
```

## 🗄️ Database Commands

### Access Database
```powershell
# Connect to PostgreSQL
docker-compose exec postgres psql -U tor_user -d tor_unveil

# One-line query
docker-compose exec postgres psql -U tor_user -d tor_unveil -c "SELECT COUNT(*) FROM relays;"
```

### PostgreSQL Commands (Inside psql)
```sql
-- List all tables
\dt

-- Describe table structure
\d relays

-- Count relays
SELECT COUNT(*) FROM relays;

-- Count by type
SELECT relay_type, COUNT(*) FROM relays GROUP BY relay_type;

-- View sample relays
SELECT fingerprint, nickname, relay_type, country FROM relays LIMIT 5;

-- Clear all data
TRUNCATE relays, traffic_patterns, analysis_results CASCADE;

-- Exit psql
\q
```

### Database Backup & Restore
```powershell
# Backup database
docker-compose exec postgres pg_dump -U tor_user tor_unveil > backup.sql

# Restore database
docker-compose exec -T postgres psql -U tor_user tor_unveil < backup.sql

# Backup to container
docker-compose exec postgres pg_dump -U tor_user -F c tor_unveil > /backup/backup.dump
```

## 🌐 API Testing

### Health Check
```powershell
# Backend health
curl http://localhost:8000/health

# Full response
Invoke-WebRequest http://localhost:8000/health
```

### Relay Endpoints
```powershell
# Get relay statistics
curl http://localhost:8000/api/relays/stats

# Get all relays (JSON)
curl http://localhost:8000/api/relays/

# Get guard relays
curl http://localhost:8000/api/relays/guards

# Refresh relay data
curl -X POST http://localhost:8000/api/relays/refresh

# Get specific relay
curl http://localhost:8000/api/relays/{fingerprint}
```

### Traffic Endpoints
```powershell
# Generate synthetic traffic
curl -X POST http://localhost:8000/api/traffic/generate `
  -H "Content-Type: application/json" `
  -d '{"num_bursts": 10, "random_seed": 42}'

# Generate correlated patterns
curl -X POST http://localhost:8000/api/traffic/generate-correlated?num_bursts=10
```

### Analysis Endpoints
```powershell
# Run analysis
curl -X POST http://localhost:8000/api/analysis/run `
  -H "Content-Type: application/json" `
  -d '{"simulation_count": 100, "top_n": 10, "random_seed": 42}'

# Get analysis result
curl http://localhost:8000/api/analysis/{analysis_id}

# Get recent analyses
curl http://localhost:8000/api/analysis/
```

### API Documentation
```powershell
# Open interactive API docs
start http://localhost:8000/docs

# Alternative docs
start http://localhost:8000/redoc
```

## 🔍 Debugging Commands

### View Container Details
```powershell
# Inspect container
docker inspect tor-unveil-backend

# View container processes
docker-compose top

# View networks
docker network ls

# View volumes
docker volume ls
```

### Check Disk Usage
```powershell
# Docker disk usage
docker system df

# Detailed breakdown
docker system df -v
```

### Clean Up Docker
```powershell
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Clean everything (WARNING: destructive)
docker system prune -a --volumes
```

## 📦 Building & Deployment

### Build Images
```powershell
# Build all images
docker-compose build

# Build specific service
docker-compose build backend

# Build with no cache (clean build)
docker-compose build --no-cache

# Parallel build
docker-compose build --parallel
```

### Pull Images
```powershell
# Pull base images
docker-compose pull

# Pull specific image
docker pull postgres:15-alpine
```

### Export/Import Images
```powershell
# Export image
docker save tor-unveil-backend -o backend.tar

# Import image
docker load -i backend.tar

# Export container
docker export tor-unveil-backend > backend-container.tar
```

## 🧪 Testing Commands

### Test Backend
```powershell
# Run pytest (if installed)
docker-compose exec backend pytest

# Run specific test
docker-compose exec backend pytest tests/test_correlation.py

# With coverage
docker-compose exec backend pytest --cov=app
```

### Test Frontend
```powershell
# Run tests
docker-compose exec frontend npm test

# Run tests once (CI mode)
docker-compose exec frontend npm test -- --watchAll=false

# Run with coverage
docker-compose exec frontend npm test -- --coverage
```

## 📝 Configuration Commands

### View Environment Variables
```powershell
# View .env file
type .env

# View container environment
docker-compose exec backend printenv

# Check specific variable
docker-compose exec backend printenv DATA_SOURCE
```

### Update Configuration
```powershell
# Edit .env file
notepad .env

# After changes, restart services
docker-compose down
docker-compose up -d
```

## 🔄 Update & Maintenance

### Update Dependencies

#### Backend (Python)
```powershell
# Update requirements.txt
docker-compose exec backend pip install --upgrade package-name

# Generate new requirements
docker-compose exec backend pip freeze > requirements.txt
```

#### Frontend (Node)
```powershell
# Update package
docker-compose exec frontend npm update package-name

# Update all packages
docker-compose exec frontend npm update

# Check for outdated packages
docker-compose exec frontend npm outdated
```

### Database Maintenance
```powershell
# Vacuum database
docker-compose exec postgres psql -U tor_user -d tor_unveil -c "VACUUM ANALYZE;"

# Check database size
docker-compose exec postgres psql -U tor_user -d tor_unveil -c "SELECT pg_size_pretty(pg_database_size('tor_unveil'));"

# Reindex database
docker-compose exec postgres psql -U tor_user -d tor_unveil -c "REINDEX DATABASE tor_unveil;"
```

## 🌐 Access URLs

### Local Development
```powershell
# Frontend Dashboard
start http://localhost:3000

# Backend API
start http://localhost:8000

# API Documentation
start http://localhost:8000/docs

# Alternative API Docs
start http://localhost:8000/redoc
```

## 🆘 Quick Troubleshooting

### Common Fix-All Command
```powershell
# Nuclear option - clean restart
docker-compose down -v
docker system prune -f
docker-compose up -d --build
```

### Check Everything
```powershell
# Comprehensive health check
docker-compose ps
docker-compose logs --tail=20
curl http://localhost:8000/health
curl http://localhost:8000/api/relays/stats
```

### Quick Reset
```powershell
# Keep data, restart services
docker-compose restart

# Full reset with fresh data
docker-compose down -v
docker-compose up -d
```

## 📚 Help Commands

### Docker Help
```powershell
# Docker Compose help
docker-compose --help

# Specific command help
docker-compose up --help

# Docker help
docker --help
```

### Application Help
```powershell
# Backend help
docker-compose exec backend python -m app.main --help

# View README
type README.md

# View docs
cd docs
dir
```

---

## 💡 Pro Tips

### Aliases for PowerShell
Add to your PowerShell profile:
```powershell
# Edit profile
notepad $PROFILE

# Add these aliases
function dc { docker-compose $args }
function dcup { docker-compose up -d }
function dcdown { docker-compose down }
function dclogs { docker-compose logs -f $args }
function dcrestart { docker-compose restart $args }
function dcps { docker-compose ps }
```

### Quick Command History
```powershell
# Recent commands
doskey /history

# Search command history
doskey /history | findstr docker
```

---

**For more details, see:**
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details
