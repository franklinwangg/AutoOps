# backend/agent/healer.py
import boto3
import json
import time
import subprocess
import os
import datetime 


BEDROCK_REGION = 'us-east-1' 
BEDROCK_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BACKEND_DIR, '..', '..', 'data')
LOG_FILE = os.path.join(DATA_DIR, 'logs.json')
ACTION_LOG_FILE = os.path.join(DATA_DIR, 'agent_actions.json')

LOGS_TO_ANALYZE = 15 

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

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
        return json.loads(ai_response_text)
    
    except Exception as e:
        print(f"Error communicating with Bedrock or parsing its response: {e}")
        return {"action": "none", "reason": f"AI analysis failed: {e}"}

def restart_service(service_name):
    """Kills and restarts a simulated service based on its name."""
    print(f"--- ACTION: RESTARTING {service_name.upper()} SERVICE ---")
    
    if service_name == "payment":
        script_path = os.path.join(BACKEND_DIR, "..", "simulated_servers", "app_payment.py")
    elif service_name == "inventory":
        script_path = os.path.join(BACKEND_DIR, "..", "simulated_servers", "app_inventory.py")
    else:
        print(f"Warning: Unknown service name '{service_name}' provided for restart.")
        return

    try:
        venv_python_path = os.path.join(BACKEND_DIR, "..", "venv", "Scripts", "python.exe")
        python_executable = venv_python_path if os.path.exists(venv_python_path) else "py"
        subprocess.Popen([python_executable, script_path])
        print(f"Restart command issued for {script_path}")
        
    except Exception as e:
        print(f"Failed to restart service: {e}")

print("Starting AI Healer agent...")
while True:
    try:
        with open(LOG_FILE, "r") as f:
            recent_logs = "".join(f.readlines()[-LOGS_TO_ANALYZE:])
        
        if not recent_logs:
            print(f"Log file '{LOG_FILE}' is empty. Waiting for data...")
            time.sleep(10)
            continue

        ai_decision = analyze_logs_with_ai(recent_logs)
        decision_timestamp = datetime.datetime.now().isoformat()
        ai_decision['timestamp'] = decision_timestamp
        
        print(f"AI Decision: {ai_decision.get('reason')}")

        with open(ACTION_LOG_FILE, 'a') as f:
            f.write(json.dumps(ai_decision) + '\n')
        
        if ai_decision.get("action") == "restart":
            service_to_restart = ai_decision.get("service_name")
            if service_to_restart:
                restart_service(service_to_restart)

    except FileNotFoundError:
        print(f"Log file '{LOG_FILE}' not found. Waiting for monitor to create it...")
    except Exception as e:
        print(f"An error occurred in the main loop: {e}")

    time.sleep(15)