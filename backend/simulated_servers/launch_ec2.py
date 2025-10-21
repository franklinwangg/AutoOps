# launch_ec2.py
import boto3
import time
import sys
from flask import Flask, jsonify

import atexit

INSTANCE_ID = None
app = Flask(__name__)


def launch_ec2_instance(service_name: str, config_filename: str) -> str:
    """Launch a new EC2 instance and start the specified service remotely."""
    global INSTANCE_ID

    ec2 = boto3.resource("ec2", region_name="us-west-2")

    # instances = ec2.create_instances(
    #     ImageId="ami-0e6af742d565ff61c",  # Amazon Linux 2 x86_64 for us-west-2
    #     MinCount=1,
    #     MaxCount=1,
    #     InstanceType="t3.micro",
    #     KeyName="autoops-key",  # your EC2 key pair name
    #     SecurityGroupIds=["sg-05b93c1804021efe6"],  # must allow inbound 5001
    #     UserData=f"""#!/bin/bash
    #     exec > /home/ec2-user/startup.log 2>&1

    #     yum update -y
    #     yum install -y python3 python3-pip git
    #     export PATH=$PATH:/usr/local/bin

    #     pip3 install flask boto3 tomli

    #     cd /home/ec2-user
    #     git clone https://github.com/Preet37/AutoOps.git
    #     cd AutoOps
    #     git checkout additional-functionality
    #     cd backend/simulated_servers

    #     nohup python3 service.py {service_name} {config_filename} > service.log 2>&1 &
    #     """,
    #     TagSpecifications=[{
    #         "ResourceType": "instance",
    #         "Tags": [{"Key": "Name", "Value": f"{service_name}-instance"}],
    #     }],
    # )
    
    instances = ec2.create_instances(
    ImageId="ami-0e6af742d565ff61c",  # Amazon Linux 2 x86_64 for us-west-2
    MinCount=1,
    MaxCount=1,
    InstanceType="t3.micro",
    KeyName="autoops-key",  # your EC2 key pair name
    SecurityGroupIds=["sg-05b93c1804021efe6"],  # must allow inbound 5001
#     UserData="""#!/bin/bash
# exec > /home/ec2-user/startup.log 2>&1
# yum update -y
# yum install -y python3-pip -y
# pip3 install flask

# cat << 'EOF' > /home/ec2-user/test_server.py
# from flask import Flask
# app = Flask(__name__)

# @app.route('/')
# def index():
#     return "hello world from ec2"

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=3000)
# EOF

# nohup python3 /home/ec2-user/test_server.py > /home/ec2-user/test_server.log 2>&1 &
# """,
    UserData=f"""#!/bin/bash
exec > /home/ec2-user/startup.log 2>&1

# --- System setup ---
yum update -y
yum install -y python3 python3-pip git
pip3 install flask boto3

# --- Clone your repository ---
cd /home/ec2-user
git clone https://github.com/Preet37/AutoOps.git
cd AutoOps/backend/simulated_servers

# --- Run your service ---
nohup python3 service.py {service_name} {config_filename} > /home/ec2-user/service.log 2>&1 &
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

    # Wait for public IP
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
    """Cleanup handler triggered when the launcher exits."""
    terminate_ec2(INSTANCE_ID)


# ------------------------------------------------------------
# 🏁 Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python launch_ec2.py <service_name> <config_filename>")
        sys.exit(1)

    service_name = sys.argv[1]
    config_filename = sys.argv[2]

    ip = launch_ec2_instance(service_name, config_filename)
    print(f"Service will run remotely on EC2 at {ip}")

    atexit.register(cleanup)
    app.run(host="0.0.0.0", port=3000, debug=False, use_reloader=False)