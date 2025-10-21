from flask import Flask, jsonify
import sys
import time

# -------------------------------------------------------------------
# Simple argument parsing
# -------------------------------------------------------------------
if len(sys.argv) < 3:
    print("Usage: python service.py <service_name> <mode>")
    sys.exit(1)

SERVICE_NAME = sys.argv[1]
MODE = sys.argv[2]  # e.g., healthy / error / slow / crash

# -------------------------------------------------------------------
# Flask setup
# -------------------------------------------------------------------
app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": SERVICE_NAME}), 200

# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    print(f"🚀 Starting {SERVICE_NAME} service in {MODE} mode on port 3000")
    app.run(host="0.0.0.0", port=3000, debug=False)