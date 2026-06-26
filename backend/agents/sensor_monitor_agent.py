from typing import Dict, List, Optional, Any
from datetime import datetime

from config_loader import get_agent_settings
import constants as C

_as = get_agent_settings()["agents"]


class SensorMonitorAgent:
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or _as["sensor_monitor_id"]
        self.name = C.AGENT_SENSOR_MONITOR
        self.status = "idle"

    def analyze(self, state: Dict) -> Dict:
        self.status = "analyzing"
        sensors = state.get("sensors", {})
        findings = {
            "agent_id": self.agent_id, "agent_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "critical_sensors": [], "warning_sensors": [], "zone_alerts": {}, "summary": "",
        }
        zone_sensors = {}
        for sid, s in sensors.items():
            zone_id = s.get("zone_id", C.UNKNOWN_ZONE)
            zone_sensors.setdefault(zone_id, {"total": 0, "critical": 0, "warning": 0, "normal": 0, "details": []})
            zone_sensors[zone_id]["total"] += 1
            status = s.get("status", C.SENSOR_STATUS_NORMAL)
            zone_sensors[zone_id][status] += 1
            zone_entry = {
                "id": sid, "type": s.get("type", ""), "value": s.get("value", 0),
                "unit": s.get("unit", ""), "status": status,
                "threshold": s.get("threshold", 0), "critical": s.get("critical", 0),
                "risk_score": s.get("risk_score", 0),
            }
            zone_sensors[zone_id]["details"].append(zone_entry)
            if status == C.SENSOR_STATUS_CRITICAL:
                findings["critical_sensors"].append(zone_entry)
            elif status == C.SENSOR_STATUS_WARNING:
                findings["warning_sensors"].append(zone_entry)
        for zid, zdata in zone_sensors.items():
            if zdata["critical"] > 0:
                severity = "CRITICAL"
            elif zdata["warning"] > 0:
                severity = "WARNING"
            else:
                severity = "NORMAL"
            findings["zone_alerts"][zid] = {
                "severity": severity, "total_sensors": zdata["total"],
                "critical_count": zdata["critical"], "warning_count": zdata["warning"],
                "affected_sensors": zdata["details"],
            }
        total_critical = len(findings["critical_sensors"])
        total_warning = len(findings["warning_sensors"])
        if total_critical > 0:
            findings["summary"] = f"CRITICAL: {total_critical} sensors in critical state, {total_warning} in warning"
            findings["severity"] = "critical"
        elif total_warning > 0:
            findings["summary"] = f"WARNING: {total_warning} sensors in warning state"
            findings["severity"] = "warning"
        else:
            findings["summary"] = "NORMAL: No sensor anomalies detected"
            findings["severity"] = "normal"
        self.status = "completed"
        return findings
