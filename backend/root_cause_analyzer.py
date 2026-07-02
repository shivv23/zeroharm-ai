from typing import Dict, List, Optional
from knowledge_graph.kg_builder import IndustrialKnowledgeGraph
from config_loader import get_incident_records, get_zones


class RootCauseAnalyzer:
    def __init__(self):
        self.kg = IndustrialKnowledgeGraph()
        self.incidents = get_incident_records()
        self.zones = get_zones()

    def analyze(self, incident_id: str = None, incident_type: str = None,
                plant_state: Dict = None) -> Dict:
        if incident_id:
            incident = next((i for i in self.incidents if i.get("id") == incident_id), None)
        elif incident_type:
            incident = next((i for i in self.incidents if i.get("type") == incident_type), None)
        else:
            incident = self.incidents[-1] if self.incidents else None
        if not incident:
            return {"incident": None, "root_causes": [], "causal_chain": [], "severity": "unknown"}

        incident_type = incident.get("type", "unknown")
        zone_id = incident.get("zone", "unknown")
        zone_info = next((z for z in self.zones if z["id"] == zone_id), {})

        causal_chain = self._trace_causal_chain(incident_type, zone_id, incident, plant_state)
        direct_causes = [c for c in causal_chain if c.get("confidence", 0) > 0.6]
        contributing_factors = [c for c in causal_chain if 0.3 <= c.get("confidence", 0) <= 0.6]

        regulatory_context = self.kg.get_regulatory_context(incident_type)

        recommendations = self._generate_recommendations(direct_causes, incident_type, zone_id)

        return {
            "incident": {
                "id": incident.get("id", "unknown"),
                "type": incident_type,
                "zone": zone_id,
                "zone_name": zone_info.get("name", "Unknown"),
                "hazard_class": zone_info.get("hazard_class", "Unknown"),
                "date": incident.get("date", ""),
                "description": incident.get("description", ""),
                "severity": incident.get("severity", "moderate"),
            },
            "root_causes": direct_causes,
            "contributing_factors": contributing_factors,
            "causal_chain": causal_chain,
            "regulatory_context": regulatory_context,
            "recommendations": recommendations,
            "overall_confidence": round(
                sum(c.get("confidence", 0) for c in direct_causes) / max(len(direct_causes), 1), 2
            ) if direct_causes else 0,
        }

    def _trace_causal_chain(self, incident_type: str, zone_id: str,
                             incident: Dict, plant_state: Optional[Dict]) -> List[Dict]:
        chain = []
        sensor_failures = {
            "gas_leak": ["LEL", "CO", "H2S", "VOC"],
            "fire": ["Temperature", "CO", "Smoke"],
            "explosion": ["LEL", "Pressure", "Temperature"],
            "confined_space_emergency": ["O2", "H2S", "LEL"],
            "medical_emergency": ["Temperature", "CO", "O2"],
        }
        relevant_sensors = sensor_failures.get(incident_type, [])
        sensors = plant_state.get("sensors", {}) if plant_state else {}
        for sid, sdata in sensors.items():
            if sdata.get("zone_id") == zone_id and sdata.get("type") in relevant_sensors:
                val = sdata.get("value", 0)
                status = sdata.get("status", "normal")
                threshold = sdata.get("critical_threshold", 25)
                if status in ("critical", "warning") or val > threshold:
                    severity_ratio = min(1.0, abs(val - threshold) / max(threshold, 1))
                    chain.append({
                        "type": "sensor_anomaly", "confidence": round(0.5 + severity_ratio * 0.4, 2),
                        "description": f"{sdata.get('type')} sensor reading {val} (threshold: {threshold})",
                        "source": sid, "value": val, "threshold": threshold, "status": status,
                    })

        permits = plant_state.get("active_permits", []) if plant_state else []
        for p in permits:
            if p.get("zone_id") == zone_id:
                risk = p.get("risk_level", "").lower()
                if risk in ("critical", "high"):
                    chain.append({
                        "type": "high_risk_permit", "confidence": 0.65,
                        "description": f"Active {risk} risk permit: {p.get('permit_type', 'Unknown')} in zone",
                        "source": p.get("id", "unknown"), "risk_level": risk,
                        "permit_type": p.get("permit_type", ""),
                    })

        zi = next((z for z in self.zones if z["id"] == zone_id), {})
        hazard_class = zi.get("hazard_class", "").lower()
        if hazard_class in ("extreme", "high"):
            chain.append({
                "type": "inherent_hazard", "confidence": 0.4,
                "description": f"Zone classified as {hazard_class} hazard",
                "source": zone_id, "hazard_class": hazard_class,
            })

        return chain

    def _generate_recommendations(self, root_causes: List[Dict],
                                   incident_type: str, zone_id: str) -> List[Dict]:
        recs = []
        seen = set()
        for cause in root_causes:
            if cause["type"] == "sensor_anomaly":
                key = f"calibrate_{cause['source']}"
                if key not in seen:
                    seen.add(key)
                    recs.append({
                        "action": "Calibrate sensor",
                        "detail": f"Replace or recalibrate {cause.get('source', 'sensor')}",
                        "priority": "high",
                    })
            if cause["type"] == "high_risk_permit":
                key = f"review_{cause['source']}"
                if key not in seen:
                    seen.add(key)
                    recs.append({
                        "action": "Review permit controls",
                        "detail": f"Re-evaluate safety controls for permit {cause.get('source', '')}",
                        "priority": "critical",
                    })

        if incident_type == "gas_leak" and not any(r["type"] == "sensor_anomaly" for r in root_causes):
            recs.append({
                "action": "Install additional gas detectors",
                "detail": f"Zone {zone_id} may need redundant gas detection coverage",
                "priority": "medium",
            })
        if incident_type == "fire":
            recs.append({
                "action": "Inspect fire suppression system",
                "detail": f"Verify fire suppression readiness in zone {zone_id}",
                "priority": "critical",
            })
        if not recs:
            recs.append({
                "action": "Conduct zone safety audit",
                "detail": f"Perform comprehensive safety audit for zone {zone_id}",
                "priority": "medium",
            })
        return recs
