# ZeroHarm AI — Industrial Safety Intelligence Platform

An AI-powered multi-agent platform for real-time industrial safety monitoring, compound risk detection, and emergency response orchestration.

> **Built for the ET AI Hackathon 2026 — Problem Statement 1: AI-Powered Industrial Safety Intelligence for Zero-Harm Operations**

## Features

- **Geospatial Risk Heatmap** — SVG-based plant layout with zone-level risk visualization
- **Multi-Agent Risk Detection** — 3 parallel agents (Sensor Monitor, Permit Activity, Maintenance Status) fused by a supervisor for compound risk scoring
- **Permit-to-Work Intelligence** — Regulatory compliance checking against OISD, Factory Act 1948, DGMS, and ISO 45001 standards
- **Emergency Response Orchestration** — Multi-channel alert dispatch, evacuation protocol, rescue team coordination, and incident report generation
- **Incident Pattern Intelligence** — Historical incident analysis with recurring zone, cause, and type pattern discovery
- **What-If Scenario Simulator** — Pre-built safety scenarios (Vizag 2025 replay, gas leak cascade, fire, confined space near-miss, LOTO failure) plus a custom scenario builder
- **Quality & Compliance Audit** — 32 compliance checks across 5 categories with weighted scoring and critical finding detection
- **Predictive Risk Trends** — Time-series risk score chart with gradient visualization
- **Plant Health Index** — Composite KPI combining sensor, permit, risk, and compliance health
- **Real-Time Activity Feed** — Scrollable multi-agent trace with severity-coded entries
- **Public WebSocket API** — Real-time state push with 2-second update intervals

## Architecture

```
Frontend (React) ←── WebSocket/REST ──→ API Gateway (FastAPI)
                                              │
                                    Orchestration Layer
                                    ├── Compound Risk Detection Engine
                                    │   ├── Sensor Monitor Agent
                                    │   ├── Permit Activity Agent
                                    │   ├── Maintenance Status Agent
                                    │   └── Fusion Supervisor
                                    ├── RAG Pipeline (Regulatory Compliance)
                                    ├── Emergency Response Orchestrator
                                    ├── Incident Pattern Intelligence
                                    ├── What-If Simulator
                                    └── Quality & Compliance Audit Agent
                                              │
                                     Synthetic Data Generator
                                      (80 sensors, 10 zones)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 |
| Backend | FastAPI + Uvicorn |
| WebSocket | Real-time bidirectional state push |
| Knowledge Graph | NetworkX |
| Data Generation | NumPy, Pandas |
| Simulation | Async event loop (2s cycles) |

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

The app runs at `http://localhost:3000` and connects to the backend at `http://localhost:8000`.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/plant/layout` | GET | Plant zone layout |
| `/api/plant/state` | GET | Current plant sensor and permit state |
| `/api/risk/current` | GET | Current risk analysis |
| `/api/risk/alerts` | GET | Active alerts |
| `/api/risk-trend` | GET | Risk score time-series |
| `/api/sensors` | GET | All sensor data |
| `/api/sensors/zone/{zone_id}` | GET | Sensors by zone |
| `/api/permits` | GET | Active permits |
| `/api/compliance/audit` | GET | Quality & compliance audit |
| `/api/compliance/trend` | GET | Compliance history + recommendations |
| `/api/activity-feed` | GET | Multi-agent activity log |
| `/api/health-index` | GET | Composite plant health score |
| `/api/emergency/trigger` | POST | Trigger emergency response |
| `/api/emergency/active` | GET | Active emergencies |
| `/api/emergency/resolve/{id}` | POST | Resolve emergency |
| `/api/what-if/scenarios` | GET | List available scenarios |
| `/api/what-if/apply` | POST | Apply a built-in scenario |
| `/api/what-if/custom` | POST | Apply a custom scenario |
| `/api/what-if/reset` | POST | Reset to normal operations |
| `/api/rag/permit-compliance` | POST | RAG-based permit compliance check |
| `/api/rag/search` | POST | Search regulatory documents |
| `/api/knowledge-graph` | GET | Knowledge graph data |
| `/api/incident-patterns` | GET | Incident patterns and statistics |
| `/ws` | WebSocket | Real-time state updates (2s interval) |

## Disclaimer

This platform uses **simulated sensor data** for demonstration purposes. All risk scores, alerts, and compliance outputs are generated from synthetic data. It is designed as a proof-of-concept for hackathon evaluation and is not intended for deployment in live industrial environments.

## License

MIT
