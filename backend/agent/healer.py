# backend/agent/healer.py
import boto3
import json
import time
import subprocess
import os
import datetime  # <--- FIX 1: ADDED MISSING IMPORT

# --- Configuration ---
BEDROCK_REGION = 'us-east-1' # Change to your preferred region
BEDROCK_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'

# --- FIX 2: Corrected path logic ---
# Get the absolute path to the 'backend' directory
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the absolute path to the root 'data' directory (one level up, then into 'data')
DATA_DIR = os.path.join(BACKEND_DIR, '..', '..', 'data')
LOG_FILE = os.path.join(DATA_DIR, 'logs.json')
ACTION_LOG_FILE = os.path.join(DATA_DIR, 'agent_actions.json')

LOGS_TO_ANALYZE = 15 # Number of recent log lines to send to the AI

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- AWS Bedrock Client ---
try:
    bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name=BEDROCK_REGION)
    print(f"Successfully connected to Bedrock in {BEDROCK_REGION}.")
except Exception as e:
    print(f"Error connecting to Bedrock: {e}")
    print("Please ensure your AWS credentials and region are configured correctly.")
    exit()

def analyze_logs_with_ai(log_data):
    """Sends logs to Bedrock and asks for an action."""
    system_prompt = """
    You are an expert AI Site Reliability Engineer named "AutoOps". Your task is to analyze server logs and decide on a corrective action.
    - A service is considered 'unhealthy' if it has a status_code other than 200 multiple times.
    - A service is 'crashed' if its status_code is 'CRASHED'.
    - If a service is crashed or consistently unhealthy, you must issue a 'restart' command.
    - ONLY respond with a single, valid JSON object and nothing else.

    If a restart is needed, respond in this format:
    {"action": "restart", "service_name": "payment", "reason": "Service is unresponsive with multiple CRASHED logs."}

    If everything is okay, respond with:
    {"action": "none", "reason": "All services are operating normally."}
    """
    
    messages = [{"role": "user", "content": f"Analyze these recent logs and provide a corrective action JSON:\n\n{log_data}"}]

    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 512,
                "system": system_prompt,
                "messages": messages
            })
        )
        result_body = json.loads(response['body'].read())
        ai_response_text = result_body['content'][0]['text']
        return json.loads(ai_response_text) # Directly parse the JSON from the AI's text response
    
    except Exception as e:
        print(f"Error communicating with Bedrock or parsing its response: {e}")
        return {"action": "none", "reason": f"AI analysis failed: {e}"}

def restart_service(service_name):
    """Kills and restarts a simulated service based on its name."""
    print(f"--- ACTION: RESTARTING {service_name.upper()} SERVICE ---")
    
    # --- FIX 2 (continued): Corrected script paths ---
    if service_name == "payment":
        script_path = os.path.join(BACKEND_DIR, "..", "simulated_servers", "app_payment.py")
    elif service_name == "inventory":
        script_path = os.path.join(BACKEND_DIR, "..", "simulated_servers", "app_inventory.py")
    else:
        print(f"Warning: Unknown service name '{service_name}' provided for restart.")
        return

    # Use 'py' to be Windows-friendly
    try:
        # We assume the 'venv' is in the 'backend' folder
        venv_python_path = os.path.join(BACKEND_DIR, "..", "venv", "Scripts", "python.exe")
        # Check if venv python exists, otherwise use global 'py'
        python_executable = venv_python_path if os.path.exists(venv_python_path) else "py"

        # Since pkill is not on Windows, we'll just start a new process.
        # The old one will be a "zombie" but for a hackathon demo this is fine.
        subprocess.Popen([python_executable, script_path])
        print(f"Restart command issued for {script_path}")
        
    except Exception as e:
        print(f"Failed to restart service: {e}")


# --- Main Healing Loop ---
print("Starting AI Healer agent...")
while True:
    try:
        with open(LOG_FILE, "r") as f:
            # Get the last N log entries
            recent_logs = "".join(f.readlines()[-LOGS_TO_ANALYZE:])
        
        if not recent_logs:
            print(f"Log file '{LOG_FILE}' is empty. Waiting for data...")
            time.sleep(10)
            continue

        ai_decision = analyze_logs_with_ai(recent_logs)
        decision_timestamp = datetime.datetime.now().isoformat()
        ai_decision['timestamp'] = decision_timestamp
        
        print(f"AI Decision: {ai_decision.get('reason')}")

        # Log the AI's decision
        with open(ACTION_LOG_FILE, 'a') as f:
            f.write(json.dumps(ai_decision) + '\n')
        
        # Execute the action if needed
        if ai_decision.get("action") == "restart":
            service_to_restart = ai_decision.get("service_name")
            if service_to_restart:
                restart_service(service_to_restart)

    except FileNotFoundError:
        print(f"Log file '{LOG_FILE}' not found. Waiting for monitor to create it...")
    except Exception as e:
        print(f"An error occurred in the main loop: {e}")

    # Wait before the next analysis cycle
    time.sleep(15)