# 🚀 Kong Performance Project

This repository showcases a **Kong Gateway performance monitoring platform** I built as part of my university project.  
It demonstrates my skills in API Gateway setup, Docker Compose orchestration, metrics monitoring, and dashboard visualization.

---

## 🧠 Overview

- 🧰 **Tech Stack:**  
  - Kong Gateway 3.4 (Data Plane mode)  
  - Prometheus + Grafana  
  - FastAPI (Python)  
  - Docker Compose  
  - JMeter (for load testing)

- 📊 **Features:**  
  - Real-time API latency, error rate, and throughput monitoring  
  - 95th percentile latency calculation using Prometheus queries  
  - Grafana dashboards for visual analysis  
  - API load testing with JMeter

---

## 🧪 How It Works

1. **Kong Gateway** runs as a data plane connected to Konnect (control plane).  
2. **Prometheus** collects metrics from Kong's `/metrics` endpoint.  
3. **Grafana** visualizes metrics such as request latency, error rate, and throughput.  
4. **FastAPI microservice** exposes custom Prometheus metrics and runs inside Docker.  
5. **JMeter** simulates traffic to evaluate system performance.

---

## 🧰 Project Structure

