# # service.py
# from flask import Flask, jsonify
# from pathlib import Path
# import tomllib
# import time
# import os
# import sys

# # ------------------------------------------------------------
# # ✅ Argument Parsing
# # ------------------------------------------------------------
# if len(sys.argv) < 3:
#     print("Usage: python service.py <service_name> <config_filename>")
#     sys.exit(1)

# SERVICE_NAME = sys.argv[1]
# CONFIG_FILENAME = sys.argv[2]

# # ------------------------------------------------------------
# # 🗂️ Paths and Config Setup
# # ------------------------------------------------------------
# BASE_DIR = Path(__file__).resolve().parent
# MVP_DIR = BASE_DIR / "scenarios"
# CONFIG_PATH = MVP_DIR / f"{CONFIG_FILENAME}_config.toml"

# if not CONFIG_PATH.exists():
#     print(f"❌ Config file not found: {CONFIG_PATH}")
#     sys.exit(1)

# # ------------------------------------------------------------
# # 🌐 Flask Application
# # ------------------------------------------------------------
# app = Flask(__name__)

# def load_config() -> dict:
#     """Load TOML configuration file."""
#     try:
#         with open(CONFIG_PATH, "rb") as f:
#             return tomllib.load(f)["service"]
#     except Exception as e:
#         print(f"Error loading config file {CONFIG_PATH}: {e}")
#         return {"name": "unknown", "mode": "error", "latency_ms": 0}


# @app.route("/health")
# def health():
#     """Return service health based on config settings."""
#     cfg = load_config()
#     mode = cfg.get("mode", "healthy")
#     latency = cfg.get("latency_ms", 0) / 1000.0
#     name = cfg.get("name", "unknown")

#     if latency > 0:
#         time.sleep(latency)

#     if mode == "healthy":
#         return jsonify({"status": "ok", "service": name, "pid": os.getpid()}), 200
#     elif mode == "error":
#         return jsonify({"status": "error", "service": name, "pid": os.getpid()}), 500
#     elif mode == "crash":
#         print(f"[{name}] Simulated crash triggered. Exiting process...")
#         os._exit(1)
#     elif mode == "slow":
#         time.sleep(latency + 1)
#         return jsonify({"status": "ok", "service": name, "pid": os.getpid()}), 200
#     else:
#         return jsonify({"status": f"unknown mode '{mode}'", "service": name}), 500


# # ------------------------------------------------------------
# # 🏁 Entry Point
# # ------------------------------------------------------------
# if __name__ == "__main__":
#     cfg = load_config()
#     port = cfg.get("port", 5001)

#     print(f"🚀 Starting {cfg.get('name', 'service')} on port {port}")
#     print(f"📄 Using config: {CONFIG_PATH}")

#     app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)





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
