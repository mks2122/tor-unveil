# Real-Time Tor Traffic Analysis

This system now supports **real-time analysis** of actual Tor Browser traffic alongside the existing simulated traffic analysis.

## How It Works

1. **Honeypot Website**: A Flask server logs all incoming requests with precise timing information
2. **Client-Side Logging**: JavaScript in the honeypot captures client-side timing data (Performance API)
3. **Automatic Analysis**: Server automatically sends collected logs to the backend for correlation analysis
4. **Guard Node Identification**: System identifies your probable guard node based on traffic patterns

## Quick Start

### 1. Start the Full System

```bash
# Start main application (backend + frontend + database)
docker-compose up -d

# Or use the start script
.\start.bat
```

### 2. Start the Honeypot Server

```bash
cd backend
python honeypot_server.py
```

The honeypot will run on `http://localhost:5000`

### 3. Expose with Ngrok

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5000
```

Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 4. Access via Tor Browser

1. Open Tor Browser
2. Navigate to your ngrok URL
3. Click the buttons to generate traffic
4. Check Tor Browser's circuit display for your guard node:
   - Click the onion icon in the address bar
   - Note the first relay (Entry/Guard node)
   - Copy its fingerprint

### 5. View Results

The analysis happens automatically! Check:

- **Console Output**: Honeypot server logs show when analysis completes
- **Backend Logs**: Docker logs show correlation results
- **Frontend Dashboard**: Navigate to `http://localhost:3000` to see all analyses

## Architecture

```
Tor Browser (Your Location)
    ↓ [Guard Node - Unknown]
    ↓ [Middle Relay]
    ↓ [Exit Node - Visible IP]
    ↓
Ngrok → Honeypot Server
    ↓ [Traffic Logs]
    ↓
Backend Analysis Service
    ↓ [Correlation Engine]
    ↓
Identify Guard Node
```

## Expected Results

### Simulated Traffic (Existing Mode)
- **Accuracy**: 60-80%
- **Confidence**: High (controlled environment)
- **Purpose**: Proof of concept

### Real Tor Traffic (New Mode)
- **Accuracy**: 15-40%
- **Confidence**: Lower (Tor's timing obfuscation works!)
- **Purpose**: Validation against real-world Tor circuits

The lower accuracy with real traffic is **expected and proves Tor's defenses work**. This research helps validate timing correlation attack feasibility.

## API Endpoints

### Real-Time Analysis
```bash
POST /api/traffic/ingest-realtime
Content-Type: application/json

{
  "client_logs": [
    {"timestamp": 0.0, "size": 512, "direction": "outgoing"},
    {"timestamp": 0.05, "size": 1024, "direction": "incoming"}
  ],
  "server_logs": [
    {"timestamp": "2025-12-21T10:00:00.123Z", "exit_ip": "185.220.101.42", "size": 512}
  ],
  "metadata": {"session_id": "test-001"}
}
```

### Status Check
```bash
GET /api/traffic/status
```

Returns:
```json
{
  "analysis_mode": "both",
  "cache_enabled": true,
  "cache_ttl_seconds": 3600,
  "expected_real_accuracy": 0.25,
  "auto_analyze": true
}
```

## Configuration

Edit `backend/app/config.py`:

```python
# Enable/disable real traffic analysis
ANALYSIS_MODE = "both"  # "simulated", "real", or "both"

# Onionoo API caching (reduces API calls)
ENABLE_RELAY_CACHE = True
ONIONOO_CACHE_TTL_SECONDS = 3600  # 1 hour

# Auto-analyze when traffic is received
REAL_TRAFFIC_AUTO_ANALYZE = True

# Expected accuracy for real Tor traffic
EXPECTED_REAL_ACCURACY = 0.25  # 25%
```

## Database Schema

New tables added:

### `relay_cache`
- Caches Onionoo API responses (relay details, IP lookups)
- Expires after TTL (default 1 hour)
- Reduces API calls and improves performance

### `traffic_uploads`
- Stores real traffic logs
- Links to analysis results
- Tracks `was_correct` for validation

## Validation Workflow

To validate if the system correctly identifies your guard:

1. Access honeypot via Tor Browser
2. Note your actual guard fingerprint from Tor circuit display
3. Wait for automatic analysis to complete
4. Compare top-ranked guard against actual guard
5. Accuracy improves with multiple sessions

## Manual Testing

You can also send logs manually:

```bash
# Capture logs to file
curl https://your-ngrok-url.ngrok.io/status > session1.json

# Send to backend
curl -X POST http://localhost:8000/api/traffic/ingest-realtime \
  -H "Content-Type: application/json" \
  -d @session1.json
```

## Troubleshooting

### "No relay found for IP"
- Exit node might be newly added (not in Onionoo yet)
- Cache may need refresh
- Try again in a few minutes

### "Analysis failed"
- Check if guard relays are loaded: `GET /api/relays/guards`
- Refresh relays: `POST /api/relays/refresh`
- Check Docker logs: `docker-compose logs backend`

### Low Correlation Scores
- **This is normal!** Real Tor traffic has:
  - Multiple middle hops adding latency
  - Intentional timing obfuscation
  - Traffic padding and shaping
- Expected correlation: 20-40% for correct guard

## Research Notes

This implementation demonstrates:
- ✅ Timing correlation attacks are possible in theory
- ✅ Real Tor circuits are significantly harder to correlate than simulations
- ✅ Tor's anonymity protections provide meaningful defense
- ✅ Multiple observations improve accuracy over time

**Ethical Usage**: This tool is for educational and research purposes only. Always:
- Use with your own Tor traffic
- Never attempt to deanonymize others
- Respect Tor Project's mission to provide privacy
