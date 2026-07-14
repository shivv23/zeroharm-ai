import asyncio
import copy
import csv
import gc
import io
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, Optional
from io import BytesIO
from contextlib import asynccontextmanager
from starlette.requests import Request
from dotenv import load_dotenv

load_dotenv()

import constants as C
from api.schemas import (
    LoginRequest, RegisterRequest, TokenResponse, UserResponse,
    PermitComplianceRequest, RAGSearchRequest, EmergencyTriggerRequest,
    EmergencyResolveRequest, WhatIfApplyRequest, WhatIfCustomRequest,
    VisionDetectRequest, VisionRTSPStartRequest, VisionRTSPStopRequest,
    CreateInvestigationRequest, AddFindingRequest, CreateCapaRequest,
    UpdateCapaStatusRequest, RefreshTokenRequest, ChangePasswordRequest,
    ResetPasswordRequest, AuditLogQuery,
)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

from auth.auth_manager import AuthManager
from data.synthetic_data_generator import SyntheticDataGenerator
from agents.compound_risk_engine import CompoundRiskDetectionEngine
from agents.quality_compliance_agent import QualityComplianceAuditAgent
from agents.agent_activity_feed import AgentActivityFeed
from knowledge_graph.kg_builder import IndustrialKnowledgeGraph
from rag.rag_pipeline import RAGPipeline
from orchestrator.emergency_response import EmergencyResponseOrchestrator
from orchestrator.incident_pattern_intelligence import IncidentPatternIntelligence
from orchestrator.what_if_simulator import WhatIfSimulator
from orchestrator.incident_investigation import IncidentInvestigation
from report_generator import ReportGenerator

from shift_handover import generate_shift_handover
from chat_assistant import ChatAssistant
from cost_of_safety import compute_cost_of_safety
from root_cause_analyzer import RootCauseAnalyzer
from digital_twin import DigitalTwinAggregator
from personnel_tracker import PersonnelTracker
import regulatory_reporter
from alert_triage import AlertTriageEngine
from equipment_health import EquipmentHealthMonitor
from safety_observations import SafetyObservationSystem
from environmental_monitor import EnvironmentalMonitor
from database import init_db, save_plant_state, save_sensor_reading, save_permit, save_compliance_audit, save_alert, get_recent_plant_states
from alert_dispatcher import AlertDispatcher
from audit_log import AuditLogger
try:
    from vision.integration import VisionIntegration
    _vision_available = True
except ImportError:
    _vision_available = False
    VisionIntegration = None

