# backend/agent/monitor.py
import requests
import json
import time
import datetime
import os

data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

LOG_FILE = os.path.join(data_dir, 'logs.json')
SERVERS = {
    "payment": "http://127.0.0.1:5002/health",
    # "inventory": "http://127.0.0.1:5002/health"
    # "payment": "http://54.186.48.127:3000/health"
}

print("Starting monitoring agent...")
while True:
    for name, url in SERVERS.items():
        log_entry = {
            "service": name,
            "url": "http://54.186.48.127:3000/health",
            "timestamp": datetime.datetime.now().isoformat(),
            "status_code": None,
            "response_body": None,
            "latency_ms": None
        }
        
        # http://54.186.48.127
        
        try:
            start_time = time.time()
            res = requests.get(url, timeout=4.0) 
            end_time = time.time()

            log_entry["status_code"] = res.status_code
            log_entry["response_body"] = res.json()
            log_entry["latency_ms"] = round((end_time - start_time) * 1000)

        except requests.exceptions.RequestException as e:
            log_entry["status_code"] = "CRASHED"
            log_entry["response_body"] = str(e)

        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        print(f"Logged: {log_entry['service']} status is {log_entry['status_code']}")
    
    time.sleep(3)