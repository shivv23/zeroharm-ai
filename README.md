# ZeroHarm AI — Industrial Safety Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**ZeroHarm AI** is a multi-agent industrial safety intelligence platform that detects compound risks before they become catastrophes. Built for the **ET AI Hackathon 2026** — Problem Statement 1: AI-Powered Industrial Safety Intelligence for Zero-Harm Operations.

---

## The Problem

On January 20, 2025, the Visakhapatnam Steel Plant suffered a catastrophic explosion. Eight workers died. Twelve were injured. The root cause? Gas pressure sensors showed warning signals — but no intelligence layer connected those readings to operational decisions. A permit-to-work was issued without checking real-time sensor data. Maintenance proceeded despite abnormal gas accumulation.

**Sensor data without an intelligence layer is just noise.**

---

## The Solution

ZeroHarm AI bridges the gap between raw sensor data and safety-critical decisions through a multi-agent architecture:

- **Compound Risk Detection Engine** correlates sensor readings, permit activity, and maintenance status to detect compound risks — conditions where multiple minor issues combine into a critical threat
- **Digital Twin Aggregator** combines all subsystems into a unified plant health dashboard
- **Real-time WebSocket push** delivers risk scores, alerts, and health metrics every 2 seconds
- **Interactive simulation** through What-If and Emergency Response modules
- **Machine Learning** for anomaly detection (Isolation Forest) and predictive risk forecasting

---

## Features

| Feature | Description |
|---------|-------------|
| **Geospatial Risk Heatmap** | SVG plant layout with 10 zone-level risk color coding and sensor/permit overlays |
| **Compound Risk Detection** | Multi-factor correlation engine for early warning of cascading failures |
| **Permit-to-Work Intelligence** | Active permit tracking with risk levels and zone overlap detection |
| **Emergency Response Orchestration** | Trigger → mustering → event log → resolution lifecycle |
| **What-If Simulator** | Pre-built and custom scenario modeling with live risk impact |
| **Root Cause Analysis** | Causal chain engine with 5-Why analysis, confidence scoring, and recommendations |
| **Digital Twin Dashboard** | Unified plant health view with sensor, permit, zone, and compliance KPIs |
| **Cost of Safety Dashboard** | Financial translation of incidents — total cost, fines, risk exposure, prevention savings |
| **Anomaly Detection** | Isolation Forest on sensor history with z-score confidence (graceful sklearn fallback) |
| **Predictive Risk Forecast** | 5-step trend projection with direction indicators |
| **Incident Pattern Intelligence** | Historical incident analysis with frequency, type, and trend discovery |
| **Incident Investigation + CAPA** | Full investigation workflow with findings and Corrective/Preventive Actions |
| **Personnel Tracker** | Zone occupancy, location tracking, hazard exposure, mustering drills |
| **Environmental Dashboard** | Per-zone air quality monitoring (CO, NOx, SO2, PM, VOCs) and compliance |
| **Equipment Health Monitor** | Real-time equipment status and maintenance prioritization |
| **Safety Observations** | Worker-submitted hazard reports with type/severity classification and trends |
| **Alert Triage Engine** | Per-alert urgency scoring with recommended response actions |
| **AI Chat Assistant** | Natural-language query interface with live plant context injection |
| **Compliance Audit Agent** | Automated 32-check audits with weighted scoring and regulatory mapping |
| **Plant Health Index** | Composite KPI (sensor + permit + risk + compliance) |
| **Agent Activity Feed** | Real-time scrolling multi-agent trace |
| **Regulatory Reporter** | Automated PDF report generation against OSHA, EPA, ISO, NFPA standards |
| **Admin Panel** | RBAC user management (4 roles), audit trail, activity stats |
| **Analytics Dashboard** | High-level KPIs, severity breakdown, zone comparison, risk trends |
| **JWT Auth + RBAC** | Bcrypt password hashing, 4 permission roles with route-level guards |
| **Database Persistence** | SQLite via SQLAlchemy async — state survives restarts via `session.merge()` |

> **Note:** All sensor data, alerts, and compliance outputs are generated in real-time by the synthetic simulation engine (80+ sensors across 10 zones, updated every 2 seconds). Marked with `data_source: simulated` in every API response.

---

## Architecture

