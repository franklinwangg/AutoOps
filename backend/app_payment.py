# backend/simulated_servers/app_payment.py
from flask import Flask, jsonify
import random
import time
import os

app = Flask(__name__)

@app.route('/health')
def health_check():
    """
    Simulates a health check endpoint that can fail or experience latency.
    """
    # Simulate random high latency
    if random.random() < 0.15: # 15% chance of being slow
        time.sleep(random.uniform(1.5, 3.0))

    # Simulate random errors (crashes)
    if random.random() < 0.25: # 25% chance of returning a server error
        return jsonify({"status": "error", "service": "payment", "pid": os.getpid()}), 500
    
    return jsonify({"status": "ok", "service": "payment", "pid": os.getpid()}), 200

if __name__ == '__main__':
    # Runs on port 5001. use_reloader=False is important for our restart script to work properly.
    app.run(port=5001, debug=True, use_reloader=False)