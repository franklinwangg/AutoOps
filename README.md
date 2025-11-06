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
Monitor → Healer Agent (Bedrock AI) → Remediation Actions (Restart / Reboot / Scale)

---

## ▶️ Run Locally
```bash
git clone https://github.com/yourusername/AutoOps.git
docker compose up
