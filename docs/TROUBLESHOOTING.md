# TOR - Unveil: Troubleshooting Guide

## Common Issues and Solutions

### 🐳 Docker Issues

#### Issue: "Docker is not running"
**Symptoms**: Error when running `start.bat` or `docker-compose up`

**Solution**:
1. Open Docker Desktop
2. Wait for Docker to fully start (whale icon in system tray)
3. Verify: Run `docker --version` in PowerShell
4. Try again: `.\start.bat`

#### Issue: Port already in use
**Symptoms**: Error like "port 3000 is already allocated"

**Solution**:
```powershell
# Check what's using the port
netstat -ano | findstr :3000

# Stop conflicting services or change ports in docker-compose.yml
# Kill process (replace PID with actual number)
taskkill /PID <PID> /F

# Or change ports in docker-compose.yml
```

#### Issue: Containers won't start
**Symptoms**: Services fail to start or crash immediately

**Solution**:
```powershell
# View logs to identify the problem
docker-compose logs

# Clean restart
docker-compose down -v
docker-compose up -d --build

# Check container status
docker-compose ps
```

### 🗄️ Database Issues

#### Issue: "Database connection failed"
**Symptoms**: Backend can't connect to PostgreSQL

**Solution**:
1. Wait 30-60 seconds for PostgreSQL to initialize
2. Check database health:
```powershell
docker-compose ps postgres
```

3. Verify database is healthy (should show "healthy" status)
4. Restart if needed:
```powershell
docker-compose restart postgres
docker-compose restart backend
```

#### Issue: "No relays in database"
**Symptoms**: Dashboard shows 0 relays, analysis fails

**Solution**:
1. Check DATA_SOURCE in `.env`:
```env
DATA_SOURCE=sample
```

2. Click "Refresh Relay Data" button in dashboard
3. Check backend logs:
```powershell
docker-compose logs backend
```

4. Manually refresh via API:
```powershell
curl -X POST http://localhost:8000/api/relays/refresh
```

#### Issue: Sample data not loading
**Symptoms**: Error loading sample_relays.json

**Solution**:
1. Verify file exists: `database/seeds/sample_relays.json`
2. Check file format (valid JSON)
3. Restart backend:
```powershell
docker-compose restart backend
```

### 🌐 Frontend Issues

#### Issue: Frontend won't load
**Symptoms**: Blank page at http://localhost:3000

**Solution**:
1. Check if frontend container is running:
```powershell
docker-compose ps frontend
```

2. View frontend logs:
```powershell
docker-compose logs frontend
```

3. Wait for compilation (first run takes 1-2 minutes)
4. Hard refresh browser: Ctrl+Shift+R
5. Clear browser cache

#### Issue: "API connection failed"
**Symptoms**: Dashboard shows connection errors

**Solution**:
1. Verify backend is running:
```powershell
docker-compose ps backend
```

2. Test backend directly: http://localhost:8000
3. Check CORS configuration in backend
4. Verify REACT_APP_API_URL in `.env`:
```env
REACT_APP_API_URL=http://localhost:8000
```

5. Restart frontend:
```powershell
docker-compose restart frontend
```

#### Issue: Charts not displaying
**Symptoms**: Dashboard loads but charts are blank

**Solution**:
1. Check browser console (F12) for errors
2. Verify Recharts and D3 are installed:
```powershell
docker-compose exec frontend npm list recharts d3
```

3. Rebuild frontend:
```powershell
docker-compose up -d --build frontend
```

### 🔧 Backend Issues

#### Issue: "ModuleNotFoundError"
**Symptoms**: Backend fails to import modules

**Solution**:
```powershell
# Rebuild backend with dependencies
docker-compose build --no-cache backend
docker-compose up -d backend
```

#### Issue: Analysis fails
**Symptoms**: "Run Analysis" button fails or times out

**Solution**:
1. Check if guards exist:
```powershell
curl http://localhost:8000/api/relays/stats
```

2. Reduce simulation count to 10 for testing
3. Check backend logs for specific error:
```powershell
docker-compose logs backend | tail -50
```

4. Verify Python dependencies:
```powershell
docker-compose exec backend pip list
```

#### Issue: Tor Onionoo API timeout
**Symptoms**: Live data fetch fails

**Solution**:
1. Check internet connection
2. Test API directly: https://onionoo.torproject.org/details
3. Switch to sample mode in `.env`:
```env
DATA_SOURCE=sample
```

4. Use "both" mode for automatic fallback:
```env
DATA_SOURCE=both
```