logging.basicConfig(
    level=getattr(logging, C.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("zeroharm-api")

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_ip_request_log: Dict[str, list] = {}
_ip_lock = asyncio.Lock()
_ws_rate: Dict[str, list] = {}
_ws_rate_lock = asyncio.Lock()
_cleanup_lock = asyncio.Lock()
_LAST_CLEANUP = 0.0


async def _cleanup_rate_limits():
    global _LAST_CLEANUP
    now = time.time()
    if now - _LAST_CLEANUP < 300:
        return
    async with _cleanup_lock:
        if now - _LAST_CLEANUP < 300:
            return
        _LAST_CLEANUP = now
    cutoff = now - C.RATE_LIMIT_WINDOW
    async with _ip_lock:
        stale = [ip for ip, ts in _ip_request_log.items() if not ts or ts[-1] < cutoff]
        for ip in stale:
            del _ip_request_log[ip]
    async with _ws_rate_lock:
        stale_ws = [ip for ip, ts in _ws_rate.items() if not ts or ts[-1] < cutoff]
        for ip in stale_ws:
            del _ws_rate[ip]


async def verify_api_key(api_key: str = Depends(_api_key_header)):
    if C.API_KEY and api_key != C.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key


async def rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    await _cleanup_rate_limits()
    async with _ip_lock:
        timestamps = _ip_request_log.get(client_ip, [])
        timestamps = [t for t in timestamps if now - t < C.RATE_LIMIT_WINDOW]
        _ip_request_log[client_ip] = timestamps
        if len(timestamps) >= C.RATE_LIMIT_REQUESTS:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        timestamps.append(now)


def flagged_response(content, **kwargs):
    if isinstance(content, dict) and "data_source" not in content:
        content = {**content, "data_source": C.DATA_SOURCE_LABEL}
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
        self.incident_investigation = IncidentInvestigation()
        self.report_generator = ReportGenerator()
        self.alert_dispatcher = AlertDispatcher()
        from predictive_risk import PredictiveRiskForecaster
        from anomaly_detector import SensorAnomalyDetector
        self.predictor = PredictiveRiskForecaster()
        self.anomaly_detector = SensorAnomalyDetector()
        self.chat = ChatAssistant()
        self.root_cause = RootCauseAnalyzer()
        self.digital_twin = DigitalTwinAggregator()
        self.personnel = PersonnelTracker()
        self.alert_triage = AlertTriageEngine()
        self.equipment_health = EquipmentHealthMonitor()
        self.safety_obs = SafetyObservationSystem()
        self.environmental = EnvironmentalMonitor()
        self.vision = VisionIntegration() if _vision_available else None
        if self.vision and C.VISION_ENABLED:
            self.vision.load_model()
        self.plant_state = {}
        self.risk_trend = []
        self.active_connections = []
        self.connections_lock = asyncio.Lock()
        self.simulation_running = False
        self.scenario_active = False
        self.scenario_state = None
        self.scenario_id = None
        self._last_compliance_result = None
        self._last_health_index = None
        self._last_risk_result = None
        self._plant_snapshot = {}

    def _get_snapshot(self):
        if not self._plant_snapshot:
            self._plant_snapshot = self.generator.step()
        return self._plant_snapshot

    async def _compute_health_index(self, plant_state, risk_result, compliance_result):
        sensors = plant_state.get("sensors", {})
        permits = plant_state.get("active_permits", [])
        w = C.HEALTH_INDEX_WEIGHTS
        s_normal = len([s for s in sensors.values() if s.get("status") == C.SENSOR_STATUS_NORMAL]) / max(len(sensors), 1)
        permit_health = 1.0 - min(1.0, len([p for p in permits if p.get("risk_level") in C.HIGH_RISK_LEVELS]) * C.HIGH_RISK_PERMIT_PENALTY)
        risk_health = 1.0 - risk_result.get("risk_score", 0)
        compliance_health = compliance_result[C.OVERALL_COMPLIANCE_SCORE_KEY] / 100.0 if compliance_result else 1.0
        overall = round((s_normal * w["sensor"] + permit_health * w["permit"] + risk_health * w["risk"] + compliance_health * w["compliance"]) * 100, 1)
        label = C.HEALTH_LABEL_EXCELLENT_STR if overall >= C.HEALTH_LABEL_EXCELLENT else C.HEALTH_LABEL_GOOD_STR if overall >= C.HEALTH_LABEL_GOOD else C.HEALTH_LABEL_FAIR_STR if overall >= C.HEALTH_LABEL_FAIR else C.HEALTH_LABEL_POOR_STR
        return {
            "overall": overall,
            "sensor_health": round(s_normal * 100, 1),
            "permit_health": round(permit_health * 100, 1),
            "risk_health": round(risk_health * 100, 1),
            "compliance_health": round(compliance_health * 100, 1),
            "label": label,
        }

    async def simulation_loop(self):
        step_count = 0
        while self.simulation_running:
            try:
                state = self.generator.step()
                if self.scenario_active and self.scenario_state:
                    self.plant_state = self.generator.apply_scenario_overrides(state, self.scenario_state)
                else:
                    self.plant_state = state
                snapshot = copy.deepcopy(self.plant_state)
                self._plant_snapshot = snapshot
                await save_plant_state(snapshot)
                for sid, s in snapshot.get("sensors", {}).items():
                    await save_sensor_reading(s)
                for p in snapshot.get("active_permits", []):
                    await save_permit(p)
                risk_result = await self.risk_engine.run_async(snapshot)
                self._last_risk_result = risk_result
                self.predictor.feed(risk_result.get("risk_score", 0))
                for sid, s in self._plant_snapshot.get("sensors", {}).items():
                    self.anomaly_detector.feed_sensor(sid, s.get("value", 0))
                self.risk_trend.append({
                    "timestamp": datetime.now().isoformat(),
                    "score": risk_result.get("risk_score", 0),
                    "severity": risk_result.get("severity", C.SENSOR_STATUS_NORMAL),
                })
                sev = risk_result.get("severity", C.SENSOR_STATUS_NORMAL)
                if sev in C.HIGH_RISK_LEVELS:
                    self.alert_dispatcher.dispatch({
                        "severity": sev,
                        "risk_score": risk_result.get("risk_score", 0),
                        "zone": self._plant_snapshot.get("zone", C.UNKNOWN_ZONE),
                        "timestamp": datetime.now().isoformat(),
                        "message": f"Risk score {risk_result.get('risk_score', 0):.2f} — {len(risk_result.get('alerts', []))} active alerts",
                    })
                if len(self.risk_trend) >= C.RISK_TREND_MAX:
                    self.risk_trend = self.risk_trend[-C.RISK_TREND_MAX:]
                sensors = self._plant_snapshot.get("sensors", {})
                permits = self._plant_snapshot.get("active_permits", [])
                s_critical = len([s for s in sensors.values() if s.get("status") == C.SENSOR_STATUS_CRITICAL])
                s_warning = len([s for s in sensors.values() if s.get("status") == C.SENSOR_STATUS_WARNING])
                high_risk_permits = len([p for p in permits if p.get("risk_level") in C.HIGH_RISK_LEVELS])
                zone_ids = set(p.get("zone_id") for p in permits if p.get("zone_id"))
                zone_overlaps = len([z for z in zone_ids if sum(1 for pp in permits if pp.get("zone_id") == z) > 1])
                in_maint = len(risk_result.get("maintenance_analysis", {}).get("equipment_in_maintenance", []))
                maint_conflicts = len(risk_result.get("maintenance_analysis", {}).get("maintenance_equipment_with_permits", []))
                self.activity_feed.log_sensor_scan(len(sensors), s_critical, s_warning)
                self.activity_feed.log_permit_audit(len(permits), high_risk_permits, zone_overlaps)
                self.activity_feed.log_maintenance_check(in_maint, maint_conflicts)
                self.activity_feed.log_risk_update(risk_result.get("risk_score", 0), risk_result.get("severity", C.SENSOR_STATUS_NORMAL), len(self._plant_snapshot.get("zone_risk_scores", {})))
                for alert in risk_result.get("alerts", []):
                    await save_alert(alert)
                compound_risks = risk_result.get("compound_risks", [])
                if compound_risks:
                    for cr in compound_risks[:C.MAX_COMPOUND_RISKS_TO_LOG]:
                        self.activity_feed.log_compound_risk(cr.get("zone_name", ""), 1, cr.get("recommendation", ""))
                step_count += 1
                if step_count % 100 == 0:
                    gc.collect()
                    try:
                        with open("/proc/self/status") as f:
                            for line in f:
                                if line.startswith("VmRSS:"):
                                    logger.debug(f"Memory: {line.strip()}")
                                    break
                    except FileNotFoundError:
                        pass
                if step_count % C.COMPLIANCE_AUDIT_INTERVAL == 0:
                    compliance_result = await asyncio.to_thread(self.compliance_agent.run_audit, snapshot)
                    self._last_compliance_result = compliance_result
                    await save_compliance_audit(compliance_result)
                    v_count = len(compliance_result.get("violations", []))
                    c_count = len(compliance_result.get("critical_findings", []))
                    self.activity_feed.log_compliance_audit(compliance_result[C.OVERALL_COMPLIANCE_SCORE_KEY], v_count, c_count)
                    self._last_health_index = await self._compute_health_index(self._plant_snapshot, risk_result, compliance_result)
                payload = {
                    "type": "state_update",
                    "timestamp": datetime.now().isoformat(),
                    "plant": self._plant_snapshot,
                    "risk": risk_result,
                    "activity_feed": self.activity_feed.get_recent(C.ACTIVITY_FEED_PAYLOAD_COUNT),
                    "risk_trend": self.risk_trend[-C.RISK_TREND_PAYLOAD_COUNT:],
                    "compliance": self._last_compliance_result,
                    "health_index": self._last_health_index,
                    "scenario_active": self.scenario_active,
                    "scenario_id": self.scenario_id,
                }
                await self.broadcast(payload)
            except Exception as e:
                logger.exception(f"Simulation step error")
            await asyncio.sleep(C.WS_UPDATE_INTERVAL)

    async def broadcast(self, message: Dict):
        async with self.connections_lock:
            dead = []
            for c in self.active_connections:
                try:
                    await c.send_json(message)
                except Exception as exc:
                    logger.warning(f"Broadcast error for connection: {exc}")
                    dead.append(c)
            if dead:
                self.active_connections[:] = [c for c in self.active_connections if c not in dead]


api = ZeroHarmAPI()
auth_manager = AuthManager()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = auth_manager.verify_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def require_role(role: str):
    async def role_dependency(user: dict = Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{role}' required")
        return user
    return role_dependency


def require_permission(permission: str):
    async def permission_dependency(user: dict = Depends(get_current_user)):
        if not auth_manager.check_permission(user, resource=permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission '{permission}' required")
        return user
    return permission_dependency


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ZeroHarm AI Platform starting...")
    await init_db()
    if not api.plant_state:
        recent = await get_recent_plant_states(1)
        if recent:
            api.plant_state = recent[0]
            api._plant_snapshot = copy.deepcopy(api.plant_state)
            logger.info("Loaded plant state from database")
    api.simulation_running = True
    loop_task = asyncio.create_task(api.simulation_loop())
    yield
    api.simulation_running = False
    loop_task.cancel()
    try:
        await asyncio.wait_for(loop_task, timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    async with api.connections_lock:
        for ws in api.active_connections:
            try:
                await ws.close(code=1001, reason="Server shutting down")
            except Exception:
                pass
        api.active_connections.clear()
    logger.info("ZeroHarm AI Platform shutting down...")


app = FastAPI(
    title=C.APP_TITLE,
    version=C.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=C.ALLOWED_ORIGINS if C.ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=C.ALLOWED_ORIGINS != ["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.middleware("http")
async def audit_middleware(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/") and request.url.path not in ("/api/health",):
        user = "anonymous"
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                payload = auth_manager.verify_token(auth_header[7:])
                if payload:
                    user = payload["username"]
        except Exception:
            pass
        if request.method != "GET":
            AuditLogger.log(
                action=f"{request.method}_{request.url.path}",
                resource=request.url.path,
                resource_id=None,
                username=user,
                success=response.status_code < 400,
            )
    return response


@app.get("/api/health")
async def health():
    return {
        "status": "ok", "service": "ZeroHarm AI",
        "timestamp": datetime.now().isoformat(),
        "simulation_running": api.simulation_running,
        "connected_clients": len(api.active_connections),
    }


_auth_attempts: Dict[str, list] = {}
_auth_lock = asyncio.Lock()


async def _check_auth_rate(ip: str):
    now = time.time()
    async with _auth_lock:
        attempts = _auth_attempts.get(ip, [])
        attempts = [t for t in attempts if now - t < 60]
        if len(attempts) >= 10:
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 60 seconds.")
        attempts.append(now)
        _auth_attempts[ip] = attempts


@app.post("/api/auth/login")
async def auth_login(data: LoginRequest, request=None):
    if request:
        ip = request.client.host if request.client else "unknown"
        await _check_auth_rate(ip)
    user = auth_manager.authenticate(data.username, data.password)
    if not user:
        AuditLogger.log("login_failed", "auth", data.username, data.username, {"reason": "invalid_credentials"}, success=False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = auth_manager.create_token(user["username"])
    refresh_token = auth_manager.create_refresh_token(user["username"])
    AuditLogger.log("login", "auth", user["username"], user["username"])
    return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.post("/api/auth/refresh")
async def auth_refresh(data: RefreshTokenRequest):
    username = auth_manager.verify_refresh_token(data.refresh_token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    auth_manager.revoke_refresh_token(data.refresh_token)
    new_token = auth_manager.create_token(username)
    new_refresh = auth_manager.create_refresh_token(username)
    AuditLogger.log("token_refresh", "auth", username, username)
    return {"access_token": new_token, "refresh_token": new_refresh, "token_type": "bearer"}


@app.post("/api/auth/change-password", dependencies=[Depends(get_current_user)])
async def auth_change_password(data: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    ok = auth_manager.change_password(user["username"], data.old_password, data.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    auth_manager.revoke_all_user_tokens(user["username"])
    AuditLogger.log("password_change", "auth", user["username"], user["username"])
    return {"detail": "Password changed successfully"}


@app.post("/api/auth/register", dependencies=[Depends(require_permission("manage_users"))])
async def auth_register(data: RegisterRequest):
    created = auth_manager.create_user(data.username, data.password, data.role, data.tenant_id, data.name)
    if not created:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    AuditLogger.log("user_created", "auth", data.username, data.username)
    return {"detail": "User created", "username": data.username, "role": data.role}


@app.get("/api/auth/me", dependencies=[Depends(get_current_user)])
async def auth_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        username=user["username"],
        role=user["role"],
        tenant_id=user["tenant_id"],
        name=user.get("name", user["username"]),
    )


@app.get("/api/admin/users", dependencies=[Depends(require_permission("manage_users"))])
async def admin_list_users():
    return {"users": auth_manager.list_users()}


@app.delete("/api/admin/users/{username}", dependencies=[Depends(require_permission("manage_users"))])
async def admin_delete_user(username: str):
    if username == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete admin user")
    ok = auth_manager.delete_user(username)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    AuditLogger.log("user_deleted", "auth", username, "admin")
    return {"detail": f"User '{username}' deleted"}


@app.put("/api/admin/users/{username}/role", dependencies=[Depends(require_permission("manage_users"))])
async def admin_update_role(username: str, role: str = Query(..., pattern=r"^(admin|safety_officer|operator|viewer)$")):
    ok = auth_manager.update_user_role(username, role)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    AuditLogger.log("role_changed", "auth", username, "admin", {"new_role": role})
    return {"detail": f"User '{username}' role updated to '{role}'"}


@app.post("/api/admin/users/reset-password", dependencies=[Depends(require_permission("manage_users"))])
async def admin_reset_password(data: ResetPasswordRequest):
    ok = auth_manager.reset_password(data.username, data.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    AuditLogger.log("password_reset", "auth", data.username, "admin")
    return {"detail": f"Password reset for '{data.username}'"}


@app.get("/api/plant/layout", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_plant_layout():
    return flagged_response(api.generator.get_plant_layout_data())


@app.get("/api/plant/state", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_plant_state():
    if not api.plant_state:
        api._get_snapshot()
    return flagged_response(api._plant_snapshot)


@app.get("/api/risk/current", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_current_risk():
    api._get_snapshot()
    risk_result = await api.risk_engine.run_async(copy.deepcopy(api._plant_snapshot))
    return flagged_response(risk_result)


@app.get("/api/risk/alerts", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_alerts():
    api._get_snapshot()
    risk_result = await api.risk_engine.run_async(copy.deepcopy(api._plant_snapshot))
    return flagged_response({"alerts": risk_result.get("alerts", []),
                             "severity": risk_result.get("severity", C.SENSOR_STATUS_NORMAL),
                             "risk_score": risk_result.get("risk_score", 0),
                             "count": len(risk_result.get("alerts", []))})


@app.get("/api/kg/query", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def query_knowledge_graph(zone_id: str = "Z01", permit_type: str = C.DEFAULT_PERMIT_TYPE,
                                  sensor_type: str = "O2", value: float = 18.5):
    findings = api.knowledge_graph.query_compound_risk_paths(
        zone_id, [permit_type], {sensor_type: value}
    )
    return flagged_response({"findings": findings, "zone_id": zone_id, "permit_type": permit_type})


@app.get("/api/kg/regulatory/{hazard_type}", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_regulatory_context(hazard_type: str):
    context = api.knowledge_graph.get_regulatory_context(hazard_type)
    return flagged_response({"hazard_type": hazard_type, "regulations": context})


@app.post("/api/rag/permit-compliance", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def check_permit_compliance(data: PermitComplianceRequest):
    permit_type = data.permit_type
    zone_hazard = data.zone_hazard_class
    sensors = data.sensor_readings
    result = api.rag_pipeline.query_permit_compliance(permit_type, zone_hazard, sensors)
    return flagged_response(result)


@app.post("/api/rag/search", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def search_documents(data: RAGSearchRequest):
    query = data.query
    top_k = data.top_k
    results = api.rag_pipeline.search(query, top_k)
    return flagged_response({"query": query, "results": results})


@app.post("/api/emergency/trigger", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def trigger_emergency(data: EmergencyTriggerRequest):
    incident_type = data.type
    context = data.context
    api._get_snapshot()
    context.setdefault("sensor_snapshot",
                        {sid: {"type": s["type"], "value": s["value"], "unit": s["unit"], "status": s["status"]}
                         for sid, s in api._plant_snapshot.get("sensors", {}).items()})
    context.setdefault("permit_snapshot", api._plant_snapshot.get("active_permits", []))
    context.setdefault("personnel_in_zone", [])
    response = api.emergency_response.trigger(incident_type, context)
    if response.get("status") == "active":
        inv = api.incident_investigation.create_investigation({
            "type": incident_type, "emergency_id": response.get("id"),
            "description": response.get("label", incident_type), "context": context,
        })
        response["investigation_id"] = inv["id"]
    return flagged_response(response)


@app.get("/api/emergency/active", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_active_emergencies():
    emergencies = api.emergency_response.get_active_emergencies()
    return flagged_response({"active_count": len(emergencies), "emergencies": emergencies})


@app.post("/api/emergency/resolve/{emergency_id}", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def resolve_emergency(emergency_id: str, data: EmergencyResolveRequest = None):
    notes = data.notes if data else ""
    result = api.emergency_response.resolve(emergency_id, notes)
    if not result:
        raise HTTPException(status_code=404, detail=f"Emergency {emergency_id} not found")
    return flagged_response(result)


@app.get("/api/incident-patterns", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_incident_patterns():
    patterns = api.incident_patterns.get_all_patterns()
    stats = api.incident_patterns.get_statistics()
    return flagged_response({"patterns": patterns, "statistics": stats})


@app.get("/api/incident-patterns/zone/{zone_id}", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_zone_patterns(zone_id: str):
    patterns = api.incident_patterns.get_zone_patterns(zone_id)
    return flagged_response({"zone_id": zone_id, "patterns": patterns})


@app.get("/api/incident-patterns/recommendations", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_prevention_recommendations(zone_id: str = "Z01", permit_type: str = C.DEFAULT_PERMIT_TYPE):
    recs = api.incident_patterns.get_prevention_recommendations(zone_id, permit_type)
    return flagged_response({"zone_id": zone_id, "permit_type": permit_type, "recommendations": recs})


@app.post("/api/investigation/create", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def create_investigation(data: CreateInvestigationRequest):
    inv = api.incident_investigation.create_investigation(data.incident_data)
    return flagged_response(inv)


@app.post("/api/investigation/{investigation_id}/finding", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def add_finding(investigation_id: str, data: AddFindingRequest):
    finding = api.incident_investigation.add_finding(investigation_id, data.finding)
    if not finding:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    return flagged_response(finding)


@app.get("/api/investigation/list", dependencies=[Depends(require_permission("read")), Depends(verify_api_key), Depends(rate_limit)])
async def list_investigations():
    return flagged_response(api.incident_investigation.list_investigations())


@app.post("/api/investigation/{investigation_id}/capa", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def create_capa(investigation_id: str, data: CreateCapaRequest):
    capa = api.incident_investigation.create_capa(
        investigation_id, data.finding, data.action_type, data.description, data.owner, data.deadline
    )
    if not capa:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    return flagged_response(capa)


@app.put("/api/capa/{capa_id}/status", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def update_capa_status(capa_id: str, data: UpdateCapaStatusRequest):
    capa = api.incident_investigation.update_capa_status(capa_id, data.status)
    if not capa:
        raise HTTPException(status_code=404, detail=f"CAPA {capa_id} not found or invalid status")
    return flagged_response(capa)


@app.get("/api/investigation/{investigation_id}", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_investigation(investigation_id: str):
    inv = api.incident_investigation.get_investigation(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    return flagged_response(inv)


@app.get("/api/capa/open", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_open_capas():
    capas = api.incident_investigation.get_open_capas()
    return flagged_response({"open_capas": capas, "count": len(capas)})


@app.get("/api/capa/statistics", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_capa_statistics():
    stats = api.incident_investigation.get_capa_statistics()
    return flagged_response(stats)


@app.get("/api/investigation/{investigation_id}/report", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_investigation_report(investigation_id: str):
    report = api.incident_investigation.get_investigation_report(investigation_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    return flagged_response(report)


@app.get("/api/sensors", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_all_sensors():
    api._get_snapshot()
    sensors = api._plant_snapshot.get("sensors", {})
    return flagged_response({"sensor_count": len(sensors), "sensors": sensors})


@app.get("/api/sensors/zone/{zone_id}", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_zone_sensors(zone_id: str):
    api._get_snapshot()
    sensors = {sid: s for sid, s in api._plant_snapshot.get("sensors", {}).items() if s.get("zone_id") == zone_id}
    return flagged_response({"zone_id": zone_id, "sensor_count": len(sensors), "sensors": sensors})


@app.get("/api/permits", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_active_permits():
    api._get_snapshot()
    return flagged_response({"active_permits": api._plant_snapshot.get("active_permits", [])})


@app.get("/api/knowledge-graph", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_knowledge_graph():
    kg_data = api.knowledge_graph.to_dict()
    return flagged_response(kg_data)


@app.get("/api/export/compliance", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def export_compliance_report():
    api._get_snapshot()
    compliance = await asyncio.to_thread(api.compliance_agent.run_audit, copy.deepcopy(api._plant_snapshot))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"ZeroHarm AI Compliance Report",
        f"Generated: {timestamp}",
        f"Plant: {api._plant_snapshot.get('plant_name', C.UNKNOWN_LABEL)}",
        f"Data Source: {C.DATA_SOURCE_LABEL_EXPORT}",
        f"",
        f"Overall Compliance Score,{compliance[C.OVERALL_COMPLIANCE_SCORE_KEY]}%",
        f"Violations,{len(compliance['violations'])}",
        f"Critical Findings,{len(compliance['critical_findings'])}",
        f"Severity,{compliance.get('severity', C.SENSOR_STATUS_NORMAL)}",
        f"",
        f"Category,Score(%)",
    ]
    for cat_id, cat in compliance.get("category_scores", {}).items():
        lines.append(f"{cat.get('title', cat_id)},{cat.get('score', 0) * 100:.1f}")
    lines.append(f"")
    lines.append(f"Check ID,Description,Passed,Detail")
    for cat in compliance.get("category_scores", {}).values():
        for check in cat.get("checks", []):
            lines.append(f"{check['id']},{check['description']},{'PASS' if check['passed'] else 'FAIL'},{check.get('detail', '')}")
    return JSONResponse(
        content={"report": "\n".join(lines), "format": "csv", "timestamp": timestamp},
        headers={"Content-Disposition": "attachment; filename=compliance_report.csv"},
    )


@app.get("/api/regulatory-standards", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_regulatory_standards():
    from config_loader import get_regulatory_standards as _grs
    return flagged_response({"standards": _grs()})


@app.get("/api/compliance/audit", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_compliance_audit():
    api._get_snapshot()
    result = await asyncio.to_thread(api.compliance_agent.run_audit, copy.deepcopy(api._plant_snapshot))
    return flagged_response(result)


@app.get("/api/compliance/trend", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_compliance_trend():
    trend = api.compliance_agent.get_compliance_trend()
    recs = api.compliance_agent.get_actionable_recommendations()
    return flagged_response({"trend": trend, "recommendations": recs})


@app.get("/api/activity-feed", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_activity_feed(count: int = 20):
    count = max(1, min(count, 200))
    return flagged_response({"entries": api.activity_feed.get_recent(count)})


@app.get("/api/risk-trend", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_risk_trend():
    return flagged_response({"trend": api.risk_trend, "current_score": api.risk_trend[-1]["score"] if api.risk_trend else 0})


@app.get("/api/what-if/scenarios", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def list_what_if_scenarios():
    return flagged_response({"scenarios": api.what_if.list_scenarios()})


@app.post("/api/what-if/apply", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def apply_what_if_scenario(data: WhatIfApplyRequest):
    scenario_id = data.scenario_id
    api._get_snapshot()
    modified = api.what_if.apply_scenario(scenario_id, copy.deepcopy(api._plant_snapshot))
    if "error" in modified:
        raise HTTPException(status_code=404, detail="Scenario not found")
    api.scenario_active = True
    api.scenario_state = copy.deepcopy(modified)
    api.scenario_id = scenario_id
    risk_result = await api.risk_engine.run_async(modified)
    sev = risk_result.get("severity", C.SENSOR_STATUS_NORMAL)
    if sev in C.HIGH_RISK_LEVELS:
        api.alert_dispatcher.dispatch({
            "severity": sev,
            "risk_score": risk_result.get("risk_score", 0),
            "zone": modified.get("zone", C.UNKNOWN_ZONE),
            "timestamp": datetime.now().isoformat(),
            "message": f"What-If scenario '{scenario_id}' applied — risk {risk_result.get('risk_score', 0):.2f}",
        })
    api.activity_feed.log_system(f"What-If scenario '{scenario_id}' applied — {risk_result.get('severity', C.UNKNOWN_LABEL)}")
    return flagged_response({"plant": modified, "risk": risk_result, "activity": api.activity_feed.get_recent(5),
                             "scenario_active": True, "scenario_id": scenario_id})


@app.post("/api/what-if/custom", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def apply_custom_scenario(data: WhatIfCustomRequest):
    api._get_snapshot()
    changes = data.changes
    permits = data.permits_to_add
    scenario_name = data.name
    modified = api.what_if.apply_custom(api._plant_snapshot, changes, permits, scenario_name)
    api.scenario_active = True
    api.scenario_state = copy.deepcopy(modified)
    api.scenario_id = "custom"
    risk_result = await api.risk_engine.run_async(modified)
    sev = risk_result.get("severity", C.SENSOR_STATUS_NORMAL)
    if sev in C.HIGH_RISK_LEVELS:
        api.alert_dispatcher.dispatch({
            "severity": sev,
            "risk_score": risk_result.get("risk_score", 0),
            "zone": modified.get("zone", C.UNKNOWN_ZONE),
            "timestamp": datetime.now().isoformat(),
            "message": f"Custom scenario '{scenario_name}' applied — risk {risk_result.get('risk_score', 0):.2f}",
        })
    api.activity_feed.log_system(f"Custom scenario '{scenario_name}' applied — {risk_result.get('severity', C.UNKNOWN_LABEL)}")
    return flagged_response({"plant": modified, "risk": risk_result, "activity": api.activity_feed.get_recent(5),
                             "scenario_active": True})


@app.post("/api/what-if/reset", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def reset_what_if_scenario():
    api.scenario_active = False
    api.scenario_state = None
    api.scenario_id = None
    api.plant_state = api.generator.step()
    api._plant_snapshot = copy.deepcopy(api.plant_state)
    api.activity_feed.log_system("What-If scenario reset — normal operations restored")
    risk_result = await api.risk_engine.run_async(copy.deepcopy(api._plant_snapshot))
    sev = risk_result.get("severity", C.SENSOR_STATUS_NORMAL)
    if sev in C.HIGH_RISK_LEVELS:
        api.alert_dispatcher.dispatch({
            "severity": sev,
            "risk_score": risk_result.get("risk_score", 0),
            "zone": api._plant_snapshot.get("zone", C.UNKNOWN_ZONE),
            "timestamp": datetime.now().isoformat(),
            "message": f"Scenario reset — residual risk {risk_result.get('risk_score', 0):.2f}",
        })
    return flagged_response({"plant": api._plant_snapshot, "risk": risk_result, "activity": api.activity_feed.get_recent(5)})


@app.post("/api/vision/detect", dependencies=[Depends(require_permission("write")), Depends(rate_limit)])
async def vision_detect(data: VisionDetectRequest):
    if not C.VISION_ENABLED or not api.vision:
        raise HTTPException(status_code=503, detail="Vision module is disabled")
    if not api.vision.is_loaded:
        raise HTTPException(status_code=503, detail="YOLO model not loaded")
    try:
        import base64
        import numpy as np
        import cv2
        raw = data.image_bytes or data.base64
        if not raw:
            raise HTTPException(status_code=400, detail="No image data provided")
        decoded = base64.b64decode(raw)
        arr = np.frombuffer(decoded, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        detections = api.vision.process_frame(frame)
        ppe_counts = api.vision.detect_ppe(frame)
        return flagged_response({
            "detections": detections,
            "ppe_counts": ppe_counts,
            "processed_at": datetime.now().isoformat(),
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Vision detect error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vision/rtsp/start", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def vision_rtsp_start(data: VisionRTSPStartRequest):
    if not C.VISION_ENABLED or not api.vision:
        raise HTTPException(status_code=503, detail="Vision module is disabled")
    if not api.vision.is_loaded:
        raise HTTPException(status_code=503, detail="YOLO model not loaded")

    def rtsp_callback(detections):
        violations = api.vision.get_safety_violations_from_detections(detections, "Z01")
        for v in violations:
            api.alert_dispatcher.dispatch(v)

    ok = api.vision.process_rtsp_stream(data.rtsp_url, rtsp_callback)
    if not ok:
        raise HTTPException(status_code=409, detail="Stream already active or failed to start")
    return {"status": "started", "rtsp_url": data.rtsp_url}


@app.post("/api/vision/rtsp/stop", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def vision_rtsp_stop(data: VisionRTSPStopRequest):
    if not C.VISION_ENABLED or not api.vision:
        raise HTTPException(status_code=503, detail="Vision module is disabled")
    ok = api.vision.stop_rtsp_stream(data.rtsp_url)
    if not ok:
        raise HTTPException(status_code=404, detail="Stream not found or not active")
    return {"status": "stopped", "rtsp_url": data.rtsp_url}


@app.get("/api/vision/status", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def vision_status():
    if not C.VISION_ENABLED or not api.vision:
        raise HTTPException(status_code=503, detail="Vision module is disabled")
    return flagged_response(api.vision.get_status())


@app.get("/api/health-index", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_health_index():
    api._get_snapshot()
    risk = await api.risk_engine.run_async(copy.deepcopy(api._plant_snapshot))
    compliance = await asyncio.to_thread(api.compliance_agent.run_audit, copy.deepcopy(api._plant_snapshot))
    return flagged_response(await api._compute_health_index(api._plant_snapshot, risk, compliance))


@app.get("/api/predictive-risk", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_predictive_risk():
    return flagged_response(api.predictor.forecast(steps=5))


@app.get("/api/anomalies", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_anomalies():
    if not api._plant_snapshot:
        return flagged_response([])
    sensors = api._plant_snapshot.get("sensors", {})
    results = await asyncio.to_thread(api.anomaly_detector.scan_all, sensors)
    return flagged_response(results)


@app.get("/api/safety-scores", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_safety_scores():
    if not api._plant_snapshot:
        return flagged_response({"zones": [], "plant_average": 0})
    zone_scores = api._plant_snapshot.get("zone_risk_scores", {})
    zones = []
    from config_loader import get_zones
    all_zones = get_zones()
    for z in all_zones:
        zid = z["id"]
        base = zone_scores.get(zid, z.get("baseRisk", 0.5))
        score = max(0, min(100, round((1 - base) * 100, 1)))
        zones.append({"zone_id": zid, "name": z["name"], "safety_score": score, "hazard": z.get("hazard_class", "High")})
    zones.sort(key=lambda x: x["safety_score"])
    avg = round(sum(z["safety_score"] for z in zones) / len(zones), 1) if zones else 0
    return flagged_response({"zones": zones, "plant_average": avg, "total_zones": len(zones)})


@app.get("/api/cost-of-safety", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_cost_of_safety():
    alerts = api._last_risk_result.get("alerts", []) if api._last_risk_result else []
    permits = api._plant_snapshot.get("active_permits", []) if api._plant_snapshot else []
    return flagged_response(compute_cost_of_safety(alerts=alerts, active_permits=permits))


from api.schemas import ChatRequest

@app.post("/api/chat", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def chat_assistant(req: ChatRequest):
    result = await api.chat.answer(
        message=req.message,
        plant_state=api._plant_snapshot,
        risk_result=api._last_risk_result,
        compliance_result=api._last_compliance_result,
        health_index=api._last_health_index,
        risk_trend=api.risk_trend,
        alerts=api._last_risk_result.get("alerts", []) if api._last_risk_result else [],
    )
    return flagged_response(result)


@app.get("/api/digital-twin", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_digital_twin():
    try:
        dashboard = api.digital_twin.build_dashboard(
            plant_state=api._plant_snapshot or {},
            risk_result=api._last_risk_result,
            compliance_result=api._last_compliance_result,
            health_index=api._last_health_index,
            risk_trend=api.risk_trend or [],
            alerts=api._last_risk_result.get("alerts", []) if api._last_risk_result else [],
            activity_feed=api.activity_feed,
        )
        return flagged_response(dashboard)
    except Exception as e:
        logger.exception("Digital twin build failed")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/incident/root-cause", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_root_cause(incident_id: str = None, incident_type: str = None):
    if not api._plant_snapshot:
        api.plant_state = api.generator.step()
        api._plant_snapshot = api.plant_state.copy()
    result = api.root_cause.analyze(
        incident_id=incident_id,
        incident_type=incident_type,
        plant_state=api._plant_snapshot,
    )
    return flagged_response(result)


@app.get("/api/personnel/locations", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_personnel_locations():
    return flagged_response({"personnel": api.personnel.get_all_locations()})


@app.get("/api/personnel/occupancy", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_zone_occupancy():
    return flagged_response({"zones": api.personnel.get_zone_occupancy()})


@app.get("/api/personnel/mustering", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def get_mustering_status(emergency_zone: str = None):
    return flagged_response(api.personnel.get_mustering_status(emergency_zone))


@app.post("/api/personnel/mustering/trigger", dependencies=[Depends(require_permission("write")), Depends(verify_api_key), Depends(rate_limit)])
async def trigger_mustering(emergency_zone: str = "Z01"):
    return flagged_response(api.personnel.trigger_mustering(emergency_zone))


@app.get("/api/personnel/hazard-exposure", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_hazard_exposure():
    return flagged_response(api.personnel.get_hazard_exposure_report())


@app.post("/api/alerts/triage", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def triage_alert(alert_id: str = None, severity: str = "warning", zone: str = "plant"):
    alert = {"id": alert_id, "severity": severity, "zone": zone}
    result = api.alert_triage.triage(alert, plant_state=api._plant_snapshot)
    return flagged_response(result)


@app.get("/api/alerts/triage-stats", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def triage_stats():
    alerts = api._last_risk_result.get("alerts", []) if api._last_risk_result else []
    return flagged_response(api.alert_triage.get_stats(alerts))


@app.get("/api/maintenance/equipment-health", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_equipment_health():
    equipment = api.equipment_health.assess_equipment(plant_state=api._plant_snapshot)
    summary = api.equipment_health.get_summary(equipment)
    return flagged_response({"equipment": equipment, "summary": summary})


@app.get("/api/safety/observations", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def list_observations(limit: int = 50):
    return flagged_response({"observations": api.safety_obs.get_all(limit)})


@app.get("/api/safety/observations/open", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def list_open_observations():
    return flagged_response({"observations": api.safety_obs.get_open()})


@app.get("/api/safety/observations/trends", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def observation_trends():
    return flagged_response(api.safety_obs.get_trends())


@app.get("/api/safety/observations/types", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def observation_types():
    return flagged_response({"types": api.safety_obs.get_observation_types()})


from api.schemas import ObservationSubmitRequest, ObservationReviewRequest

@app.post("/api/safety/observations/submit", dependencies=[Depends(require_permission("write")), Depends(rate_limit)])
async def submit_observation(req: ObservationSubmitRequest):
    result = api.safety_obs.submit(
        observation_type=req.observation_type, zone_id=req.zone_id,
        description=req.description, severity=req.severity,
        submitted_by=req.submitted_by, location_detail=req.location_detail,
    )
    return flagged_response(result)


@app.post("/api/safety/observations/review", dependencies=[Depends(require_permission("write")), Depends(rate_limit)])
async def review_observation(req: ObservationReviewRequest):
    result = api.safety_obs.review(
        obs_id=req.obs_id, reviewer=req.reviewer,
        resolution=req.resolution, status=req.status,
    )
    return flagged_response(result or {"error": "Observation not found"})


@app.get("/api/environmental/metrics", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_environmental_metrics():
    return flagged_response(api.environmental.get_summary(sensors=api._plant_snapshot.get("sensors")))


@app.get("/api/environmental/compliance", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_environmental_compliance():
    return flagged_response(api.environmental.get_compliance(sensors=api._plant_snapshot.get("sensors")))


@app.get("/api/environmental/history/{metric_id}", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_environmental_history(metric_id: str, hours: int = 24):
    return flagged_response({"metric": metric_id, "history": api.environmental.get_history(metric_id, hours)})


@app.get("/api/audit/log", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_audit_log(action: Optional[str] = Query(None), resource: Optional[str] = Query(None),
                         username: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=1000),
                         offset: int = Query(0, ge=0)):
    return flagged_response({
        "entries": AuditLogger.query(action, resource, username, limit, offset),
        "stats": AuditLogger.stats(),
    })


@app.get("/api/analytics/dashboard", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_analytics_dashboard():
    api._get_snapshot()
    sensors = api._plant_snapshot.get("sensors", {})
    permits = api._plant_snapshot.get("active_permits", [])
    zone_scores = api._plant_snapshot.get("zone_risk_scores", {})
    critical_sensors = sum(1 for s in sensors.values() if s.get("status") == C.SENSOR_STATUS_CRITICAL)
    warning_sensors = sum(1 for s in sensors.values() if s.get("status") == C.SENSOR_STATUS_WARNING)
    high_risk_permits = sum(1 for p in permits if p.get("risk_level") in C.HIGH_RISK_LEVELS)
    risk_trend = api.risk_trend[-C.RISK_TREND_PAYLOAD_COUNT:]
    severity_counts = {}
    for s in sensors.values():
        sev = s.get("status", "normal")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    zone_risk_list = [{"zone_id": zid, "score": score} for zid, score in zone_scores.items()]
    zone_risk_list.sort(key=lambda x: x["score"], reverse=True)
    return flagged_response({
        "sensor_summary": {"total": len(sensors), "critical": critical_sensors, "warning": warning_sensors, "normal": len(sensors) - critical_sensors - warning_sensors, "severity_breakdown": severity_counts},
        "permit_summary": {"total": len(permits), "high_risk": high_risk_permits},
        "risk_trend": risk_trend,
        "zone_risks": zone_risk_list,
        "current_risk": api._last_risk_result.get("risk_score", 0) if api._last_risk_result else 0,
        "current_severity": api._last_risk_result.get("severity", "normal") if api._last_risk_result else "normal",
        "compliance_score": api._last_compliance_result.get(C.OVERALL_COMPLIANCE_SCORE_KEY, 0) if api._last_compliance_result else 0,
        "health_index": api._last_health_index,
    })


@app.get("/api/export/all", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def export_all_data():
    api._get_snapshot()
    sensors = api._plant_snapshot.get("sensors", {})
    permits = api._plant_snapshot.get("active_permits", [])
    alerts = api._last_risk_result.get("alerts", []) if api._last_risk_result else []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = io.StringIO()
    output.write("=== SENSORS ===\n")
    writer = csv.writer(output)
    writer.writerow(["id", "type", "zone_id", "value", "unit", "status", "risk_score"])
    for sid, s in sensors.items():
        writer.writerow([sid, s.get("type", ""), s.get("zone_id", ""), s.get("value", ""), s.get("unit", ""), s.get("status", ""), s.get("risk_score", "")])
    output.write("\n=== PERMITS ===\n")
    writer = csv.writer(output)
    writer.writerow(["id", "type", "zone_id", "status", "risk_level", "workers"])
    for p in permits:
        writer.writerow([p.get("id", ""), p.get("type", ""), p.get("zone_id", ""), p.get("status", ""), p.get("risk_level", ""), len(p.get("workers", []))])
    output.write("\n=== ALERTS ===\n")
    writer = csv.writer(output)
    writer.writerow(["severity", "source", "message", "zone_id"])
    for a in alerts:
        writer.writerow([a.get("severity", ""), a.get("source", ""), a.get("message", ""), a.get("zone_id", "")])
    output.write("\n=== RISK TREND ===\n")
    writer = csv.writer(output)
    writer.writerow(["timestamp", "score", "severity"])
    for r in api.risk_trend:
        writer.writerow([r.get("timestamp", ""), r.get("score", ""), r.get("severity", "")])
    csv_bytes = output.getvalue().encode("utf-8")
    output.close()
    return StreamingResponse(
        BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=zeroharm_export_{timestamp}.csv"},
    )


@app.get("/api/search", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def global_search(q: str = Query(..., min_length=1, max_length=200)):
    api._get_snapshot()
    q = q.lower()
    results = {"sensors": [], "permits": [], "alerts": [], "incidents": []}
    for sid, s in api._plant_snapshot.get("sensors", {}).items():
        if q in sid.lower() or q in s.get("type", "").lower() or q in s.get("zone_id", "").lower():
            results["sensors"].append({"id": sid, "type": s.get("type"), "zone_id": s.get("zone_id"), "status": s.get("status")})
    for p in api._plant_snapshot.get("active_permits", []):
        if q in p.get("id", "").lower() or q in p.get("type", "").lower() or q in p.get("zone_id", "").lower():
            results["permits"].append({"id": p.get("id"), "type": p.get("type"), "zone_id": p.get("zone_id"), "status": p.get("status")})
    if api._last_risk_result:
        for a in api._last_risk_result.get("alerts", []):
            if q in a.get("message", "").lower() or q in a.get("severity", "").lower() or q in a.get("zone_id", "").lower():
                results["alerts"].append({"severity": a.get("severity"), "message": a.get("message"), "zone_id": a.get("zone_id")})
    return flagged_response({"query": q, "total": sum(len(v) for v in results.values()), "results": results})


@app.get("/api/reports/regulatory/{standard}", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_regulatory_report(standard: str):
    standards_map = {
        "oisd": regulatory_reporter.generate_oisd_report,
        "factory-act": regulatory_reporter.generate_factory_act_report,
        "iso45001": regulatory_reporter.generate_iso45001_report,
    }
    if standard not in standards_map:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown standard: {standard}. Use: oisd, factory-act, iso45001")
    pdf_bytes = standards_map[standard]()
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=compliance_{standard}.pdf"})


@app.get("/api/reports/shift-handover", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_shift_handover(shift: str = "Night"):
    api._get_snapshot()
    alerts = api._last_risk_result.get("alerts", []) if api._last_risk_result else []
    permits = api._plant_snapshot.get("active_permits", [])
    incidents = []
    try:
        from database import get_incident_history
        incidents = await get_incident_history(limit=20)
    except Exception:
        pass
    pdf_bytes = generate_shift_handover(
        plant_name=C.PLANT_NAME,
        shift_label=shift,
        alerts=alerts,
        permits=permits,
        risk_trend=api.risk_trend,
        incidents=incidents,
        compliance_score=api._last_compliance_result.get(C.OVERALL_COMPLIANCE_SCORE_KEY) if api._last_compliance_result else None,
        health_index=api._last_health_index,
        zone_risk_scores=api._plant_snapshot.get("zone_risk_scores"),
    )
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=shift_handover_{shift.lower()}.pdf"})


@app.get("/api/reports/compliance", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_compliance_report():
    api._get_snapshot()
    compliance = await asyncio.to_thread(api.compliance_agent.run_audit, copy.deepcopy(api._plant_snapshot))
    timestamp = datetime.now().isoformat()
    plant_name = api._plant_snapshot.get("plant_name", api.report_generator._cfg.get("company_name", C.PLANT_NAME))
    if api.report_generator._cfg.get("include_recommendations", True):
        compliance["recommendations"] = api.compliance_agent.get_actionable_recommendations()
    pdf_bytes = await asyncio.to_thread(api.report_generator.generate_compliance_report, compliance, plant_name, timestamp)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"},
    )


@app.get("/api/reports/risk", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_risk_report():
    api._get_snapshot()
    risk = await api.risk_engine.run_async(copy.deepcopy(api._plant_snapshot))
    timestamp = datetime.now().isoformat()
    pdf_bytes = await asyncio.to_thread(api.report_generator.generate_risk_report, risk, api._plant_snapshot, timestamp)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"},
    )


@app.get("/api/reports/incident/{incident_id}", dependencies=[Depends(require_permission("read")), Depends(rate_limit)])
async def get_incident_report(incident_id: str):
    emergencies = api.emergency_response.get_active_emergencies()
    em = next((e for e in emergencies if e["id"] == incident_id), None)
    if not em:
        all_emergencies = api.emergency_response.active_emergencies
        em = next((e for e in all_emergencies if e["id"] == incident_id), None)
    if not em:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    incident_data = em.get("incident_report", {})
    if not incident_data:
        raise HTTPException(status_code=404, detail=f"No report data for incident {incident_id}")
    incident_data["severity"] = em.get("severity", em.get("type", "unknown"))
    plant_name = api._plant_snapshot.get("plant_name", api.report_generator._cfg.get("company_name", C.PLANT_NAME)) if api._plant_snapshot else C.PLANT_NAME
    pdf_bytes = await asyncio.to_thread(api.report_generator.generate_incident_report, incident_data, plant_name)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=incident_report_{incident_id}.pdf"},
    )


async def _check_ws_rate(websocket: WebSocket) -> bool:
    client_ip = websocket.client.host if websocket.client else "unknown"
    now = time.time()
    async with _ws_rate_lock:
        timestamps = _ws_rate.get(client_ip, [])
        timestamps = [t for t in timestamps if now - t < 60]
        if len(timestamps) >= 60:
            await websocket.close(code=1008, reason="Rate limit exceeded")
            return False
        timestamps.append(now)
        _ws_rate[client_ip] = timestamps
    return True


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query("")):
    origin = websocket.headers.get("origin", "")
    allowed = C.ALLOWED_ORIGINS if C.ALLOWED_ORIGINS != ["*"] else []
    if allowed and origin not in allowed:
        await websocket.close(code=1008, reason="Origin not allowed")
        return
    ws_user = auth_manager.verify_token(token)
    if not ws_user:
        await websocket.close(code=1008, reason="Authentication required")
        return
    await websocket.accept()
    async with api.connections_lock:
        if len(api.active_connections) >= C.MAX_WS_CONNECTIONS:
            await websocket.close(code=1008, reason="Too many connections")
            return
        api.active_connections.append(websocket)
    logger.info(f"Client connected (user={ws_user['username']}). Total: {len(api.active_connections)}")
    try:
        while True:
            if not await _check_ws_rate(websocket):
                break
            raw = await websocket.receive_text()
            if len(raw) > C.MAX_WS_MESSAGE_SIZE:
                await websocket.send_json({"type": "error", "message": "Message too large"})
                continue
            try:
                msg = json.loads(raw)
                action = msg.get("action", "")
                if action == "trigger_emergency":
                    response = api.emergency_response.trigger(
                        msg.get("type", C.DEFAULT_INCIDENT_TYPE),
                        msg.get("context", {}),
                    )
                    await websocket.send_json({"type": "emergency_triggered", "data": response})
                elif action == "resolve_emergency":
                    result = api.emergency_response.resolve(
                        msg.get("emergency_id", ""),
                        msg.get("notes", ""),
                    )
                    await websocket.send_json({"type": "emergency_resolved", "data": result})
                elif action == "get_plant_state":
                    if not api._plant_snapshot:
                        api.plant_state = api.generator.step()
                        api._plant_snapshot = copy.deepcopy(api.plant_state)
                    await websocket.send_json({"type": "plant_state", "data": api._plant_snapshot})
                elif action == "what_if_apply":
                    modified = api.what_if.apply_scenario(msg.get("scenario_id", ""), copy.deepcopy(api._plant_snapshot))
                    if "error" not in modified:
                        api.scenario_active = True
                        api.scenario_state = copy.deepcopy(modified)
                        api.scenario_id = msg.get("scenario_id", "")
                        risk_result = await api.risk_engine.run_async(modified)
                        sev = risk_result.get("severity", C.SENSOR_STATUS_NORMAL)
                        if sev in C.HIGH_RISK_LEVELS:
                            api.alert_dispatcher.dispatch({
                                "severity": sev,
                                "risk_score": risk_result.get("risk_score", 0),
                                "zone": modified.get("zone", C.UNKNOWN_ZONE),
                                "timestamp": datetime.now().isoformat(),
                                "message": f"WS What-If scenario applied — risk {risk_result.get('risk_score', 0):.2f}",
                            })
                        api.activity_feed.log_system("What-If scenario applied via WebSocket")
                        await websocket.send_json({"type": "what_if_applied", "plant": modified, "risk": risk_result, "activity": api.activity_feed.get_recent(10)})
                    else:
                        await websocket.send_json({"type": "error", "message": "Scenario not found"})
                elif action == "what_if_reset":
                    api.scenario_active = False
                    api.scenario_state = None
                    api.scenario_id = None
                    api.plant_state = api.generator.step()
                    api._plant_snapshot = copy.deepcopy(api.plant_state)
                    risk_result = await api.risk_engine.run_async(copy.deepcopy(api._plant_snapshot))
                    api._last_risk_result = risk_result
                    sev = risk_result.get("severity", C.SENSOR_STATUS_NORMAL)
                    if sev in C.HIGH_RISK_LEVELS:
                        api.alert_dispatcher.dispatch({
                            "severity": sev,
                            "risk_score": risk_result.get("risk_score", 0),
                            "zone": api._plant_snapshot.get("zone", C.UNKNOWN_ZONE),
                            "timestamp": datetime.now().isoformat(),
                            "message": f"WS scenario reset — residual risk {risk_result.get('risk_score', 0):.2f}",
                        })
                    api.activity_feed.log_system("What-If scenario reset")
                    await websocket.send_json({"type": "what_if_reset", "plant": api._plant_snapshot, "risk": risk_result, "activity": api.activity_feed.get_recent(10)})
                elif action == "sync_state":
                    if api._plant_snapshot:
                        risk = api._last_risk_result or await api.risk_engine.run_async(copy.deepcopy(api._plant_snapshot))
                        await websocket.send_json({
                            "type": "state_update",
                            "plant": api._plant_snapshot,
                            "risk": risk,
                            "activity_feed": api.activity_feed.get_recent(C.ACTIVITY_FEED_PAYLOAD_COUNT),
                            "risk_trend": api.risk_trend[-C.RISK_TREND_PAYLOAD_COUNT:],
                            "compliance": api._last_compliance_result,
                            "health_index": api._last_health_index,
                        })
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await websocket.send_json({"type": "error", "message": "Internal error processing message"})
    except WebSocketDisconnect:
        async with api.connections_lock:
            api.active_connections[:] = [c for c in api.active_connections if c is not websocket]
        logger.info(f"Client disconnected. Total: {len(api.active_connections)}")


if __name__ == "__main__":
    uvicorn.run(app, host=C.HOST, port=C.PORT)
