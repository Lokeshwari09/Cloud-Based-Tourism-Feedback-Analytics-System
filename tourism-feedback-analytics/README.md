# Cloud-Based Tourism Feedback Analytics System

A cloud-native web application that collects tourist feedback, runs sentiment and topic analysis,
and shows live analytics (sentiment split, destination scores, topic scores, keywords) on a dashboard.
Containerised with **Docker**, deployable on **AWS EC2** (or an **Oracle VirtualBox** VM), and capacity-tested
with **CloudSim**.

## 1. Architecture

```
Tourist / Admin (browser)
        |  HTTP
        v
 [ AWS Security Group / VirtualBox port-forward ]
        v
 [ Docker container: Gunicorn + Flask ]  --->  /api/feedback, /api/stats, /api/upload, /export.csv
        |                                      Analyzer (sentiment + topic rules)
        v
 [ SQLite on Docker volume /data ]   (upgrade path: Amazon RDS / S3 for CSV storage)
```
Cloud concepts covered: SaaS delivery, containerisation, IaaS deployment (EC2 / VirtualBox VM),
horizontal scalability (CloudSim), persistent storage, REST APIs, health checks.

## 2. Project structure

```
tourism-feedback-analytics/
├── app/
│   ├── app.py            Flask REST API + DB
│   ├── analyzer.py       Sentiment + topic + keyword analysis
│   └── templates/index.html   Dashboard (Chart.js)
├── cloudsim/TourismCloudSim.java   Load/scalability simulation
├── sample_feedback.csv   Bulk-upload sample
├── Dockerfile, docker-compose.yml, requirements.txt
└── .vscode/launch.json   F5 debug config
```

## 3. Run in VS Code (no Docker)

```bash
cd tourism-feedback-analytics
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python app/app.py
```
Open http://localhost:5000 (or press **F5** in VS Code). The app seeds 12 sample reviews on first run.

## 4. Run with Docker

```bash
docker compose up --build
```
Open http://localhost:5000. Data persists in the `feedback-data` volume. Stop with `docker compose down`.

## 5. Test the API

```bash
curl -X POST http://localhost:5000/api/feedback -H "Content-Type: application/json" \
     -d '{"destination":"Munnar","rating":5,"comment":"Beautiful views and friendly staff"}'
curl http://localhost:5000/api/stats
curl -F "file=@sample_feedback.csv" http://localhost:5000/api/upload
```

## 6. Deploy on AWS (console)

1. **EC2 > Launch instance**: Ubuntu 22.04, `t2.micro` (free tier), create/download a key pair.
2. **Security group**: inbound SSH (22) from *My IP*, custom TCP **5000** (or 80) from anywhere.
3. Connect, install Docker and run:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
   sudo usermod -aG docker $USER && newgrp docker
   # copy the project (git clone or scp), then:
   cd tourism-feedback-analytics && docker compose up -d --build
   ```
4. Browse to `http://<EC2-public-IP>:5000`. Health check: `/health`.
5. Optional extensions: **S3** bucket for CSV exports, **RDS** instead of SQLite, **ALB + Auto Scaling Group**
   for multiple instances, **CloudWatch** for logs/alarms. Stop/terminate the instance afterwards to avoid charges.

## 7. Deploy on Oracle VirtualBox (alternative)

1. Create an Ubuntu Server VM (2 CPU, 2 GB RAM, 20 GB disk), network mode **NAT**.
2. Settings > Network > Advanced > **Port Forwarding**: Host 5000 -> Guest 5000.
3. Inside the VM install Docker (same commands as step 6.3) and run `docker compose up -d --build`.
4. Open http://localhost:5000 on the host machine.

## 8. CloudSim simulation (scalability analysis)

Requires JDK 8+ and the CloudSim 3.0.3 jar (https://github.com/Cloudslab/cloudsim/releases).
```bash
cd cloudsim
javac -cp cloudsim-3.0.3.jar TourismCloudSim.java
java  -cp .;cloudsim-3.0.3.jar TourismCloudSim 2 40     # Windows  (Linux/Mac use ':' instead of ';')
java  -cp .;cloudsim-3.0.3.jar TourismCloudSim 4 40
java  -cp .;cloudsim-3.0.3.jar TourismCloudSim 8 40
```
Run with 2, 4 and 8 VMs and compare **makespan** and average CPU time. This shows how scaling out VMs reduces
processing time for feedback-analysis jobs and supports your auto-scaling discussion. In VS Code, install the
*Extension Pack for Java* and add the jar under `.vscode/settings.json > java.project.referencedLibraries`.

## 9. Suggested report sections

Introduction, Problem statement, Objectives, Architecture (diagram above), Cloud service/deployment model
(SaaS on IaaS, public cloud), Implementation, Screenshots (dashboard, Docker, EC2 console, CloudSim output),
Results of VM-scaling table, Security (security groups, HTTPS via ALB, IAM), Cost estimate, Conclusion & future work
(ML models such as BERT, multilingual feedback, Amazon Comprehend, auto-scaling).