### ⚙️ Configuration Issues

#### Issue: Changes to .env not taking effect
**Symptoms**: Modified settings don't apply

**Solution**:
```powershell
# Restart all services
docker-compose down
docker-compose up -d

# Or restart specific service
docker-compose restart backend
```

#### Issue: Wrong ports configured
**Symptoms**: Services on unexpected ports

**Solution**:
1. Edit `docker-compose.yml` ports section
2. Edit `.env` for application URLs
3. Restart services:
```powershell
docker-compose down
docker-compose up -d
```

### 🔍 Performance Issues

#### Issue: Analysis takes too long
**Symptoms**: Analysis runs for several minutes

**Solution**:
1. Reduce simulation count (try 50 instead of 100)
2. Reduce top_n value
3. Check system resources:
```powershell
docker stats
```

4. Consider upgrading Docker resource limits in Docker Desktop settings

#### Issue: High memory usage
**Symptoms**: System becomes slow

**Solution**:
1. Check container resource usage:
```powershell
docker stats
```

2. Restart containers:
```powershell
docker-compose restart
```

3. Increase Docker memory in Docker Desktop:
   - Settings → Resources → Memory → 4GB+

### 📝 Data Issues

#### Issue: Invalid analysis results
**Symptoms**: Confidence scores are all 0 or NaN

**Solution**:
1. Verify relay data has bandwidth and uptime values
2. Check if traffic patterns are being generated:
```powershell
curl -X POST http://localhost:8000/api/traffic/generate
```

3. Review correlation engine weights
4. Check for division by zero in logs

#### Issue: Missing relay metadata
**Symptoms**: Empty fields in guard table

**Solution**:
1. Re-fetch relay data:
```powershell
curl -X POST http://localhost:8000/api/relays/refresh
```

2. Switch to live mode for complete data:
```env
DATA_SOURCE=live
```

3. Verify sample data structure in `database/seeds/sample_relays.json`

## 🔧 Diagnostic Commands

### Check All Service Status
```powershell
docker-compose ps
```

### View All Logs
```powershell
docker-compose logs -f
```

### View Specific Service Logs
```powershell
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Test Backend API
```powershell
# Health check
curl http://localhost:8000/health

# Relay stats
curl http://localhost:8000/api/relays/stats

# API documentation
start http://localhost:8000/docs
```

### Check Database
```powershell
# Connect to PostgreSQL
docker-compose exec postgres psql -U tor_user -d tor_unveil

# Inside psql:
\dt                          # List tables
SELECT COUNT(*) FROM relays; # Count relays
\q                           # Exit
```

### Container Resource Usage
```powershell
docker stats
```

### Cleanup and Reset
```powershell
# Stop and remove containers
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images (force fresh build)
docker-compose down --rmi all

# Complete clean start
docker-compose down -v
docker-compose up -d --build
```

## 🆘 Getting Help

### Still Having Issues?

1. **Check Logs**: Always review logs first
```powershell
docker-compose logs -f
```

2. **Verify Configuration**: Ensure `.env` is correct

3. **Test Components**: Test backend, frontend, database separately

4. **Clean Restart**: Try complete cleanup:
```powershell
docker-compose down -v
docker-compose up -d --build
```

5. **Check Requirements**:
   - Docker Desktop installed and running
   - Ports 3000, 8000, 5432 available
   - Sufficient disk space (2GB+)
   - Sufficient RAM (4GB+ recommended)

### Common Error Messages

#### "ECONNREFUSED"
- Backend not running or wrong API URL
- Solution: Verify backend at http://localhost:8000

#### "404 Not Found"
- Wrong API endpoint or backend not fully started
- Solution: Wait 30 seconds, check backend logs

#### "500 Internal Server Error"
- Backend error, check logs
- Solution: `docker-compose logs backend`

#### "Database connection refused"
- PostgreSQL not ready
- Solution: Wait 30 seconds or restart postgres

#### "ModuleNotFoundError"
- Missing Python dependencies
- Solution: Rebuild backend container

#### "Cannot find module"
- Missing Node dependencies
- Solution: Rebuild frontend container

## 📞 Support Resources

- **API Documentation**: http://localhost:8000/docs
- **Project README**: `README.md`
- **Architecture Guide**: `docs/ARCHITECTURE.md`
- **Quick Start**: `docs/QUICKSTART.md`

---

**Tip**: Most issues are resolved by waiting 30-60 seconds for services to fully initialize, or by running a clean restart with `docker-compose down -v && docker-compose up -d --build`
