# Quick Start Guide - Real-Time Tor Analysis

## Prerequisites
- Docker Desktop installed and **running**
- Python 3.8+ installed
- Ngrok installed (download from https://ngrok.com/download)
- Tor Browser installed

## Step-by-Step Setup

### 1. Start Docker Desktop
**Important**: Open Docker Desktop and wait for it to fully start before proceeding.

### 2. Start the Main Application

```bash
# Navigate to project directory
cd e:\personalProjects\tor-unveil

# Start all services (backend, frontend, database)
docker-compose up -d

# Wait about 30 seconds for services to initialize
```

Check services are running:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs
- Database: PostgreSQL on port 5432

### 3. Install Python Dependencies (for honeypot)

```bash
cd backend
pip install -r requirements.txt
```

### 4. Test the Backend

```bash
# From project root
python test_realtime.py
```

Expected output:
```
✓ Backend is running
✓ Guard relays available
✓ Real-time analysis successful!
```

### 5. Start the Honeypot Server

```bash
cd backend
python honeypot_server.py
```

You should see:
```
============================================================
TOR UNVEIL HONEYPOT SERVER
============================================================
1. Start this server: python honeypot_server.py
2. Expose with ngrok: ngrok http 5000
3. Access ngrok URL via Tor Browser
4. Server will auto-send logs to backend for analysis
============================================================
 * Running on http://0.0.0.0:5000
```

**Keep this terminal open!**

### 6. Expose Honeypot with Ngrok

Open a **new terminal**:

```bash
ngrok http 5000
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

**Keep this terminal open!**

### 7. Access via Tor Browser

1. Open **Tor Browser**
2. Paste the ngrok URL into the address bar
3. Press Enter

4. **Note Your Guard Node**:
   - Click the **onion icon** (🧅) in the address bar
   - Look for the first relay (Entry/Guard)
   - It will show something like:
     ```
     This browser → Guard (YourGuardNode) → Middle → Exit → Internet
     ```
   - Write down the guard node name/fingerprint

5. **Generate Traffic**:
   - Click the "Load Page 1", "Load Page 2", "Load Page 3" buttons
   - Click them multiple times (10-20 clicks total)
   - This generates traffic patterns

### 8. View Analysis Results

**In the honeypot terminal**, you should see:
```
INFO: Request from 185.220.101.42: GET /
INFO: Request from 185.220.101.42: GET /page1
INFO: Request from 185.220.101.42: GET /page2
INFO: Analysis completed: abc-123-def-456
```

**In the backend logs**:
```bash
docker-compose logs -f backend
```

Look for:
```
Real-time analysis complete. Top guard: 9695DFC35FF... (34.56% probability)
```

**In the Frontend Dashboard**:
- Open http://localhost:3000
- Recent analyses will show the real-time results
- Compare the top-ranked guard against your actual guard!

## Understanding the Results

### What You'll See:

```json
{
  "analysis_id": "abc-123",
  "mode": "real",
  "ranked_guards": [
    {
      "fingerprint": "9695DFC35FFEB861329B9F1AB04C46397020CE31",
      "nickname": "Quintex42",
      "probability": 0.3456,  // 34.56%
      "country": "DE"
    },
    ...
  ],
  "exit_node": {
    "ip": "185.220.101.42",
    "fingerprint": "ABC123..."
  },
  "statistics": {
    "entry_packets": 8,
    "exit_packets": 8,
    "traffic_duration": 1.25
  }
}
```

### Validation:

1. **Compare fingerprints**: Does the top-ranked guard match your actual guard?
2. **Check probability**: 20-40% is typical for real Tor traffic
3. **Multiple sessions**: Accuracy improves with more data

### Expected Accuracy:
- **Simulated traffic**: 60-80% (proof of concept)
- **Real Tor traffic**: 15-40% (Tor's defenses work!)

**Lower accuracy with real traffic is expected** - it proves Tor's timing obfuscation is effective.

## Troubleshooting

### "Docker daemon not running"
- Open Docker Desktop application
- Wait for the whale icon to stop animating
- Try `docker ps` to verify it's running

### "No guard relays available"
```bash
# Refresh relays
curl -X POST http://localhost:8000/api/relays/refresh
```

### "ModuleNotFoundError: No module named 'flask'"
```bash
cd backend
pip install -r requirements.txt
```

### "Connection refused" on backend
```bash
# Check if backend is running
docker-compose ps

# Restart if needed
docker-compose restart backend

# View logs
docker-compose logs backend
```

### "No relay found for IP"
- Exit node might be new (not in Onionoo database yet)
- Wait a few minutes and try again
- The analysis will still rank guards, just without exit node info

### Low correlation scores
**This is normal!** Real Tor traffic is intentionally obfuscated:
- Multiple hops add random latency
- Traffic padding disguises patterns
- Timing correlation is harder than simulations suggest

## Advanced Usage

### Manual Log Submission

Save traffic to JSON:
```json
{
  "version": "1.0",
  "metadata": {
    "capture_start": "2025-12-21T10:00:00Z",
    "entry_node_fingerprint": "KNOWN_GUARD_FINGERPRINT"
  },
  "entry_traffic": {
    "timestamps": [0.0, 0.05, 0.12, 0.18],
    "packet_sizes": [512, 1024, 512, 768]
  },
  "exit_traffic": {
    "timestamps": [0.1, 0.15, 0.22, 0.28],
    "packet_sizes": [512, 1024, 512, 768]
  }
}
```

Submit via API:
```bash
curl -X POST http://localhost:8000/api/traffic/ingest-realtime \
  -H "Content-Type: application/json" \
  -d @traffic_log.json
```

### Configuration

Edit `backend/app/config.py`:

```python
# Enable both modes
ANALYSIS_MODE = "both"

# Cache Onionoo API calls
ENABLE_RELAY_CACHE = True
ONIONOO_CACHE_TTL_SECONDS = 3600  # 1 hour

# Auto-analyze incoming traffic
REAL_TRAFFIC_AUTO_ANALYZE = True
```

Restart backend after changes:
```bash
docker-compose restart backend
```

## Next Steps

1. **Multiple Sessions**: Run 10-20 sessions to measure average accuracy
2. **Different Guards**: Tor changes guards every 2-3 months
3. **Traffic Patterns**: Try different browsing patterns (fast clicks vs slow)
4. **Location Testing**: Test from different physical locations
5. **Validation Dashboard**: Track `was_correct` field to measure accuracy over time

## API Reference

### Real-Time Analysis
```
POST /api/traffic/ingest-realtime
Content-Type: application/json

{
  "client_logs": [...],
  "server_logs": [...],
  "metadata": {...}
}
```

### Status Check
```
GET /api/traffic/status
```

### Guard Relays
```
GET /api/relays/guards
POST /api/relays/refresh
```

## Safety & Ethics

⚠️ **Important Reminders**:
- This tool is for **educational research only**
- Only analyze **your own** Tor traffic
- Never attempt to deanonymize others
- Respect Tor Project's privacy mission
- This research helps improve Tor's defenses

## Support

If you encounter issues:
1. Check Docker Desktop is running
2. Verify all ports are available (3000, 5000, 8000, 5432)
3. Review logs: `docker-compose logs -f`
4. Test backend: `python test_realtime.py`
5. Check firewall settings for ngrok

---

**Research Goal**: Validate whether timing correlation attacks can work against real Tor circuits. The results show that while theoretically possible, Tor's defenses significantly reduce attack effectiveness.
