from typing import Dict, List, Optional, Any, TypedDict, Annotated
from datetime import datetime
import json
import operator
import asyncio

from .sensor_monitor_agent import SensorMonitorAgent
from .permit_activity_agent import PermitActivityAgent
from .maintenance_status_agent import MaintenanceStatusAgent


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
        self.name = "Compound Risk Detection Engine"
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

        sensor_severity = {"normal": 0, "info": 0.1, "warning": 0.4, "high": 0.6, "critical": 1.0}.get(
            sensor.get("severity", "normal"), 0)
        permit_severity = {"normal": 0, "info": 0.1, "warning": 0.3, "high": 0.5, "critical": 0.9}.get(
            permit.get("severity", "normal"), 0)
        maintenance_severity = {"normal": 0, "info": 0.05, "warning": 0.2, "high": 0.5, "critical": 0.8}.get(
            maintenance.get("severity", "normal"), 0)

        fused_score = sensor_severity * 0.4 + permit_severity * 0.35 + maintenance_severity * 0.25

        alerts = []
        critical_sensors = sensor.get("critical_sensors", [])
        if critical_sensors:
            for cs in critical_sensors:
                alerts.append({
                    "type": "SENSOR_CRITICAL",
                    "severity": "critical",
                    "source": "sensor_monitor",
                    "message": f"{cs['type']} sensor at {cs['value']:.1f}{cs['unit']} in {cs.get('zone_id', 'unknown')}",
                    "timestamp": datetime.now().isoformat(),
                })
        high_risk_permits = permit.get("high_risk_permits", [])
        for hrp in high_risk_permits:
            alerts.append({
                "type": "HIGH_RISK_PERMIT",
                "severity": "high",
                "source": "permit_activity",
                "message": f"{hrp['type']} ({hrp['risk_level']}) in {hrp['zone_name']}",
                "timestamp": datetime.now().isoformat(),
            })
        overlapping = permit.get("overlapping_zone_permits", [])
        for ov in overlapping:
            if len(ov.get("permit_types", [])) > 1:
                types_str = ", ".join(ov["permit_types"])
                alerts.append({
                    "type": "PERMIT_OVERLAP",
                    "severity": "high",
                    "source": "permit_activity",
                    "message": f"Multiple permits ({types_str}) overlapping in {ov['zone_name']} ({ov['zone_id']})",
                    "timestamp": datetime.now().isoformat(),
                })
        maint_with_permits = maintenance.get("maintenance_equipment_with_permits", [])
        for mp in maint_with_permits:
            eq = mp.get("equipment", {})
            alerts.append({
                "type": "MAINTENANCE_PERMIT_CONFLICT",
                "severity": "high",
                "source": "maintenance_status",
                "message": f"Equipment {eq.get('name', '')} in maintenance with active permits in zone {mp.get('zone_id', '')}",
                "timestamp": datetime.now().isoformat(),
            })
        for ecr in existing_compound:
            alerts.append({
                "type": "COMPOUND_RISK",
                "severity": "critical",
                "source": "compound_risk_engine",
                "message": ecr.get("recommendation", f"Compound risk in {ecr['zone_name']}"),
                "zone_id": ecr["zone_id"],
                "zone_name": ecr["zone_name"],
                "compound_risk_score": ecr.get("compound_risk_score", 0),
                "permit_type": ecr.get("permit_type", ""),
                "risks": ecr.get("risks", []),
                "timestamp": datetime.now().isoformat(),
            })

        compound_risk_alerts = [a for a in alerts if a["type"] == "COMPOUND_RISK"]
        if compound_risk_alerts:
            fused_score = max(fused_score, 0.9)
            fused_severity = "critical"
        elif sensor_severity >= 1.0 or fused_score >= 0.7:
            fused_severity = "critical"
        elif fused_score >= 0.4:
            fused_severity = "high"
        elif fused_score >= 0.2:
            fused_severity = "warning"
        elif fused_score >= 0.1:
            fused_severity = "info"
        else:
            fused_severity = "normal"

        summary_parts = []
        if sensor.get("severity") in ["warning", "critical"]:
            summary_parts.append(f"Sensors: {sensor.get('summary', '')}")
        if permit.get("severity") in ["warning", "high", "critical"]:
            summary_parts.append(f"Permits: {permit.get('summary', '')}")
        if maintenance.get("severity") in ["high", "critical"]:
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
        state: AgentState = {
            "plant_state": plant_state,
            "sensor_findings": None,
            "permit_findings": None,
            "maintenance_findings": None,
            "compound_risks": None,
            "fused_risk_score": None,
            "fused_severity": None,
            "fused_alerts": None,
            "fused_summary": None,
        }
        sensor_task = asyncio.create_task(asyncio.to_thread(self.run_sensor_analysis, state))
        permit_task = asyncio.create_task(asyncio.to_thread(self.run_permit_analysis, state))
        maint_task = asyncio.create_task(asyncio.to_thread(self.run_maintenance_analysis, state))
        await asyncio.gather(sensor_task, permit_task, maint_task)
        state = self.fuse_and_rank(state)
        return {
            "risk_score": state["fused_risk_score"],
            "severity": state["fused_severity"],
            "alerts": state["fused_alerts"],
            "summary": state["fused_summary"],
            "sensor_analysis": state["sensor_findings"],
            "permit_analysis": state["permit_findings"],
            "maintenance_analysis": state["maintenance_findings"],
            "compound_risks": state["compound_risks"],
            "engine_name": self.name,
            "timestamp": datetime.now().isoformat(),
        }

    def run(self, plant_state: Dict) -> Dict:
        return asyncio.run(self.run_async(plant_state))
