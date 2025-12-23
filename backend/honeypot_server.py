"""
Simple Flask honeypot server for capturing real Tor traffic
This server logs all incoming requests with timing information
and can send logs to the main Tor Unveil backend for analysis
"""

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import logging
import requests
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store traffic logs in memory (replace with database in production)
traffic_logs = []

# Configure backend URL
BACKEND_URL = "http://localhost:8000"  # Change if running in Docker

HONEYPOT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Tor Network Research</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .content { line-height: 1.6; }
        .action-btn { background: #4CAF50; color: white; padding: 15px 30px; 
                      border: none; cursor: pointer; margin: 10px; font-size: 16px; border-radius: 5px; }
        .action-btn:hover { background: #45a049; }
        .action-btn:disabled { background: #cccccc; cursor: not-allowed; }
        
        /* Loader styles */
        .loader-overlay { 
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7); z-index: 9999; justify-content: center; align-items: center;
        }
        .loader-overlay.active { display: flex; }
        .loader-content { text-align: center; color: white; }
        .spinner { border: 8px solid #f3f3f3; border-top: 8px solid #4CAF50; border-radius: 50%;
                   width: 60px; height: 60px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { margin-top: 10px; font-size: 14px; color: #ddd; }
        #logCount { font-weight: bold; color: #4CAF50; }
    </style>
</head>
<body>
    <h1>Welcome to Tor Network Research</h1>
    <div class="content">
        <p>This is a research honeypot for analyzing Tor network traffic patterns.</p>
        <p>Your access is being logged for academic research purposes.</p>
        
        <button class="action-btn" id="analyzeBtn" onclick="generateTrafficAndAnalyze()">
            🔍 Generate Traffic & Analyze 
        </button>
        
        <div id="result"></div>
    </div>
    
    <!-- Loading Overlay -->
    <div class="loader-overlay" id="loader">
        <div class="loader-content">
            <div class="spinner"></div>
            <h2>Analyzing Tor Traffic...</h2>
            <p class="status">Captured <span id="logCount">0</span> packets</p>
            <p class="status" id="statusText">Generating traffic patterns...</p>
        </div>
    </div>
    
    <script>
        // Capture client-side timing data
        const clientLogs = [];
        const startTime = performance.now();
        
        function logEvent(event, size) {
            clientLogs.push({
                timestamp: (performance.now() - startTime) / 1000,  // Convert to seconds
                size: size,
                event: event,
                direction: event.includes('request') ? 'outgoing' : 'incoming'
            });
            document.getElementById('logCount').textContent = clientLogs.length;
        }
        
        // Log initial page load
        window.addEventListener('load', function() {
            const perfData = performance.getEntriesByType('navigation')[0];
            logEvent('page_load', perfData.transferSize || 1024);
        });
        
        async function generateTrafficAndAnalyze() {
            const btn = document.getElementById('analyzeBtn');
            const loader = document.getElementById('loader');
            const statusText = document.getElementById('statusText');
            
            // Disable button and show loader
            btn.disabled = true;
            loader.classList.add('active');
            
            // Clear previous logs
            clientLogs.length = 0;
            
            try {
                // Generate realistic traffic with proper timing variations
                // Create 30 request-response pairs (60 total events)
                for (let i = 0; i < 30; i++) {
                    const requestSize = 400 + Math.floor(Math.random() * 400);  // 400-800 bytes
                    const responseSize = 1200 + Math.floor(Math.random() * 3800);  // 1.2-5KB
                    
                    // Log outgoing request
                    logEvent(`request_${i}`, requestSize);
                    
                    // Simulate Tor latency (50-250ms with some variance)
                    const latency = 50 + Math.random() * 200;
                    await new Promise(resolve => setTimeout(resolve, latency));
                    
                    // Log incoming response
                    logEvent(`response_${i}`, responseSize);
                    
                    // Inter-request delay (10-100ms, with occasional longer pauses)
                    let interDelay = 10 + Math.random() * 90;
                    
                    // Every 5th request, add a longer pause (simulates burst boundaries)
                    if (i % 5 === 4) {
                        interDelay += 200 + Math.random() * 300;  // 200-500ms burst gap
                    }
                    
                    await new Promise(resolve => setTimeout(resolve, interDelay));
                    
                    // Update status every 5 requests
                    if ((i+1) % 5 === 0) {
                        statusText.textContent = `Generating traffic patterns... (${(i+1)*2}/60 packets)`;
                    }
                }
                
                statusText.textContent = `Submitting ${clientLogs.length} packets for analysis...`;
                console.log('Generated logs:', clientLogs.length, 'packets');
                
                // Submit logs to backend
                const response = await fetch('/submit-logs', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({client_logs: clientLogs})
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('Analysis result:', result);
                    statusText.textContent = 'Analysis complete! Check the dashboard for results.';
                    setTimeout(() => {
                        loader.classList.remove('active');
                        btn.disabled = false;
                        document.getElementById('result').innerHTML = 
                            `<p style="color: green; font-weight: bold;">✅ Analyzed ${clientLogs.length} packets! Check the realtime dashboard.</p>`;
                    }, 2000);
                } else {
                    const errorText = await response.text();
                    throw new Error(`Server error: ${errorText}`);
                }
                
            } catch (error) {
                console.error('Error:', error);
                statusText.textContent = 'Error: ' + error.message;
                document.getElementById('result').innerHTML = 
                    `<p style="color: red;">❌ ${error.message}</p>`;
                setTimeout(() => {
                    loader.classList.remove('active');
                    btn.disabled = false;
                }, 3000);
            }
        }
        
        // Auto-submit logs before page unload
        window.addEventListener('beforeunload', function() {
            if (clientLogs.length > 0) {
                navigator.sendBeacon('/submit-logs', JSON.stringify({client_logs: clientLogs}));
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main honeypot page with client-side logging"""
    log_request()
    return render_template_string(HONEYPOT_HTML)

@app.route('/page1')
@app.route('/page2')
@app.route('/page3')
def pages():
    """Sample pages for generating traffic"""
    log_request()
    page_content = f"This is {request.path}. Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10
    return jsonify({"content": page_content, "timestamp": datetime.utcnow().isoformat()})

@app.route('/submit-logs', methods=['POST'])
def submit_logs():
    """Receive client-side logs and trigger analysis"""
    try:
        client_logs = request.json.get('client_logs', [])
        
        logger.info(f"Received {len(client_logs)} client logs")
        
        # Validate client logs have required fields
        if not client_logs or len(client_logs) < 10:
            return jsonify({
                "status": "error", 
                "message": f"Insufficient client logs: {len(client_logs)} (need at least 10)"
            }), 400
        
        # Create synthetic server-side logs matching client pattern
        # In real scenario, these would be actual server observations
        # For honeypot, we simulate exit node observations based on client timing
        server_logs = []
        exit_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        
        base_server_time = datetime.utcnow()
        for i, log in enumerate(client_logs):
            # Server sees packets with slight delay (Tor routing latency)
            server_timestamp = base_server_time + timedelta(seconds=log.get('timestamp', 0) + 0.05)
            server_logs.append({
                "timestamp": server_timestamp.isoformat() + "Z",
                "exit_ip": exit_ip,
                "size": log.get('size', 512),
                "sequence": i
            })
        
        logger.info(f"Created {len(server_logs)} server logs, exit_ip: {exit_ip}")
        
        # Send to backend for analysis
        send_to_backend_for_analysis(client_logs, server_logs)
        
        return jsonify({
            "status": "success", 
            "logs_received": len(client_logs),
            "server_logs_created": len(server_logs)
        })
    except Exception as e:
        logger.error(f"Error submitting logs: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

def log_request():
    """Log incoming request details"""
    # Get real client IP from proxy headers (ngrok forwards with X-Forwarded-For)
    real_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in real_ip:
        # X-Forwarded-For can be a list: "client, proxy1, proxy2"
        real_ip = real_ip.split(',')[0].strip()
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "exit_ip": real_ip,
        "path": request.path,
        "method": request.method,
        "user_agent": request.headers.get('User-Agent', ''),
        "size": request.content_length or 0,
        "headers": dict(request.headers)
    }
    traffic_logs.append(log_entry)
    logger.info(f"Request from {real_ip} (via {request.remote_addr}): {request.method} {request.path}")

def get_recent_server_logs(limit=20):
    """Get recent server logs for analysis"""
    return traffic_logs[-limit:] if traffic_logs else []

def send_to_backend_for_analysis(client_logs, server_logs):
    """Send collected logs to Tor Unveil backend (async, don't block)"""
    import threading
    
    def send_async():
        try:
            payload = {
                "client_logs": client_logs,
                "server_logs": server_logs,
                "metadata": {
                    "session_id": f"honeypot_{datetime.utcnow().timestamp()}",
                    "capture_time": datetime.utcnow().isoformat()
                }
            }
            
            # Send to backend with longer timeout (analysis takes ~16 seconds)
            response = requests.post(
                f"{BACKEND_URL}/api/traffic/ingest-realtime",
                json=payload,
                timeout=60  # Increased timeout for analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Analysis completed: {result.get('analysis_id')}")
                # Log top guard result
                if result.get('ranked_guards'):
                    top = result['ranked_guards'][0]
                    logger.info(f"Top Guard: {top.get('nickname')} ({top.get('probability'):.2%}) - {top.get('country')}")
            else:
                logger.error(f"Backend analysis failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send to backend: {e}")
    
    # Run in background thread to not block the response
    thread = threading.Thread(target=send_async)
    thread.daemon = True
    thread.start()

@app.route('/status')
def status():
    """Status endpoint showing collected logs"""
    return jsonify({
        "status": "running",
        "logs_collected": len(traffic_logs),
        "backend_url": BACKEND_URL
    })

if __name__ == '__main__':
    print("=" * 60)
    print("TOR UNVEIL HONEYPOT SERVER")
    print("=" * 60)
    print("1. Start this server: python honeypot_server.py")
    print("2. Expose with ngrok: ngrok http 5000")
    print("3. Access ngrok URL via Tor Browser")
    print("4. Server will auto-send logs to backend for analysis")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
