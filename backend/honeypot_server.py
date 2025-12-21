"""
Simple Flask honeypot server for capturing real Tor traffic
This server logs all incoming requests with timing information
and can send logs to the main Tor Unveil backend for analysis
"""

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
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
        .action-btn { background: #4CAF50; color: white; padding: 10px 20px; 
                      border: none; cursor: pointer; margin: 5px; }
    </style>
</head>
<body>
    <h1>Welcome to Tor Network Research</h1>
    <div class="content">
        <p>This is a research honeypot for analyzing Tor network traffic patterns.</p>
        <p>Your access is being logged for academic research purposes.</p>
        
        <button class="action-btn" onclick="fetchData('/page1')">Load Page 1</button>
        <button class="action-btn" onclick="fetchData('/page2')">Load Page 2</button>
        <button class="action-btn" onclick="fetchData('/page3')">Load Page 3</button>
        
        <div id="result"></div>
    </div>
    
    <script>
        // Capture client-side timing data
        const clientLogs = [];
        const startTime = performance.now();
        
        function logEvent(event, size) {
            clientLogs.push({
                timestamp: (performance.now() - startTime) / 1000,  // Convert to seconds
                event: event,
                size: size,
                direction: event.includes('request') ? 'outgoing' : 'incoming'
            });
        }
        
        // Log initial page load
        window.addEventListener('load', function() {
            const perfData = performance.getEntriesByType('navigation')[0];
            logEvent('page_load', perfData.transferSize || 1024);
        });
        
        function fetchData(url) {
            const start = performance.now();
            logEvent('request_sent', 512);
            
            fetch(url)
                .then(response => response.text())
                .then(data => {
                    const duration = performance.now() - start;
                    logEvent('response_received', data.length);
                    document.getElementById('result').innerHTML = '<p>' + data + '</p>';
                    
                    // After some interaction, send logs to backend
                    if (clientLogs.length > 5) {
                        sendLogsToBackend();
                    }
                });
        }
        
        function sendLogsToBackend() {
            fetch('/submit-logs', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({client_logs: clientLogs})
            }).then(() => {
                console.log('Logs submitted for analysis');
            });
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
        
        # Get server-side logs
        server_logs = get_recent_server_logs()
        
        # Send to backend for analysis
        if len(client_logs) > 0 and len(server_logs) > 0:
            send_to_backend_for_analysis(client_logs, server_logs)
        
        return jsonify({"status": "success", "logs_received": len(client_logs)})
    except Exception as e:
        logger.error(f"Error submitting logs: {e}")
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
