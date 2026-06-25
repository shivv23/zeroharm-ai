# ZeroHarm AI — Architecture Diagram

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                             ZEROHARM AI PLATFORM                                      │
│                     Industrial Safety Intelligence System                              │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                         PRESENTATION LAYER (React)                            │   │
│  │  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │   │
│  │  │ Geospatial   │  │ Alert & Risk   │  │ Permit       │  │ Emergency      │  │   │
│  │  │ Heatmap      │  │ Dashboard      │  │ Intelligence │  │ Response UI    │  │   │
│  │  │ (Leaflet/SVG)│  │ (real-time)    │  │ (Compliance)  │  │ (Timeline)     │  │   │
│  │  └──────┬───────┘  └────────┬───────┘  └──────┬───────┘  └───────┬──────────┘  │   │
│  └─────────┴──────────────────┴──────────────────┴──────────────────┴─────────────┘   │
│            │                         ▲                         │                      │
│            │  WebSocket (ws://)      │      REST API (HTTP)    │                      │
│            ▼                         │                         ▼                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                      API GATEWAY (FastAPI + Uvicorn)                         │   │
│  │  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │   │
│  │  │ /api/plant/* │  │ /api/risk/*   │  │ /api/kg/*    │  │ /api/rag/*     │  │   │
│  │  │ /api/sensors │  │ /api/permits  │  │ /api/incident│  │ /api/emergency │  │   │
│  │  └──────────────┘  └────────────────┘  └──────────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                        │
├────────────┼────────────────────────────────────────────────────────────────────────┤
│            ▼                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                      ORCHESTRATION LAYER (Python)                             │   │
│  │                                                                              │   │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │              Compound Risk Detection Engine                              │ │   │
│  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │ │   │
│  │  │  │ Sensor Monitor   │  │ Permit Activity  │  │ Maintenance     │       │ │   │
│  │  │  │ Agent            │  │ Agent            │  │ Status Agent     │       │ │   │
│  │  │  │ • Reads sensor   │  │ • Tracks active  │  │ • Equipment in   │       │ │   │
│  │  │  │   data           │  │   permits        │  │   maintenance    │       │ │   │
│  │  │  │ • Flags abnormal │  │ • Identifies     │  │ • By-pass status │       │ │   │
│  │  │  │   conditions     │  │   overlapping    │  │ • Conflict check │       │ │   │
│  │  │  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘       │ │   │
│  │  │           └──────────────────────┴─────────────────────┘                │ │   │
│  │  │                              ▼                                          │ │   │
│  │  │                   ┌──────────────────────┐                              │ │   │
│  │  │                   │   Fusion & Ranking   │                              │ │   │
│  │  │                   │   Supervisor Agent   │                              │ │   │
│  │  │                   │ • Risk score fusion  │                              │ │   │
│  │  │                   │ • Alert prioritization│                             │ │   │
│  │  │                   │ • Compound risk flag │                              │ │   │
│  │  │                   └──────────────────────┘                              │ │   │
│  │  └──────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                              │   │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │  Permit Intelligence Agent (RAG)         │  Emergency Response           │ │   │
│  │  │  • RAG over regulatory docs              │  Orchestrator                 │ │   │
│  │  │  • Compliance checking                   │  • Multi-channel dispatch     │ │   │
│  │  │  • Sensor-permit cross-reference         │  • Evacuation protocol        │ │   │
│  │  │  • Recommendation generation             │  • Incident report generation │ │   │
│  │  └──────────────────────────────────────────┘  • Timeline tracking          │ │   │
│  │  ┌──────────────────────────────────────────┐  └────────────────────────────┘ │   │
│  │  │  Incident Pattern Intelligence           │                                  │   │
│  │  │  • Historical incident analysis          │  ┌────────────────────────────┐  │   │
│  │  │  • Pattern discovery (zone, cause, type) │  │ Knowledge Graph            │  │   │
│  │  │  • Prevention recommendations            │  │ • NetworkX-based           │  │   │
│  │  │  • Trend statistics                      │  │ • Zone-Eq-Permit-Regulation│  │   │
│  │  └──────────────────────────────────────────┘  │ • Compound risk paths      │  │   │
│  │                                                │ • Query engine             │  │   │
│  │                                                └────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                      DATA FUSION LAYER                                        │   │
│  │                                                                              │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────┐     │   │
│  │  │ Synthetic Data   │  │ Real Sensor Data │  │ Regulatory Documents  │     │   │
│  │  │ Generator        │  │ (simulated)      │  │ • OISD Standards      │     │   │
│  │  │ • 8 sensor types │  │ • 10 plant zones │  │ • Factory Act 1948    │     │   │
│  │  │ • 10 zones       │  │ • 80+ sensors    │  │ • DGMS Circulars      │     │   │
│  │  │ • Permit lifecycle│  │ • Live WebSocket │  │ • ISO 45001           │     │   │
│  │  │ • Incident replay │  │ • 2s update rate│  │ • Safety Best Practices│     │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
[Sensor Data] ──► Sensor Monitor Agent ──┐
[Permit Data] ──► Permit Activity Agent ──┼──► Fusion & Ranking ──► Geospatial Heatmap
[Maintenance] ──► Maintenance Agent ──────┘         │                    + Risk Panel
                                                     │
                                                     ├──► Alert Panel (real-time alerts)
                                                     │
                                                     ├──► Permit Intelligence (RAG check)
                                                     │
                                                     └──► Emergency Orchestrator (on trigger)
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + Leaflet | Geospatial heatmap, dashboards |
| State | WebSocket (ws://) | Real-time bidirectional data flow |
| Backend | FastAPI + Uvicorn | REST API + WebSocket server |
| Agent Framework | Multi-Agent Orchestrator (Python) | Parallel agent fusion pipeline |
| Knowledge Graph | NetworkX | Zone-equipment-permit relationships |
| Vector / RAG | Chroma + Sentence Transformers | Regulatory document retrieval |
| Data Generation | NumPy + Pandas | Synthetic industrial data |
| Simulation | Async event loop | 2-second update cycle |

## Key Integration Points

1. **Agent Fusion Pipeline**: 3 independent agents → one supervisor → fused risk score + prioritized alerts
2. **RAG + Knowledge Graph Hybrid**: Compounding detection uses KG for regulatory context + RAG for detailed compliance
3. **Real-Time WebSocket Architecture**: Every simulation step pushes state + risk to all connected clients
4. **Emergency Response State Machine**: Trigger → dispatch → track → resolve with full audit trail

## Component Relationships

```
SyntheticDataGenerator
  ├── generates: sensors (80+), permits (dynamic), zone risks
  └── consumed by: CompoundRiskEngine, API endpoints

CompoundRiskDetectionEngine
  ├── SensorMonitorAgent → reads sensor values, flags anomalies
  ├── PermitActivityAgent → tracks permits, detects overlaps
  ├── MaintenanceStatusAgent → equipment status, bypass detection
  └── Fusion Supervisor → composite scoring, alert generation

RAGPipeline
  ├── regulatory docs (embedded in code)
  ├── search(query) → ranked document results
  └── query_permit_compliance(permit_type, sensors) → violation report

EmergencyResponseOrchestrator
  ├── trigger(type, context) → multi-channel dispatch + timeline
  ├── resolve(id, notes) → closure + audit trail
  └── _generate_incident_report() → regulatory-compliant PDF-ready report

IncidentPatternIntelligence
  ├── 8 historical incident records (real patterns)
  ├── _discover_patterns() → zone/cause/type clustering
  └── get_prevention_recommendations() → actionable insights
```
