# backend/agent/monitor.py
import requests
import json
import time
import datetime
import os

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

LOG_FILE = 'data/logs.json'
SERVERS = {
    "payment": "http://127.0.0.1:5001/health",
    "inventory": "http://127.0.0.1:5002/health"
}

print("Starting monitoring agent...")
while True:
    for name, url in SERVERS.items():
        log_entry = {
            "service": name,
            "url": url,
            "timestamp": datetime.datetime.now().isoformat(),
            "status_code": None,
            "response_body": None,
            "latency_ms": None
        }
        
        try:
            start_time = time.time()
            res = requests.get(url, timeout=2.0) # 2-second timeout
            end_time = time.time()

            log_entry["status_code"] = res.status_code
            log_entry["response_body"] = res.json()
            log_entry["latency_ms"] = round((end_time - start_time) * 1000)

        except requests.exceptions.RequestException as e:
            log_entry["status_code"] = "CRASHED"
            log_entry["response_body"] = str(e)
        
        # Append the log entry as a new line in the JSON log file
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        print(f"Logged: {log_entry['service']} status is {log_entry['status_code']}")
    
    # Wait before the next round of checks
    time.sleep(3)