from typing import Dict, List, Optional
from datetime import datetime

from config_loader import get_incident_records, get_zones


class AlertTriageEngine:
    def __init__(self):
        self.incidents = get_incident_records()
        self.zones = get_zones()
        self._triage_cache: Dict[str, Dict] = {}

    def triage(self, alert: Dict, plant_state: Optional[Dict] = None) -> Dict:
        alert_id = alert.get("id", str(id(alert)))
        if alert_id in self._triage_cache:
            return self._triage_cache[alert_id]

        severity = alert.get("severity", "info")
        zone_name = alert.get("zone", "plant")
        zone_info = next((z for z in self.zones if z["id"] == zone_name or z["name"] == zone_name), {})

        zone_risk_score = 0
        if plant_state:
            scores = plant_state.get("zone_risk_scores", {})
            zone_risk_score = scores.get(zone_info.get("id", ""), 0)

        related_incidents = [
            i for i in self.incidents
            if i.get("zone", "").lower() == zone_name.lower()
            or i.get("zone", "").lower() == zone_info.get("name", "").lower()
        ]

        urgency = self._calculate_urgency(severity, zone_risk_score, related_incidents)
        suggested_actions = self._generate_actions(alert, severity, zone_info, plant_state)
        triage_result = {
            "id": alert_id,
            "severity": severity,
            "urgency": urgency,
            "zone": {"id": zone_info.get("id", zone_name), "name": zone_info.get("name", zone_name)},
            "zone_risk_score": zone_risk_score,
            "related_incidents": len(related_incidents),
            "related_incident_details": [
                {"id": i.get("id"), "type": i.get("type"), "date": i.get("date")}
                for i in related_incidents[-3:]
            ],
            "suggested_actions": suggested_actions,
            "triaged_at": datetime.now().isoformat(),
            "requires_immediate_attention": urgency in ("critical", "high"),
        }
        self._triage_cache[alert_id] = triage_result
        return triage_result

    def _calculate_urgency(self, severity: str, zone_risk: float,
                            related_incidents: List) -> str:
        if severity == "critical":
            return "critical"
        if severity == "high":
            return "high"
        if zone_risk > 0.7:
            return "high"
        if severity == "warning" and zone_risk > 0.4:
            return "elevated"
        if related_incidents:
            recent = [i for i in related_incidents if i.get("date", "").startswith("202")]
            if len(recent) >= 2:
                return "elevated"
        return "normal"

    def _generate_actions(self, alert: Dict, severity: str,
                           zone_info: Dict, plant_state: Optional[Dict]) -> List[Dict]:
        actions = []
        if severity in ("critical", "high"):
            actions.append({
                "priority": "immediate", "action": "Evacuate zone",
                "detail": f"Initiate evacuation of {zone_info.get('name', 'affected zone')}",
            })
            actions.append({
                "priority": "immediate", "action": "Dispatch emergency team",
                "detail": "Alert emergency response team and safety officer",
            })
        if zone_info.get("hazard_class", "").lower() in ("extreme", "high"):
            actions.append({
                "priority": "high", "action": "Verify gas detection",
                "detail": "Cross-verify gas detection readings in zone",
            })
        sensors = plant_state.get("sensors", {}) if plant_state else {}
        zone_sensors = [
            s for s in sensors.values()
            if s.get("zone_id") in (zone_info.get("id", ""), zone_info.get("name", ""))
        ]
        if any(s.get("status") == "critical" for s in zone_sensors):
            actions.append({
                "priority": "high", "action": "Isolate equipment",
                "detail": "Isolate equipment in zone with critical sensor readings",
            })
        actions.append({
            "priority": "medium", "action": "Review permit status",
            "detail": "Check active permits and suspend if necessary",
        })
        actions.append({
            "priority": "low", "action": "Log incident report",
            "detail": "Document event in incident investigation system",
        })
        return actions

    def get_stats(self, recent_alerts: Optional[List[Dict]] = None) -> Dict:
        if not recent_alerts:
            return {"total": 0, "critical": 0, "high": 0, "triaged": len(self._triage_cache)}
        return {
            "total": len(recent_alerts),
            "critical": sum(1 for a in recent_alerts if a.get("severity") == "critical"),
            "high": sum(1 for a in recent_alerts if a.get("severity") == "high"),
            "warning": sum(1 for a in recent_alerts if a.get("severity") == "warning"),
            "triaged": len(self._triage_cache),
            "requires_action": sum(1 for a in recent_alerts if a.get("severity") in ("critical", "high")),
        }