```
Frontend (React 18) ←── WebSocket + REST ──→ API Gateway (FastAPI)
                                                   │
                                         Orchestration Layer
                                         ├── Compound Risk Detection Engine
                                         │   ├── Sensor Monitor Agent
                                         │   ├── Permit Activity Agent
                                         │   ├── Maintenance Status Agent
                                         │   └── Fusion Supervisor
                                         ├── Digital Twin Aggregator
                                         ├── Emergency Response Orchestrator
                                         ├── What-If Simulator
                                         ├── Root Cause Analyzer
                                         ├── Quality & Compliance Audit Agent
                                         ├── Incident Pattern Intelligence
                                         ├── Incident Investigation Engine
                                         ├── Anomaly Detector (Isolation Forest)
                                         ├── Predictive Risk Forecaster
                                         ├── Alert Triage Engine
                                         ├── Equipment Health Monitor
                                         ├── Safety Observation System
                                         ├── Environmental Monitor
                                         ├── Personnel Tracker
                                         ├── Chat Assistant
                                         └── Report Generator (ReportLab)
                                                   │
                                          Synthetic Data Generator
                                           (80 sensors, 10 zones)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Webpack 5, SVG, CSS-in-JS |
| Backend | Python 3.13 FastAPI + Uvicorn |
| Communication | WebSocket (real-time push) + REST API |
| ML | scikit-learn (Isolation Forest, optional) |
| Optional ML | sentence-transformers, ultralytics YOLO, opencv-python |
| Data Generation | NumPy |
| Database | SQLite + SQLAlchemy async |
| Auth | JWT + bcrypt |
| PDF | ReportLab |
| Containerization | Docker, docker-compose |

---

## Quick Start

### Option 1: Docker

```bash
docker compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:8080
# API docs: http://localhost:8000/docs
```

### Option 2: Manual

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm start
```

### Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| safety_officer | safety_officer123 | safety_officer |
| operator | operator123 | operator |
| viewer | viewer123 | viewer |

---

## API Documentation

