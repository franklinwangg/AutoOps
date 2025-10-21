from flask import Flask, jsonify
from pathlib import Path
import boto3
import tomllib
import time
import os
import sys
import atexit

# ------------------------------------------------------------
# ✅ Argument Parsing
# ------------------------------------------------------------
if len(sys.argv) < 3:
    print("Usage: python service.py <service_name> <config_filename>")
    sys.exit(1)

SERVICE_NAME = sys.argv[1]
CONFIG_FILENAME = sys.argv[2]

# ------------------------------------------------------------
# 🗂️ Paths and Config Setup
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MVP_DIR = BASE_DIR / "scenarios"
CONFIG_PATH = MVP_DIR / f"{CONFIG_FILENAME}_config.toml"

if not CONFIG_PATH.exists():
    print(f"❌ Config file not found: {CONFIG_PATH}")
    sys.exit(1)

# ------------------------------------------------------------
# ☁️ EC2 Management
# ------------------------------------------------------------
INSTANCE_ID = None

def launch_ec2_instance(service_name: str, config_filename: str) -> str:
    """Launch a new EC2 instance and run the specified service on it."""
    global INSTANCE_ID

    ec2 = boto3.resource("ec2", region_name="us-west-2")

    instances = ec2.create_instances(
        # ImageId="ami-0c55b159cbfafe1f0",  # Amazon Linux 2
        ImageId="ami-0e6af742d565ff61c",  # Amazon Linux 2 x86_64 for us-west-2
        MinCount=1,
        MaxCount=1,
        InstanceType="t3.micro",          # slightly newer, faster, still cheap
        KeyName="autoops-key",  # name of your EC2 key pair
        SecurityGroupIds=["sg-05b93c1804021efe6"],  # must allow inbound 5001
        UserData=f"""#!/bin/bash
        cd /home/ec2-user
        git clone https://github.com/yourrepo/mvp.git
        cd mvp
        python3 service.py {service_name} {config_filename} > log.txt 2>&1 &
        """,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": f"{service_name}-instance"}],
        }],
    )

    instance = instances[0]
    INSTANCE_ID = instance.id

    print("🚀 Launching EC2 instance, waiting for it to start...")
    instance.wait_until_running()

    # Wait for a public IP to be assigned
    for _ in range(10):
        instance.reload()
        if instance.public_ip_address:
            break
        time.sleep(3)

    print(f"✅ EC2 started: {instance.id}, public IP: {instance.public_ip_address}")
    return instance.public_ip_address


def terminate_ec2(instance_id: str):
    """Terminate the specified EC2 instance."""
    if not instance_id:
        print("⚠️ No EC2 instance to terminate.")
        return

    ec2 = boto3.client("ec2", region_name="us-west-2")
    ec2.terminate_instances(InstanceIds=[instance_id])
    print(f"🛑 Terminated instance {instance_id}")


def cleanup():
    """Cleanup handler triggered when the app shuts down."""
    terminate_ec2(INSTANCE_ID)

# Automatically terminate EC2 when the program exits
atexit.register(cleanup)

# ------------------------------------------------------------
# 🌐 Flask Application
# ------------------------------------------------------------
app = Flask(__name__)

def load_config() -> dict:
    """Load TOML configuration file."""
    try:
        with open(CONFIG_PATH, "rb") as f:
            return tomllib.load(f)["service"]
    except Exception as e:
        print(f"Error loading config file {CONFIG_PATH}: {e}")
        return {"name": "unknown", "mode": "error", "latency_ms": 0}


@app.route("/health")
def health():
    """Return service health based on config settings."""
    cfg = load_config()
    mode = cfg.get("mode", "healthy")
    latency = cfg.get("latency_ms", 0) / 1000.0
    name = cfg.get("name", "unknown")

    if latency > 0:
        time.sleep(latency)

    if mode == "healthy":
        return jsonify({"status": "ok", "service": name, "pid": os.getpid()}), 200
    elif mode == "error":
        return jsonify({"status": "error", "service": name, "pid": os.getpid()}), 500
    elif mode == "crash":
        print(f"[{name}] Simulated crash triggered. Exiting process...")
        os._exit(1)
    elif mode == "slow":
        time.sleep(latency + 1)
        return jsonify({"status": "ok", "service": name, "pid": os.getpid()}), 200
    else:
        return jsonify({"status": f"unknown mode '{mode}'", "service": name}), 500


