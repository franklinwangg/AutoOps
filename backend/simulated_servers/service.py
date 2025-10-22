# from flask import Flask, jsonify
# import sys
# import time

# # -------------------------------------------------------------------
# # Simple argument parsing
# # -------------------------------------------------------------------
# if len(sys.argv) < 3:
#     print("Usage: python service.py <service_name> <mode>")
#     sys.exit(1)

# SERVICE_NAME = sys.argv[1]
# MODE = sys.argv[2]  # e.g., healthy / error / slow / crash

# # -------------------------------------------------------------------
# # Flask setup
# # -------------------------------------------------------------------
# app = Flask(__name__)

# @app.route("/health")
# def health():
#     return jsonify({"status": "ok", "service": SERVICE_NAME}), 200

# # -------------------------------------------------------------------
# # Entry point
# # -------------------------------------------------------------------
# if __name__ == "__main__":
#     print(f"🚀 Starting {SERVICE_NAME} service in {MODE} mode on port 3000")
#     app.run(host="0.0.0.0", port=3000, debug=False)

from flask import Flask, jsonify
import sys
import time
import tomli
import threading
import os

# -------------------------------------------------------------------
# Argument parsing
# -------------------------------------------------------------------
if len(sys.argv) < 3:
    print("Usage: python service.py <service_name> <mode_toml_file>")
    sys.exit(1)

SERVICE_NAME = sys.argv[1]
MODE_FILE = sys.argv[2]  # e.g., healthy.toml, slow.toml, crash.toml

# -------------------------------------------------------------------
# Load configuration from TOML
# -------------------------------------------------------------------
if not os.path.exists(MODE_FILE):
    print(f"❌ Mode file '{MODE_FILE}' not found.")
    sys.exit(1)

with open(MODE_FILE, "rb") as f:
    config = tomli.load(f)

behavior = config.get("behavior", {})
STATUS = behavior.get("status", "ok")
DELAY = behavior.get("delay", 0)
CRASH = behavior.get("crash", False)

# -------------------------------------------------------------------
# Flask setup
# -------------------------------------------------------------------
app = Flask(__name__)

@app.route("/health")
def health():
    if CRASH:
        # Simulate crash by exiting the process
        print("💥 Simulating crash mode...")
        os._exit(1)
    
    if DELAY > 0:
        print(f"⏳ Simulating slow response: {DELAY}s delay")
        time.sleep(DELAY)
    
    return jsonify({"status": STATUS, "service": SERVICE_NAME}), 200

# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    print(f"🚀 Starting {SERVICE_NAME} service using config '{MODE_FILE}'")
    print(f"    → status: {STATUS}, delay: {DELAY}, crash: {CRASH}")
    app.run(host="0.0.0.0", port=3000, debug=False)
