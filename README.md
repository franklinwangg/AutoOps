# ⚙️ AutoOps

An AI-powered self-healing infrastructure system that detects, diagnoses, and automatically fixes application or server failures in real time.  
Built to simulate autonomous cloud recovery on a single EC2 instance using Dockerized microservices.

---

## ⚙️ Tech Stack

**Core:** Python, FastAPI, Docker, AWS EC2, CloudWatch  
**AI:** AWS Bedrock (Log Reasoning Agent)  
**Monitoring:** Health checks, log analysis, RCA automation

---

## 🚀 Features

- 🤖 AI-based root cause analysis of logs
- 🔁 Automatic container and service recovery
- 📊 CloudWatch integration for live system health
- 🧱 Multi-container architecture using Docker Compose

---

## 🧩 Architecture

This diagram describes the attachment of two EC2 instances to the healer, but in actuality the healer can attach to and automatically heal any number of EC2 instances. 
![System Architecture Diagram](./docs/architecture-diagram.png)

(1) services are started on EC2 instances, and their health status is posted at their /health endpoint. 
(2) The monitor sends periodic HTTP requests to each service’s /health endpoint, logging response codes and latency. (see Note A for more details)
(3) Periodically, the healer reads the logs of the monitor, and uses AWS Bedrock to analyze them.(see Note B for more details)
(4) Based on AWS Bedrock's decision, the healer performs remediation action.(see Note C for more details)
(5) The logs from the monitor and the actions of the healer are fed into and displayed through the Streamlit frontend.

**Note A.** When a service returns repeated 500 errors or becomes unresponsive, it’s marked unhealthy or “CRASHED.” For OS-level issues, timeouts, failed EC2 instance checks via describe_instance_status, or CloudWatch metrics like zero CPU utilization indicate that the underlying machine or container has failed. 
**Note B.** If health checks fail and EC2 or CloudWatch reports abnormalities, the issue is classified as an OS-level failure (e.g., container crash, instance reboot). If the container responds but returns 500s or has high latency, the problem is considered application-level—such as overload, code bugs, or dependency errors. The healer uses these signals to identify whether it needs to restart the environment or the app logic itself. 4) Based on AWS Bedrock's decision, the healer performs remediation action.
**Note C.** For OS-level failures, it can restart the process, restart the Docker container, or reboot the EC2 instance if the whole VM is unresponsive. For application-level failures, it restarts the service to clear transient issues or starts another container if CloudWatch shows high CPU usage, effectively scaling horizontally. Each fix is chosen based on what the RCA determines.

---

## ▶️ Run Locally

```bash
git clone https://github.com/yourusername/AutoOps.git
docker compose up
```
