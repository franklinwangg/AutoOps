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
    
    instances = ec2.create_instances(
    ImageId="ami-0e6af742d565ff61c",  # Amazon Linux 2 x86_64 for us-west-2
    MinCount=1,
    MaxCount=1,
    InstanceType="t3.micro",
    KeyName="my-ec2-key",  # your EC2 key pair name
    SecurityGroupIds=["sg-05b93c1804021efe6"],  # must allow inbound 5001
#     UserData=f"""#!/bin/bash
# exec > /home/ec2-user/startup.log 2>&1

# # --- System setup ---
# yum update -y
# yum install -y python3 python3-pip git -y
# pip3 install flask boto3 tomli

# # --- Clone your repository ---
# cd /home/ec2-user
# git clone https://github.com/Preet37/AutoOps.git
# cd AutoOps

# # --- Checkout the correct branch ---
# git checkout additional-functionality

# # --- Move into the service directory ---
# cd backend/agent

# # --- Run your service ---
# nohup python3 healer.py > /home/ec2-user/healer.log 2>&1 &
# nohup python3 monitor.py > /home/ec2-user/monitor.log 2>&1 &
# """,
        UserData=f"""#!/bin/bash
exec > /home/ec2-user/startup.log 2>&1

# --- System setup ---
yum update -y
amazon-linux-extras enable python3.8
yum install -y python3.8 python3.8-pip git aws-cli -y

# --- Install Python dependencies (using 3.8) ---
pip3.8 install --upgrade pip
pip3.8 install flask boto3 requests

# --- AWS IAM role setup for Bedrock ---
ROLE_NAME="AutoOpsEC2BedrockRole"
PROFILE_NAME="AutoOpsEC2Profile"

# Create trust policy for EC2
cat > /home/ec2-user/trust-policy.json <<'EOF'
{{
  "Version": "2012-10-17",
  "Statement": [
    {{
      "Effect": "Allow",
      "Principal": {{
        "Service": "ec2.amazonaws.com"
      }},
      "Action": "sts:AssumeRole"
    }}
  ]
}}
EOF

# Create IAM role if it doesn't exist
if ! aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1; then
  aws iam create-role --role-name $ROLE_NAME \
    --assume-role-policy-document file:///home/ec2-user/trust-policy.json
  aws iam attach-role-policy --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
  aws iam attach-role-policy --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
fi

# Create instance profile if needed
if ! aws iam get-instance-profile --instance-profile-name $PROFILE_NAME >/dev/null 2>&1; then
  aws iam create-instance-profile --instance-profile-name $PROFILE_NAME
  aws iam add-role-to-instance-profile --instance-profile-name $PROFILE_NAME \
    --role-name $ROLE_NAME
fi

# Get current instance ID and associate the profile
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
aws ec2 associate-iam-instance-profile \
  --instance-id "$INSTANCE_ID" \
  --iam-instance-profile Name=$PROFILE_NAME || true

# --- Clone your repository ---
cd /home/ec2-user
git clone https://github.com/Preet37/AutoOps.git
cd AutoOps

# --- Checkout the correct branch ---
git checkout additional-functionality

# --- Create data directory ---
mkdir -p /home/ec2-user/AutoOps/data
chmod 777 /home/ec2-user/AutoOps/data

# --- Move into the service directory ---
cd backend/agent

# --- Run your services using Python 3.8 ---
nohup python3.8 healer.py > /home/ec2-user/healer.log 2>&1 &
nohup python3.8 monitor.py > /home/ec2-user/monitor.log 2>&1 &
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