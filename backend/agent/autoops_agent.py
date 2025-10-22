import boto3
import time
import os

class AutoOpsAgent:
    def __init__(self, region="us-west-2"):
        self.region = region
        self.ec2 = boto3.resource("ec2", region_name=self.region)
        self.client = boto3.client("ec2", region_name=self.region)

        # Modify these for your setup:
        self.ami_id = "ami-024e4b8b6ef78434a"  # Amazon Linux 2 (example)
        self.instance_type = "t3.micro"
        self.key_name = "my-ec2-key"           # must exist in your AWS account
        self.security_group = "sg-05b93c1804021efe6"

        # self.security_group = ["sg-05b93c1804021efe6"]      # must allow inbound SSH + relevant ports

    def create_instance(self):
        """Launch EC2 with monitor + healer auto-start commands."""
        print("🚀 Launching EC2 instance...")

        user_data_script = """#!/bin/bash
set -e

# Update and install dependencies
yum update -y
yum install -y python3 git

cd /home/ec2-user

# Clone your repo cleanly
rm -rf AutoOps || true
git clone https://github.com/Preet37/AutoOps.git
cd AutoOps
git checkout additional-functionality

# Install Python dependencies compatible with Amazon Linux 2's OpenSSL (1.0.2)
pip3 install 'urllib3<2' 'requests<2.30' 'boto3<1.28' 'botocore<1.31'

# Ensure ec2-user owns everything
chown -R ec2-user:ec2-user /home/ec2-user

# Create logs and set permissions
touch /home/ec2-user/monitor.log /home/ec2-user/healer.log
chmod 666 /home/ec2-user/monitor.log /home/ec2-user/healer.log

# Start services as ec2-user
sudo -u ec2-user -i bash -c 'cd /home/ec2-user/AutoOps/backend/agent && nohup python3 monitor.py > /home/ec2-user/monitor.log 2>&1 &'
sudo -u ec2-user -i bash -c 'cd /home/ec2-user/AutoOps/backend/agent && nohup python3 healer.py > /home/ec2-user/healer.log 2>&1 &'
"""





        
        instance = self.ec2.create_instances(
            ImageId=self.ami_id,
            InstanceType=self.instance_type,
            KeyName=self.key_name,  # 👈 attaches your AWS keypair here
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[self.security_group],
            UserData=user_data_script,
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": "autoops-agent"}]
                }
            ],
        )[0]



        print(f"✅ Instance launching: {instance.id}")
        instance.wait_until_running()
        instance.reload()
        print(f"✅ EC2 running at: {instance.public_dns_name or instance.public_ip_address}")
        return instance

    def describe_instances(self):
        """List all running AutoOps instances."""
        for i in self.ec2.instances.all():
            if i.state["Name"] == "running":
                print(f"{i.id} | {i.public_ip_address} | {i.tags}")

    def terminate_instance(self, instance_id):
        """Stop and terminate a specific instance."""
        print(f"🛑 Terminating {instance_id}...")
        self.client.terminate_instances(InstanceIds=[instance_id])
        print("✅ Termination requested.")


if __name__ == "__main__":
    agent = AutoOpsAgent(region="us-west-2")
    instance = agent.create_instance()
    print("🌐 AutoOps Agent instance ready.")
