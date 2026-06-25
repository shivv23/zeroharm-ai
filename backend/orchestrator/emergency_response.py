from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid


class EmergencyResponseOrchestrator:
    def __init__(self):
        self.name = "Emergency Response Orchestrator"
        self.active_emergencies = []
        self.response_templates = {
            "gas_leak": {
                "type": "gas_leak",
                "label": "Gas Leak - Emergency Response",
                "alert_channels": ["plant_sirens", "slack_safety_channel", "telegram_safety", "sms_managers"],
                "evacuation_radius": 100,
                "requires_shutdown": True,
                "requires_rescue_team": True,
            },
            "fire": {
                "type": "fire",
                "label": "Fire - Emergency Response",
                "alert_channels": ["plant_sirens", "fire_brigade_pager", "slack_safety_channel", "sms_all"],
                "evacuation_radius": 200,
                "requires_shutdown": True,
                "requires_rescue_team": True,
            },
            "confined_space_emergency": {
                "type": "confined_space_emergency",
                "label": "Confined Space Rescue",
                "alert_channels": ["local_alarm", "rescue_team_pager", "slack_safety_channel"],
                "evacuation_radius": 50,
                "requires_shutdown": False,
                "requires_rescue_team": True,
            },
            "explosion": {
                "type": "explosion",
                "label": "Explosion - Full Site Emergency",
                "alert_channels": ["plant_sirens", "fire_brigade_pager", "sms_all", "local_authorities", "district_control"],
                "evacuation_radius": 500,
                "requires_shutdown": True,
                "requires_rescue_team": True,
            },
            "medical_emergency": {
                "type": "medical_emergency",
                "label": "Medical Emergency",
                "alert_channels": ["slack_safety_channel", "sms_managers", "medical_center_pager"],
                "evacuation_radius": 0,
                "requires_shutdown": False,
                "requires_rescue_team": False,
            },
        }

    def trigger(self, incident_type: str, context: Dict) -> Dict:
        template = self.response_templates.get(incident_type, self.response_templates["medical_emergency"])
        emergency_id = f"EMR-{uuid.uuid4().hex[:8].upper()}"
        zone_id = context.get("zone_id", "Unknown")
        zone_name = context.get("zone_name", "Unknown")
        timestamp = datetime.now()
        response = {
            "id": emergency_id,
            "type": incident_type,
            "label": template["label"],
            "status": "triggered",
            "zone_id": zone_id,
            "zone_name": zone_name,
            "triggered_at": timestamp.isoformat(),
            "timeline": [
                {"time": timestamp.isoformat(), "event": "Emergency triggered", "details": f"{template['label']} initiated for {zone_name}"},
            ],
            "alerts_dispatched": [],
            "evacuation_status": "pending",
            "evacuation_radius_m": template["evacuation_radius"],
            "shutdown_initiated": False,
            "rescue_team_dispatched": False,
            "incident_report": None,
            "sensor_evidence_snapshot": context.get("sensor_snapshot", {}),
            "active_permits_snapshot": context.get("permit_snapshot", []),
            "personnel_in_zone": context.get("personnel_in_zone", []),
        }

        alert_results = []
        for channel in template["alert_channels"]:
            alert_result = {
                "channel": channel,
                "status": "dispatched",
                "message": f"[{emergency_id}] {template['label']} in {zone_name}. Evacuate immediately.",
                "dispatched_at": datetime.now().isoformat(),
            }
            alert_results.append(alert_result)
            response["timeline"].append({
                "time": datetime.now().isoformat(),
                "event": f"Alert dispatched via {channel}",
                "details": alert_result["message"],
            })
        response["alerts_dispatched"] = alert_results
        if template["evacuation_radius"] > 0:
            response["evacuation_status"] = "in_progress"
            response["timeline"].append({
                "time": datetime.now().isoformat(),
                "event": f"Evacuation initiated for {zone_name} and surrounding areas ({template['evacuation_radius']}m radius)",
                "details": "All personnel to proceed to designated assembly points",
            })
        if template["requires_shutdown"]:
            response["shutdown_initiated"] = True
            response["timeline"].append({
                "time": datetime.now().isoformat(),
                "event": "Emergency shutdown sequence initiated",
                "details": "Isolating equipment and depressurizing systems in affected zone",
            })
        if template["requires_rescue_team"]:
            response["rescue_team_dispatched"] = True
            response["timeline"].append({
                "time": datetime.now().isoformat(),
                "event": "Rescue team dispatched",
                "details": "Trained rescue team with appropriate PPE and equipment en route",
            })
        response["incident_report"] = self._generate_incident_report(emergency_id, incident_type, zone_id, zone_name, timestamp, context)
        response["timeline"].append({
            "time": datetime.now().isoformat(),
            "event": "Preliminary incident report generated",
            "details": "Regulatory-compliant report prepared for submission",
        })
        response["status"] = "active"
        self.active_emergencies.append(response)
        return response

    def _generate_incident_report(self, emergency_id: str, incident_type: str, zone_id: str,
                                   zone_name: str, timestamp: datetime, context: Dict) -> Dict:
        sensor_snapshot = context.get("sensor_snapshot", {})
        sensor_table = []
        for sid, sdata in sensor_snapshot.items():
            sensor_table.append(f"{sdata.get('type', 'N/A')}: {sdata.get('value', 'N/A')} {sdata.get('unit', '')} ({sdata.get('status', 'N/A')})")
        permit_snapshot = context.get("permit_snapshot", [])
        permit_table = [f"{p.get('id', 'N/A')} - {p.get('type', 'N/A')} ({p.get('risk_level', 'N/A')})" for p in permit_snapshot]
        return {
            "report_id": f"IR-{emergency_id}",
            "generated_at": datetime.now().isoformat(),
            "status": "preliminary",
            "classification": "CONFIDENTIAL - FOR REGULATORY SUBMISSION",
            "details": {
                "emergency_id": emergency_id,
                "incident_type": incident_type.upper().replace("_", " "),
                "location": f"Zone {zone_id} - {zone_name}",
                "date": timestamp.strftime("%Y-%m-%d"),
                "time": timestamp.strftime("%H:%M:%S IST"),
                "reporting_officer": "Auto-generated by ZeroHarm AI Emergency Response System",
                "regulatory_references": self._get_regulatory_refs(incident_type),
            },
            "sensor_evidence": sensor_table,
            "active_permits_at_time": permit_table,
            "personnel_in_zone": context.get("personnel_in_zone", []),
            "timeline_of_events": [
                {"time": timestamp.isoformat(), "event": f"Emergency triggered in {zone_name}"},
                {"time": datetime.now().isoformat(), "event": "Preliminary report generated by ZeroHarm AI"},
            ],
            "preliminary_findings": f"Emergency response initiated for {incident_type} in {zone_name}. Full investigation pending site access.",
            "next_steps": [
                "Secure incident scene - do not disturb evidence",
                "Conduct headcount - verify all personnel accounted for",
                "Await arrival of investigation team",
                "Preserve all sensor data logs and CCTV footage",
                "Submit detailed report within 48 hours as per OISD guidelines",
            ],
        }

    def _get_regulatory_refs(self, incident_type: str) -> List[str]:
        refs = {
            "gas_leak": ["OISD-STD-116 Sec 6.2", "Factory Act 1948 Sec 37", "ISO 45001 Clause 8.2"],
            "fire": ["OISD-STD-105 Sec 4.0", "OISD-STD-116 Sec 8.0", "Factory Act 1948 Sec 38", "ISO 45001 Clause 8.2"],
            "confined_space_emergency": ["Factory Act 1948 Sec 36", "OISD-GDN-204", "ISO 45001 Clause 6.1"],
            "explosion": ["OISD-STD-150", "Factory Act 1948 Sec 37", "DGMS Circular 2024-SC1"],
            "medical_emergency": ["Factory Act 1948 Sec 7A", "ISO 45001 Clause 7.2"],
        }
        return refs.get(incident_type, ["Factory Act 1948", "ISO 45001"])

    def resolve(self, emergency_id: str, resolution_notes: str = "") -> Optional[Dict]:
        for i, em in enumerate(self.active_emergencies):
            if em["id"] == emergency_id:
                self.active_emergencies[i]["status"] = "resolved"
                self.active_emergencies[i]["resolved_at"] = datetime.now().isoformat()
                self.active_emergencies[i]["resolution_notes"] = resolution_notes
                self.active_emergencies[i]["timeline"].append({
                    "time": datetime.now().isoformat(),
                    "event": "Emergency resolved",
                    "details": resolution_notes or "All clear declared",
                })
                return self.active_emergencies[i]
        return None

    def get_active_emergencies(self) -> List[Dict]:
        return [e for e in self.active_emergencies if e["status"] == "active"]