# ------------------------------------------------------------
# 🏁 Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    ip = launch_ec2_instance(SERVICE_NAME, CONFIG_FILENAME)
    print(f"Service will run on EC2 at {ip}")

    cfg = load_config()
    port = cfg.get("port", 5001)

    print(f"🚀 Starting {cfg.get('name', 'service')} on port {port}")
    print(f"📄 Using config: {CONFIG_PATH}")

    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)



# # launch_ec2.py
# import boto3
# import time
# import sys
# from flask import Flask, jsonify

# import atexit

# INSTANCE_ID = None
# app = Flask(__name__)


# def launch_ec2_instance(service_name: str, config_filename: str) -> str:
#     """Launch a new EC2 instance and start the specified service remotely."""
#     global INSTANCE_ID

#     ec2 = boto3.resource("ec2", region_name="us-west-2")

#     # instances = ec2.create_instances(
#     #     ImageId="ami-0e6af742d565ff61c",  # Amazon Linux 2 x86_64 for us-west-2
#     #     MinCount=1,
#     #     MaxCount=1,
#     #     InstanceType="t3.micro",
#     #     KeyName="autoops-key",  # your EC2 key pair name
#     #     SecurityGroupIds=["sg-05b93c1804021efe6"],  # must allow inbound 5001
#     #     UserData=f"""#!/bin/bash
#     #     exec > /home/ec2-user/startup.log 2>&1

#     #     yum update -y
#     #     yum install -y python3 python3-pip git
#     #     export PATH=$PATH:/usr/local/bin

#     #     pip3 install flask boto3 tomli

#     #     cd /home/ec2-user
#     #     git clone https://github.com/Preet37/AutoOps.git
#     #     cd AutoOps
#     #     git checkout additional-functionality
#     #     cd backend/simulated_servers

#     #     nohup python3 service.py {service_name} {config_filename} > service.log 2>&1 &
#     #     """,
#     #     TagSpecifications=[{
#     #         "ResourceType": "instance",
#     #         "Tags": [{"Key": "Name", "Value": f"{service_name}-instance"}],
#     #     }],
#     # )
    
#     instances = ec2.create_instances(
#     ImageId="ami-0e6af742d565ff61c",  # Amazon Linux 2 x86_64 for us-west-2
#     MinCount=1,
#     MaxCount=1,
#     InstanceType="t3.micro",
#     KeyName="autoops-key",  # your EC2 key pair name
#     SecurityGroupIds=["sg-05b93c1804021efe6"],  # must allow inbound 5001
#     UserData=f"""#!/bin/bash
# exec > /home/ec2-user/startup.log 2>&1
# yum update -y
# yum install -y python3-pip git -y
# pip3 install flask boto3 tomli

# cd /home/ec2-user
# git clone https://github.com/Preet37/AutoOps.git
# cd AutoOps
# git checkout additional-functionality
# cd backend/simulated_servers

# nohup python3 service.py {service_name} {config_filename} > /home/ec2-user/service.log 2>&1 &
# """,
#     TagSpecifications=[{
#         "ResourceType": "instance",
#         "Tags": [{"Key": "Name", "Value": f"{service_name}-instance"}],
#     }],
#     )

#     instance = instances[0]
#     INSTANCE_ID = instance.id

#     print("🚀 Launching EC2 instance, waiting for it to start...")
#     instance.wait_until_running()

#     # Wait for public IP
#     for _ in range(10):
#         instance.reload()
#         if instance.public_ip_address:
#             break
#         time.sleep(3)

#     print(f"✅ EC2 started: {instance.id}, public IP: {instance.public_ip_address}")
#     return instance.public_ip_address


# def terminate_ec2(instance_id: str):
#     """Terminate the specified EC2 instance."""
#     if not instance_id:
#         print("⚠️ No EC2 instance to terminate.")
#         return

#     ec2 = boto3.client("ec2", region_name="us-west-2")
#     ec2.terminate_instances(InstanceIds=[instance_id])
#     print(f"🛑 Terminated instance {instance_id}")


# def cleanup():
#     """Cleanup handler triggered when the launcher exits."""
#     terminate_ec2(INSTANCE_ID)


# # ------------------------------------------------------------
# # 🏁 Entry Point
# # ------------------------------------------------------------
# if __name__ == "__main__":
#     if len(sys.argv) < 3:
#         print("Usage: python launch_ec2.py <service_name> <config_filename>")
#         sys.exit(1)

#     service_name = sys.argv[1]
#     config_filename = sys.argv[2]

#     ip = launch_ec2_instance(service_name, config_filename)
#     print(f"Service will run remotely on EC2 at {ip}")

#     atexit.register(cleanup)
#     app.run(host="0.0.0.0", port=3000, debug=False, use_reloader=False)