Interactive Swagger docs at `http://localhost:8000/docs` when the backend is running.

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/auth/login` | POST | JWT login |
| `/api/auth/register` | POST | Register user |
| `/api/auth/me` | GET | Current user info |
| `/api/auth/refresh` | POST | Refresh JWT token |
| `/api/plant/state` | GET | Current plant sensor and permit state |
| `/api/risk/current` | GET | Current risk analysis |
| `/api/risk/alerts` | GET | Active alerts |
| `/api/risk-trend` | GET | Risk score time-series |
| `/api/sensors` | GET | All sensor readings |
| `/api/permits` | GET | Active permits |
| `/api/compliance/audit` | GET | Quality & compliance audit |
| `/api/compliance/trend` | GET | Compliance history |
| `/api/health-index` | GET | Composite plant health score |
| `/api/digital-twin` | GET | Digital Twin aggregated dashboard |
| `/api/cost-of-safety` | GET | Financial cost analysis |
| `/api/anomalies` | GET | Sensor anomaly detection results |
| `/api/forecast` | GET | Predictive risk forecast (5-step) |
| `/api/safety-scores` | GET | Per-zone safety score leaderboard |
| `/api/personnel/locations` | GET | Personnel zone locations |
| `/api/personnel/occupancy` | GET | Zone occupancy counts |
| `/api/personnel/hazard-exposure` | GET | Hazard exposure by zone |
| `/api/personnel/mustering/trigger` | POST | Trigger mustering drill |
| `/api/environmental/metrics` | GET | Environmental monitoring metrics |
| `/api/environmental/compliance` | GET | Environmental compliance status |
| `/api/safety/observations` | GET | Safety observations list |
| `/api/safety/observations/trends` | GET | Observation trends |
| `/api/safety/observations/submit` | POST | Submit safety observation |
| `/api/maintenance/equipment-health` | GET | Equipment health status |
| `/api/alerts/triage` | GET | Alert triage assessment |
| `/api/alerts/triage` | POST | Resolve alert with action |
| `/api/chat` | POST | Chat assistant query |
| `/api/users` | GET | List users (admin) |
| `/api/users/create` | POST | Create user (admin) |
| `/api/users/reset-password` | POST | Reset user password (admin) |
| `/api/audit/log` | GET | Audit trail log (admin) |
| `/api/audit/stats` | GET | Audit statistics (admin) |
| `/api/analytics/summary` | GET | Analytics dashboard summary |
| `/api/kg/query` | GET | Knowledge graph query |
| `/api/what-if/scenarios` | GET | List available scenarios |
| `/api/what-if/apply` | POST | Apply a built-in scenario |
| `/api/what-if/custom` | POST | Apply a custom scenario |
| `/api/what-if/reset` | POST | Reset to normal operations |
| `/api/emergency/trigger` | POST | Trigger emergency response |
| `/api/emergency/active` | GET | Active emergencies |
| `/api/incident-patterns` | GET | Incident patterns and statistics |
| `/api/incident/root-cause` | GET | Root cause analysis |
| `/api/investigation/list` | GET | List investigations |
| `/api/investigation/create` | POST | Create investigation |
| `/api/investigation/{id}/finding` | POST | Add finding to investigation |
| `/api/investigation/{id}/capa` | POST | Create CAPA item |
| `/api/capa/statistics` | GET | CAPA statistics |
| `/api/capa/open` | GET | Open CAPA items |
| `/api/reports/regulatory/{std_id}` | GET | PDF regulatory report |
| `/api/reports/compliance` | GET | PDF compliance report |
| `/api/reports/incident/{id}` | GET | PDF incident report |
| `/api/reports/risk` | GET | PDF risk assessment |
| `/api/activity-feed` | GET | Multi-agent activity log |
| `/ws` | WebSocket | Real-time state updates (2s interval) |

---

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

56 pytest tests covering: risk engine, compliance audit, what-if simulator, emergency response, incident patterns, digital twin, anomaly detection, root cause analysis, and synthetic data generator.

---

## Project Structure

```
zeroharm-ai/
├── backend/
│   ├── api/main.py                    # FastAPI server + WebSocket
│   ├── agents/
│   │   ├── compound_risk_engine.py
│   │   ├── sensor_monitor_agent.py
│   │   ├── permit_activity_agent.py
│   │   ├── maintenance_status_agent.py
│   │   ├── quality_compliance_agent.py
│   │   └── agent_activity_feed.py
│   ├── data/
│   │   └── synthetic_data_generator.py
│   ├── digital_twin.py
│   ├── cost_of_safety.py
│   ├── anomaly_detector.py
│   ├── predictive_risk.py
│   ├── root_cause.py
│   ├── chat_assistant.py
│   ├── personnel_tracker.py
│   ├── environmental_monitor.py
│   ├── safety_observation_system.py
│   ├── equipment_health_monitor.py
│   ├── alert_triage_engine.py
│   ├── report_generator.py
│   ├── what_if_simulator.py
│   ├── emergency_response.py
│   ├── incident_investigation.py
│   ├── incident_pattern_intelligence.py
│   ├── rag/
│   │   ├── rag_pipeline.py
│   │   └── semantic_search.py
│   ├── knowledge_graph/
│   ├── auth/auth_manager.py
│   ├── vision/integration.py
│   ├── config/
│   ├── constants.py
│   ├── config_loader.py
│   ├── database.py
│   └── alert_dispatcher.py
├── frontend/
│   ├── public/
│   └── src/
│       ├── App.js
│       ├── components/           # 25+ UI components
│       │   ├── GeospatialHeatmap.js
│       │   ├── RiskPanel.js
│       │   ├── AlertPanel.js
│       │   ├── DigitalTwinDashboard.js
│       │   ├── CostOfSafetyDashboard.js
│       │   ├── AnomalyPanel.js
│       │   ├── ChatWidget.js
│       │   ├── SafetyGamification.js
│       │   ├── AdminPanel.js
│       │   ├── AnalyticsDashboard.js
│       │   └── ... (15+ more)
│       └── store/
│           ├── websocketStore.js
│           ├── theme.js
│           ├── apiRoutes.js
│           └── authFetch.js
├── render.yaml                   # Render deployment config
├── docker-compose.yml
└── Makefile
```

---

## Deployment

### Render (Free Tier)

The application is configured for deployment on Render using `render.yaml`:

- **Backend:** `uvicorn` ASGI server via `gunicorn -k uvicorn.workers.UvicornWorker`
- **Frontend:** Static site with SPA rewrite rule for client-side routing
- **Memory:** 512MB starter plan
- **Graceful degradation:** Heavy ML dependencies (sentence-transformers, ultralytics, opencv-python) are optional — the app functions fully without them

Set the following environment variables:
- `JWT_SECRET` — Secret key for token signing
- `ALLOWED_ORIGINS` — Comma-separated CORS origins
- `API_KEY` — Optional API key for external service auth

---

## License

MIT
