import asyncio
import copy
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
import uvicorn

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.synthetic_data_generator import SyntheticDataGenerator
from agents.compound_risk_engine import CompoundRiskDetectionEngine
from agents.quality_compliance_agent import QualityComplianceAuditAgent
from agents.agent_activity_feed import AgentActivityFeed
from knowledge_graph.kg_builder import IndustrialKnowledgeGraph, OISD_STANDARDS
from rag.rag_pipeline import RAGPipeline
from orchestrator.emergency_response import EmergencyResponseOrchestrator
from orchestrator.incident_pattern_intelligence import IncidentPatternIntelligence
from orchestrator.what_if_simulator import WhatIfSimulator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("zeroharm-api")


def flagged_response(content, **kwargs):
    if isinstance(content, dict) and "data_source" not in content:
        content = {**content, "data_source": "simulated"}
    return JSONResponse(content=content, **kwargs)


class ZeroHarmAPI:
    def __init__(self):
        self.generator = SyntheticDataGenerator()
        self.risk_engine = CompoundRiskDetectionEngine()
        self.knowledge_graph = IndustrialKnowledgeGraph()
        self.rag_pipeline = RAGPipeline()
        self.emergency_response = EmergencyResponseOrchestrator()
        self.incident_patterns = IncidentPatternIntelligence()
        self.compliance_agent = QualityComplianceAuditAgent()
        self.activity_feed = AgentActivityFeed()
        self.what_if = WhatIfSimulator()
        self.plant_state = {}
        self.risk_trend = []
        self.active_connections = []
        self.simulation_running = False
        self.scenario_active = False
        self.scenario_state = None
        self.scenario_id = None

    async def _compute_health_index(self, plant_state, risk_result, compliance_result):
        sensors = plant_state.get("sensors", {})
        permits = plant_state.get("active_permits", [])
        s_normal = len([s for s in sensors.values() if s.get("status") == "normal"]) / max(len(sensors), 1)
        permit_health = 1.0 - min(1.0, len([p for p in permits if p.get("risk_level") in ["Critical", "High"]]) * 0.15)
        risk_health = 1.0 - risk_result.get("risk_score", 0)
        compliance_health = compliance_result["overall_compliance_score"] / 100.0 if compliance_result else 1.0
        overall = round((s_normal * 0.25 + permit_health * 0.2 + risk_health * 0.3 + compliance_health * 0.25) * 100, 1)
        return {
            "overall": overall,
            "sensor_health": round(s_normal * 100, 1),
            "permit_health": round(permit_health * 100, 1),
            "risk_health": round(risk_health * 100, 1),
            "compliance_health": round(compliance_health * 100, 1),
            "label": "Excellent" if overall >= 85 else "Good" if overall >= 70 else "Fair" if overall >= 50 else "Poor",
        }

    async def simulation_loop(self):
        step_count = 0
        last_health_index = None
        while self.simulation_running:
            try:
                if self.scenario_active and self.scenario_state:
                    self.plant_state = self.generator.apply_scenario_overrides(self.plant_state, self.scenario_state)
                else:
                    self.plant_state = self.generator.step()
                risk_result = await self.risk_engine.run_async(self.plant_state)
                self.risk_trend.append({
                    "timestamp": datetime.now().isoformat(),
                    "score": risk_result.get("risk_score", 0),
                    "severity": risk_result.get("severity", "normal"),
                })
                if len(self.risk_trend) > 60:
                    self.risk_trend = self.risk_trend[-60:]
                sensors = self.plant_state.get("sensors", {})
                permits = self.plant_state.get("active_permits", [])
                s_critical = len([s for s in sensors.values() if s.get("status") == "critical"])
                s_warning = len([s for s in sensors.values() if s.get("status") == "warning"])
                high_risk_permits = len([p for p in permits if p.get("risk_level") in ["Critical", "High"]])
                zone_overlaps = len(set(p.get("zone_id") for p in permits if sum(1 for pp in permits if pp.get("zone_id") == p.get("zone_id")) > 1))
                in_maint = len(risk_result.get("maintenance_analysis", {}).get("equipment_in_maintenance", []))
                maint_conflicts = len(risk_result.get("maintenance_analysis", {}).get("maintenance_equipment_with_permits", []))
                self.activity_feed.log_sensor_scan(len(sensors), s_critical, s_warning)
                self.activity_feed.log_permit_audit(len(permits), high_risk_permits, zone_overlaps)
                self.activity_feed.log_maintenance_check(in_maint, maint_conflicts)
                self.activity_feed.log_risk_update(risk_result.get("risk_score", 0), risk_result.get("severity", "normal"), len(self.plant_state.get("zone_risk_scores", {})))
                compound_risks = risk_result.get("compound_risks", [])
                if compound_risks:
                    for cr in compound_risks[:2]:
                        self.activity_feed.log_compound_risk(cr.get("zone_name", ""), 1, cr.get("recommendation", ""))
                step_count += 1
                if step_count % 3 == 0:
                    compliance_result = await asyncio.to_thread(self.compliance_agent.run_audit, self.plant_state)
                    v_count = len(compliance_result.get("violations", []))
                    c_count = len(compliance_result.get("critical_findings", []))
                    self.activity_feed.log_compliance_audit(compliance_result["overall_compliance_score"], v_count, c_count)
                    last_health_index = await self._compute_health_index(self.plant_state, risk_result, compliance_result)
                else:
                    compliance_result = None
                payload = {
                    "type": "state_update",
                    "timestamp": datetime.now().isoformat(),
                    "plant": self.plant_state,
                    "risk": risk_result,
                    "activity_feed": self.activity_feed.get_recent(15),
                    "risk_trend": self.risk_trend[-30:],
                    "compliance": compliance_result,
                    "health_index": last_health_index,
                    "scenario_active": self.scenario_active,
                    "scenario_id": self.scenario_id,
                }
                await self.broadcast(payload)
            except Exception as e:
                logger.error(f"Simulation step error: {e}")
            await asyncio.sleep(2)

    async def broadcast(self, message: Dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for conn in dead_connections:
            self.active_connections.remove(conn)


api = ZeroHarmAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ZeroHarm AI Platform starting...")
    api.simulation_running = True
    loop_task = asyncio.create_task(api.simulation_loop())
    yield
    api.simulation_running = False
    loop_task.cancel()
    logger.info("ZeroHarm AI Platform shutting down...")


app = FastAPI(
    title="ZeroHarm AI - Industrial Safety Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "ZeroHarm AI",
        "timestamp": datetime.now().isoformat(),
        "simulation_running": api.simulation_running,
        "connected_clients": len(api.active_connections),
    }


@app.get("/api/plant/layout")
async def get_plant_layout():
    return flagged_response(api.generator.get_plant_layout_data())


@app.get("/api/plant/state")
async def get_plant_state():
    if not api.plant_state:
        api.plant_state = api.generator.step()
    return flagged_response(api.plant_state)


@app.get("/api/risk/current")
async def get_current_risk():
    if not api.plant_state:
        api.plant_state = api.generator.step()
    risk_result = await api.risk_engine.run_async(api.plant_state)
    return flagged_response(risk_result)


@app.get("/api/risk/alerts")
async def get_alerts():
    if not api.plant_state:
        api.plant_state = api.generator.step()
    risk_result = await api.risk_engine.run_async(api.plant_state)
    return flagged_response({"alerts": risk_result.get("alerts", []),
                             "severity": risk_result.get("severity", "normal"),
                             "risk_score": risk_result.get("risk_score", 0),
                             "count": len(risk_result.get("alerts", []))})


@app.get("/api/kg/query")
async def query_knowledge_graph(zone_id: str = "Z01", permit_type: str = "Confined Space Entry",
                                  sensor_type: str = "O2", value: float = 18.5):
    findings = api.knowledge_graph.query_compound_risk_paths(
        zone_id, [permit_type], {sensor_type: value}
    )
    return flagged_response({"findings": findings, "zone_id": zone_id, "permit_type": permit_type})


@app.get("/api/kg/regulatory/{hazard_type}")
async def get_regulatory_context(hazard_type: str):
    context = api.knowledge_graph.get_regulatory_context(hazard_type)
    return flagged_response({"hazard_type": hazard_type, "regulations": context})


@app.post("/api/rag/permit-compliance")
async def check_permit_compliance(data: Dict):
    permit_type = data.get("permit_type", "Hot Work")
    zone_hazard = data.get("zone_hazard_class", "High")
    sensors = data.get("sensor_readings", {})
    result = api.rag_pipeline.query_permit_compliance(permit_type, zone_hazard, sensors)
    return flagged_response(result)


@app.post("/api/rag/search")
async def search_documents(data: Dict):
    query = data.get("query", "")
    top_k = data.get("top_k", 3)
    results = api.rag_pipeline.search(query, top_k)
    return flagged_response({"query": query, "results": results})


@app.post("/api/emergency/trigger")
async def trigger_emergency(data: Dict):
    incident_type = data.get("type", "gas_leak")
    context = data.get("context", {})
    if not api.plant_state:
        api.plant_state = api.generator.step()
    context.setdefault("sensor_snapshot",
                        {sid: {"type": s["type"], "value": s["value"], "unit": s["unit"], "status": s["status"]}
                         for sid, s in api.plant_state.get("sensors", {}).items()})
    context.setdefault("permit_snapshot", api.plant_state.get("active_permits", []))
    context.setdefault("personnel_in_zone", [])
    response = api.emergency_response.trigger(incident_type, context)
    return flagged_response(response)


@app.get("/api/emergency/active")
async def get_active_emergencies():
    emergencies = api.emergency_response.get_active_emergencies()
    return flagged_response({"active_count": len(emergencies), "emergencies": emergencies})


@app.post("/api/emergency/resolve/{emergency_id}")
async def resolve_emergency(emergency_id: str, data: Dict = {}):
    notes = data.get("notes", "")
    result = api.emergency_response.resolve(emergency_id, notes)
    if not result:
        raise HTTPException(status_code=404, detail=f"Emergency {emergency_id} not found")
    return flagged_response(result)


@app.get("/api/incident-patterns")
async def get_incident_patterns():
    patterns = api.incident_patterns.get_all_patterns()
    stats = api.incident_patterns.get_statistics()
    return flagged_response({"patterns": patterns, "statistics": stats})


@app.get("/api/incident-patterns/zone/{zone_id}")
async def get_zone_patterns(zone_id: str):
    patterns = api.incident_patterns.get_zone_patterns(zone_id)
    return flagged_response({"zone_id": zone_id, "patterns": patterns})


@app.get("/api/incident-patterns/recommendations")
async def get_prevention_recommendations(zone_id: str = "Z01", permit_type: str = "Confined Space Entry"):
    recs = api.incident_patterns.get_prevention_recommendations(zone_id, permit_type)
    return flagged_response({"zone_id": zone_id, "permit_type": permit_type, "recommendations": recs})


@app.get("/api/sensors")
async def get_all_sensors():
    if not api.plant_state:
        api.plant_state = api.generator.step()
    sensors = api.plant_state.get("sensors", {})
    return flagged_response({"sensor_count": len(sensors), "sensors": sensors})


@app.get("/api/sensors/zone/{zone_id}")
async def get_zone_sensors(zone_id: str):
    if not api.plant_state:
        api.plant_state = api.generator.step()
    sensors = {sid: s for sid, s in api.plant_state.get("sensors", {}).items() if s.get("zone_id") == zone_id}
    return flagged_response({"zone_id": zone_id, "sensor_count": len(sensors), "sensors": sensors})


@app.get("/api/permits")
async def get_active_permits():
    if not api.plant_state:
        api.plant_state = api.generator.step()
    return flagged_response({"active_permits": api.plant_state.get("active_permits", [])})


@app.get("/api/knowledge-graph")
async def get_knowledge_graph():
    kg_data = api.knowledge_graph.to_dict()
    return flagged_response(kg_data)


@app.get("/api/regulatory-standards")
async def get_regulatory_standards():
    return flagged_response({"standards": OISD_STANDARDS})


@app.get("/api/compliance/audit")
async def get_compliance_audit():
    if not api.plant_state:
        api.plant_state = api.generator.step()
    result = await asyncio.to_thread(api.compliance_agent.run_audit, api.plant_state)
    return flagged_response(result)


@app.get("/api/compliance/trend")
async def get_compliance_trend():
    trend = api.compliance_agent.get_compliance_trend()
    recs = api.compliance_agent.get_actionable_recommendations()
    return flagged_response({"trend": trend, "recommendations": recs})


@app.get("/api/activity-feed")
async def get_activity_feed(count: int = 20):
    return flagged_response({"entries": api.activity_feed.get_recent(count)})


@app.get("/api/risk-trend")
async def get_risk_trend():
    return flagged_response({"trend": api.risk_trend, "current_score": api.risk_trend[-1]["score"] if api.risk_trend else 0})


@app.get("/api/what-if/scenarios")
async def list_what_if_scenarios():
    return flagged_response({"scenarios": api.what_if.list_scenarios()})


@app.post("/api/what-if/apply")
async def apply_what_if_scenario(data: Dict):
    scenario_id = data.get("scenario_id", "")
    if not api.plant_state:
        api.plant_state = api.generator.step()
    modified = api.what_if.apply_scenario(scenario_id, api.plant_state)
    if "error" in modified:
        raise HTTPException(status_code=404, detail=modified["error"])
    api.scenario_active = True
    api.scenario_state = copy.deepcopy(modified)
    api.scenario_id = scenario_id
    risk_result = await api.risk_engine.run_async(modified)
    api.activity_feed.log_system(f"What-If scenario '{scenario_id}' applied — {risk_result.get('severity', 'unknown')}")
    return flagged_response({"plant": modified, "risk": risk_result, "activity": api.activity_feed.get_recent(5),
                             "scenario_active": True, "scenario_id": scenario_id})


@app.post("/api/what-if/custom")
async def apply_custom_scenario(data: Dict):
    if not api.plant_state:
        api.plant_state = api.generator.step()
    changes = data.get("changes", {})
    permits = data.get("permits_to_add", [])
    scenario_name = data.get("name", "Custom Scenario")
    modified = api.what_if.apply_custom(api.plant_state, changes, permits, scenario_name)
    api.scenario_active = True
    api.scenario_state = copy.deepcopy(modified)
    api.scenario_id = "custom"
    risk_result = await api.risk_engine.run_async(modified)
    api.activity_feed.log_system(f"Custom scenario '{scenario_name}' applied — {risk_result.get('severity', 'unknown')}")
    return flagged_response({"plant": modified, "risk": risk_result, "activity": api.activity_feed.get_recent(5),
                             "scenario_active": True})


@app.post("/api/what-if/reset")
async def reset_what_if_scenario():
    api.scenario_active = False
    api.scenario_state = None
    api.scenario_id = None
    api.plant_state = api.generator.step()
    api.activity_feed.log_system("What-If scenario reset — normal operations restored")
    risk_result = await api.risk_engine.run_async(api.plant_state)
    return flagged_response({"plant": api.plant_state, "risk": risk_result, "activity": api.activity_feed.get_recent(5)})


@app.get("/api/health-index")
async def get_health_index():
    if not api.plant_state:
        api.plant_state = api.generator.step()
    risk = await api.risk_engine.run_async(api.plant_state)
    compliance = await asyncio.to_thread(api.compliance_agent.run_audit, api.plant_state)
    return flagged_response(await api._compute_health_index(api.plant_state, risk, compliance))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    api.active_connections.append(websocket)
    logger.info(f"Client connected. Total: {len(api.active_connections)}")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "trigger_emergency":
                    response = api.emergency_response.trigger(
                        msg.get("type", "gas_leak"),
                        msg.get("context", {}),
                    )
                    await websocket.send_json({"type": "emergency_triggered", "data": response})
                elif msg.get("action") == "resolve_emergency":
                    result = api.emergency_response.resolve(
                        msg.get("emergency_id", ""),
                        msg.get("notes", ""),
                    )
                    await websocket.send_json({"type": "emergency_resolved", "data": result})
                elif msg.get("action") == "get_plant_state":
                    if not api.plant_state:
                        api.plant_state = api.generator.step()
                    await websocket.send_json({"type": "plant_state", "data": api.plant_state})
                elif msg.get("action") == "what_if_apply":
                    modified = api.what_if.apply_scenario(msg.get("scenario_id", ""), api.plant_state)
                    if "error" not in modified:
                        api.scenario_active = True
                        api.scenario_state = copy.deepcopy(modified)
                        api.scenario_id = msg.get("scenario_id", "")
                        risk_r = await api.risk_engine.run_async(modified)
                        api.activity_feed.log_system(f"What-If scenario applied via WebSocket")
                        await websocket.send_json({"type": "what_if_applied", "plant": modified, "risk": risk_r, "activity": api.activity_feed.get_recent(10)})
                elif msg.get("action") == "what_if_reset":
                    api.scenario_active = False
                    api.scenario_state = None
                    api.scenario_id = None
                    api.plant_state = api.generator.step()
                    risk_r = await api.risk_engine.run_async(api.plant_state)
                    api.activity_feed.log_system("What-If scenario reset")
                    await websocket.send_json({"type": "what_if_reset", "plant": api.plant_state, "risk": risk_r, "activity": api.activity_feed.get_recent(10)})
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
    except WebSocketDisconnect:
        api.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(api.active_connections)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
