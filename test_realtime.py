"""
Test script to verify real-time analysis setup
"""
import requests
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

def test_backend_status():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/traffic/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Backend is running")
            print(f"  - Analysis mode: {data['analysis_mode']}")
            print(f"  - Cache enabled: {data['cache_enabled']}")
            print(f"  - Auto-analyze: {data['auto_analyze']}")
            return True
        else:
            print("✗ Backend returned error:", response.status_code)
            return False
    except Exception as e:
        print(f"✗ Backend not accessible: {e}")
        return False

def test_realtime_analysis():
    """Test real-time traffic analysis with sample data"""
    print("\nTesting real-time analysis...")
    
    # Sample traffic logs
    payload = {
        "client_logs": [
            {"timestamp": 0.0, "size": 512, "direction": "outgoing"},
            {"timestamp": 0.05, "size": 1024, "direction": "incoming"},
            {"timestamp": 0.12, "size": 512, "direction": "outgoing"},
            {"timestamp": 0.18, "size": 768, "direction": "incoming"},
            {"timestamp": 1.2, "size": 512, "direction": "outgoing"},
            {"timestamp": 1.25, "size": 1024, "direction": "incoming"},
        ],
        "server_logs": [
            {"timestamp": datetime.utcnow().isoformat() + "Z", "exit_ip": "185.220.101.42", "size": 512},
            {"timestamp": datetime.utcnow().isoformat() + "Z", "exit_ip": "185.220.101.42", "size": 1024},
            {"timestamp": datetime.utcnow().isoformat() + "Z", "exit_ip": "185.220.101.42", "size": 768},
        ],
        "metadata": {
            "session_id": "test-001",
            "test": True
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/traffic/ingest-realtime",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Real-time analysis successful!")
            print(f"  - Analysis ID: {result['analysis_id']}")
            print(f"  - Mode: {result['mode']}")
            print(f"  - Execution time: {result['execution_time']:.2f}s")
            
            if result.get('ranked_guards'):
                top_guard = result['ranked_guards'][0]
                print(f"  - Top guard: {top_guard['fingerprint'][:16]}...")
                print(f"  - Probability: {top_guard['probability']:.2%}")
                print(f"  - Country: {top_guard['country']}")
            
            if result.get('exit_node'):
                exit_node = result['exit_node']
                print(f"  - Exit IP: {exit_node.get('ip', 'N/A')}")
                print(f"  - Exit fingerprint: {exit_node.get('fingerprint', 'Unknown')[:16]}...")
            
            return True
        else:
            print(f"✗ Analysis failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Analysis request failed: {e}")
        return False

def test_guard_relays():
    """Check if guard relays are loaded"""
    print("\nChecking guard relays...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/relays/guards", timeout=10)
        if response.status_code == 200:
            guards = response.json()
            print(f"✓ {len(guards)} guard relays available")
            if guards:
                print(f"  Sample: {guards[0].get('nickname', 'N/A')} ({guards[0].get('country', 'N/A')})")
            return True
        else:
            print("✗ Failed to fetch guard relays")
            return False
    except Exception as e:
        print(f"✗ Guard relay check failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TOR UNVEIL - Real-Time Analysis Test")
    print("=" * 60)
    
    # Run tests
    status_ok = test_backend_status()
    
    if status_ok:
        guards_ok = test_guard_relays()
        
        if guards_ok:
            analysis_ok = test_realtime_analysis()
            
            if analysis_ok:
                print("\n" + "=" * 60)
                print("✓ ALL TESTS PASSED")
                print("=" * 60)
                print("\nYou can now:")
                print("1. Start honeypot: python backend/honeypot_server.py")
                print("2. Expose with ngrok: ngrok http 5000")
                print("3. Access via Tor Browser")
                print("=" * 60)
            else:
                print("\n✗ Real-time analysis test failed")
        else:
            print("\n✗ Guard relays not loaded. Run: POST /api/relays/refresh")
    else:
        print("\n✗ Backend is not running. Start with: docker-compose up -d")
