# backend/simulated_servers/app_inventory.py
from flask import Flask, jsonify
import random
import time
import os

app = Flask(__name__)

@app.route('/health')
def health_check():
    """
    Simulates a health check endpoint for the inventory service.
    """
    # Simulate random latency
    if random.random() < 0.10: # 10% chance of being slow
        time.sleep(random.uniform(1.0, 2.0))

    # Simulate random errors
    if random.random() < 0.20: # 20% chance of failure
        return jsonify({"status": "error", "service": "inventory", "pid": os.getpid()}), 500
        
    return jsonify({"status": "ok", "service": "inventory", "pid": os.getpid()}), 200

if __name__ == '__main__':
    # Runs on port 5002
    app.run(port=5002, debug=True, use_reloader=False)