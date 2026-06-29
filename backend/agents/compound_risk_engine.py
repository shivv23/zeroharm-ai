from typing import Dict, List, Optional, TypedDict
from datetime import datetime
import asyncio
import copy

from .sensor_monitor_agent import SensorMonitorAgent
from .permit_activity_agent import PermitActivityAgent
from .maintenance_status_agent import MaintenanceStatusAgent
from config_loader import get_agent_settings
import constants as C

_cr = get_agent_settings()["compound_risk"]


class AgentState(TypedDict):
    plant_state: Dict
    sensor_findings: Optional[Dict]
    permit_findings: Optional[Dict]
    maintenance_findings: Optional[Dict]
    compound_risks: Optional[List[Dict]]
    fused_risk_score: Optional[float]
    fused_severity: Optional[str]
    fused_alerts: Optional[List[Dict]]
    fused_summary: Optional[str]


class CompoundRiskDetectionEngine:
    def __init__(self):
        self.name = C.AGENT_COMPOUND_RISK
        self.sensor_agent = SensorMonitorAgent()
        self.permit_agent = PermitActivityAgent()
        self.maintenance_agent = MaintenanceStatusAgent()

    def run_sensor_analysis(self, state: AgentState) -> AgentState:
        state["sensor_findings"] = self.sensor_agent.analyze(state["plant_state"])
        return state

    def run_permit_analysis(self, state: AgentState) -> AgentState:
        state["permit_findings"] = self.permit_agent.analyze(state["plant_state"])
        return state

    def run_maintenance_analysis(self, state: AgentState) -> AgentState:
        state["maintenance_findings"] = self.maintenance_agent.analyze(state["plant_state"])
        return state

    def fuse_and_rank(self, state: AgentState) -> AgentState:
        sensor = state.get("sensor_findings", {}) or {}
        permit = state.get("permit_findings", {}) or {}
        maintenance = state.get("maintenance_findings", {}) or {}
        existing_compound = state.get("plant_state", {}).get("compound_risks", None) or []

        sensor_severity = _cr["sensor_severity_weights"].get(sensor.get("severity", C.SENSOR_STATUS_NORMAL), 0)
        permit_severity = _cr["permit_severity_weights"].get(permit.get("severity", C.SENSOR_STATUS_NORMAL), 0)
        maintenance_severity = _cr["maintenance_severity_weights"].get(maintenance.get("severity", C.SENSOR_STATUS_NORMAL), 0)

        fused_score = sensor_severity * _cr["fusion_weights"]["sensor"] + permit_severity * _cr["fusion_weights"]["permit"] + maintenance_severity * _cr["fusion_weights"]["maintenance"]

        alerts = []
        for cs in sensor.get("critical_sensors", []):
            alerts.append({
                "type": "SENSOR_CRITICAL", "severity": C.SEVERITY_CRITICAL, "source": "sensor_monitor",
                "message": f"{cs['type']} sensor at {cs['value']:.1f}{cs['unit']} in {cs.get('zone_id', C.UNKNOWN_ZONE)}",
                "timestamp": datetime.now().isoformat(),
            })
        for hrp in permit.get("high_risk_permits", []):
            alerts.append({
                "type": "HIGH_RISK_PERMIT", "severity": C.SEVERITY_HIGH, "source": "permit_activity",
                "message": f"{hrp['type']} ({hrp['risk_level']}) in {hrp['zone_name']}",
                "timestamp": datetime.now().isoformat(),
            })
        for ov in permit.get("overlapping_zone_permits", []):
            if len(ov.get("permit_types", [])) > _cr["overlap_min_types"]:
                types_str = ", ".join(ov["permit_types"])
                alerts.append({
                    "type": "PERMIT_OVERLAP", "severity": C.SEVERITY_HIGH, "source": "permit_activity",
                    "message": f"Multiple permits ({types_str}) overlapping in {ov['zone_name']} ({ov['zone_id']})",
                    "timestamp": datetime.now().isoformat(),
                })
        for mp in maintenance.get("maintenance_equipment_with_permits", []):
            eq = mp.get("equipment", {})
            alerts.append({
                "type": "MAINTENANCE_PERMIT_CONFLICT", "severity": C.SEVERITY_HIGH, "source": "maintenance_status",
                "message": f"Equipment {eq.get('name', '')} in maintenance with active permits in zone {mp.get('zone_id', '')}",
                "timestamp": datetime.now().isoformat(),
            })
        for ecr in existing_compound:
            alerts.append({
                "type": "COMPOUND_RISK", "severity": C.SEVERITY_CRITICAL, "source": "compound_risk_engine",
                "message": ecr.get("recommendation", f"Compound risk in {ecr['zone_name']}"),
                "zone_id": ecr["zone_id"], "zone_name": ecr["zone_name"],
                "compound_risk_score": ecr.get("compound_risk_score", 0),
                "permit_type": ecr.get("permit_type", ""), "risks": ecr.get("risks", []),
                "timestamp": datetime.now().isoformat(),
            })

        compound_risk_alerts = [a for a in alerts if a["type"] == "COMPOUND_RISK"]
        if compound_risk_alerts:
            fused_score = max(fused_score, _cr["compound_risk_min_score"])
            fused_severity = C.SEVERITY_CRITICAL
        elif sensor_severity >= _cr["critical_sensor_severity"] or fused_score >= _cr["critical_fused_threshold"]:
            fused_severity = C.SEVERITY_CRITICAL
        elif fused_score >= _cr["high_fused_threshold"]:
            fused_severity = C.SEVERITY_HIGH
        elif fused_score >= _cr["warning_fused_threshold"]:
            fused_severity = C.SENSOR_STATUS_WARNING
        elif fused_score >= _cr["info_fused_threshold"]:
            fused_severity = C.SEVERITY_INFO
        else:
            fused_severity = C.SENSOR_STATUS_NORMAL

        summary_parts = []
        if sensor.get("severity") in [C.SENSOR_STATUS_WARNING, C.SEVERITY_CRITICAL]:
            summary_parts.append(f"Sensors: {sensor.get('summary', '')}")
        if permit.get("severity") in [C.SENSOR_STATUS_WARNING, C.SEVERITY_HIGH, C.SEVERITY_CRITICAL]:
            summary_parts.append(f"Permits: {permit.get('summary', '')}")
        if maintenance.get("severity") in [C.SEVERITY_HIGH, C.SEVERITY_CRITICAL]:
            summary_parts.append(f"Maintenance: {maintenance.get('summary', '')}")
        if compound_risk_alerts:
            summary_parts.append(f"COMPOUND RISK: {len(compound_risk_alerts)} compound risk conditions detected")

        state["compound_risks"] = existing_compound
        state["fused_risk_score"] = round(fused_score, 3)
        state["fused_severity"] = fused_severity
        state["fused_alerts"] = alerts
        state["fused_summary"] = " | ".join(summary_parts) if summary_parts else "NORMAL: All systems nominal"
        return state

    async def run_async(self, plant_state: Dict) -> Dict:
        sensor_findings = await asyncio.to_thread(self.sensor_agent.analyze, copy.deepcopy(plant_state))
        permit_findings = await asyncio.to_thread(self.permit_agent.analyze, copy.deepcopy(plant_state))
        maint_findings = await asyncio.to_thread(self.maintenance_agent.analyze, copy.deepcopy(plant_state))
        state: AgentState = {
            "plant_state": plant_state,
            "sensor_findings": sensor_findings, "permit_findings": permit_findings,
            "maintenance_findings": maint_findings,
            "compound_risks": None, "fused_risk_score": None, "fused_severity": None,
            "fused_alerts": None, "fused_summary": None,
        }
        state = self.fuse_and_rank(state)
        return {
            "risk_score": state["fused_risk_score"], "severity": state["fused_severity"],
            "alerts": state["fused_alerts"], "summary": state["fused_summary"],
            "sensor_analysis": state["sensor_findings"], "permit_analysis": state["permit_findings"],
            "maintenance_analysis": state["maintenance_findings"], "compound_risks": state["compound_risks"],
            "engine_name": self.name, "timestamp": datetime.now().isoformat(),
        }

    def run(self, plant_state: Dict) -> Dict:
        return asyncio.run(self.run_async(plant_state))
