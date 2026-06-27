from typing import Dict, List, Optional, Any
from datetime import datetime

from config_loader import get_rag_documents, get_safety_practices, get_agent_settings
import constants as C

_rp = get_agent_settings()["rag_pipeline"]


class RAGPipeline:
    def __init__(self):
        self.documents = get_rag_documents()
        self.best_practices = get_safety_practices()
        self.vector_store = {}

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        if top_k is None:
            top_k = _rp["default_top_k"]
        query_lower = query.lower()
        results = []
        for doc_id, doc in self.documents.items():
            score = 0
            for kw in doc["keywords"]:
                if kw.lower() in query_lower:
                    score += _rp["keyword_match_score"]
            if query_lower in doc["title"].lower():
                score += _rp["title_match_score"]
            if query_lower in doc["content"].lower():
                score += _rp["content_match_score"]
            if score > 0:
                results.append({"type": "regulatory", "id": doc_id, "title": doc["title"],
                                "content": doc["content"], "score": round(score, 2)})
        for bp in self.best_practices:
            score = 0
            if query_lower in bp["title"].lower():
                score += _rp["best_practice_title_score"]
            if query_lower in bp["content"].lower():
                score += _rp["best_practice_content_score"]
            for at in bp["applicable_permit_types"]:
                if at.lower() in query_lower:
                    score += _rp["best_practice_permit_type_score"]
            if score > 0:
                results.append({"type": "best_practice", "title": bp["title"],
                                "content": bp["content"], "score": round(score, 2)})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def query_permit_compliance(self, permit_type: str, zone_hazard_class: str,
                                 sensor_readings: Dict[str, float]) -> Dict:
        findings = {"permit_type": permit_type, "compliant": True, "violations": [], "recommendations": []}
        if permit_type == "Hot Work":
            lel = sensor_readings.get("LEL", 0)
            if lel > _rp["hot_work_lel_limit"]:
                findings["compliant"] = False
                findings["violations"].append(f"LEL at {lel:.1f}% exceeds {_rp['hot_work_lel_limit']}% safe limit for hot work")
                findings["recommendations"].append("Suspend hot work immediately. Purge area and verify LEL < 10% before resuming.")
            voc = sensor_readings.get("VOC", 0)
            if voc > _rp["hot_work_voc_limit"]:
                findings["compliant"] = False
                findings["violations"].append(f"VOC at {voc:.1f}ppm indicates flammable atmosphere")
                findings["recommendations"].append("Increase ventilation and re-test atmosphere before continuing hot work.")
        elif permit_type == "Confined Space Entry":
            o2 = sensor_readings.get("O2", 20.9)
            if o2 < _rp["o2_safe_lower"]:
                findings["compliant"] = False
                findings["violations"].append(f"O2 at {o2:.1f}% below {_rp['o2_safe_lower']}% safe entry threshold")
                findings["recommendations"].append("Stop entry. Ventilate confined space until O2 is restored above 19.5%.")
            if o2 > _rp["o2_safe_upper"]:
                findings["compliant"] = False
                findings["violations"].append(f"O2 at {o2:.1f}% above {_rp['o2_safe_upper']}% - oxygen-enriched atmosphere")
                findings["recommendations"].append("Stop entry. Investigate oxygen enrichment source.")
            h2s = sensor_readings.get("H2S", 0)
            if h2s > _rp["h2s_safe_limit"]:
                findings["compliant"] = False
                findings["violations"].append(f"H2S at {h2s:.1f}ppm exceeds safe limit for confined space")
                findings["recommendations"].append("H2S hazard detected. Respiratory protection required before entry.")
        elif permit_type == "Height Work":
            temp = sensor_readings.get("Temperature", 30)
            if temp > _rp["height_work_temp_limit"]:
                findings["compliant"] = False
                findings["violations"].append(f"Temperature at {temp:.0f}°C exceeds safe working limit for height work")
                findings["recommendations"].append("Postpone height work until temperature decreases to safe level.")
        regulatory_docs = self.search(f"{permit_type} safety compliance", top_k=2)
        findings["applicable_regulations"] = regulatory_docs
        findings["timestamp"] = datetime.now().isoformat()
        return findings

    def query_emergency_protocol(self, incident_type: str) -> Dict:
        protocols = {
            "gas_leak": {
                "title": "Gas Leak Emergency Response", "priority": "IMMEDIATE",
                "steps": [
                    "Activate area emergency alarm",
                    "Isolate gas source (close isolation valves)",
                    "Initiate emergency shutdown of affected equipment",
                    "Evacuate all personnel from affected zone",
                    "Establish wind direction monitoring",
                    "Deploy gas monitoring team with portable detectors",
                    "Establish exclusion zone (minimum 100m downwind)",
                    "Notify plant fire brigade and local authorities",
                    "Begin rescue operations only with appropriate PPE and breathing apparatus",
                    "Conduct headcount at assembly point",
                ],
                "regulations": ["OISD-STD-116", "Factory-Act-1948-Sec37"],
            },
            "fire": {
                "title": "Fire Emergency Response", "priority": "IMMEDIATE",
                "steps": [
                    "Activate fire alarm",
                    "Call plant fire brigade with location details",
                    "Initiate emergency shutdown of fuel sources",
                    "Activate fixed fire suppression systems",
                    "Evacuate all personnel from affected zone and adjacent zones",
                    "Establish water supply for firefighting operations",
                    "Set up incident command post upwind of fire",
                    "Account for all personnel at assembly point",
                    "Do NOT re-enter until declared safe by fire officer",
                    "Preserve area for incident investigation after fire is controlled",
                ],
                "regulations": ["OISD-STD-105", "OISD-STD-116", "Factory-Act-1948-Sec38"],
            },
            "confined_space_emergency": {
                "title": "Confined Space Rescue Emergency", "priority": "IMMEDIATE",
                "steps": [
                    "Sound emergency alarm",
                    "Call designated rescue team",
                    "DO NOT enter confined space without breathing apparatus",
                    "Activate forced ventilation if available",
                    "Monitor atmosphere continuously",
                    "Prepare rescue tripod and winch system",
                    "Rescue team to enter with full PPE, SCBA, and lifeline",
                    "Remove victim to fresh air immediately",
                    "Administer first aid / CPR if required",
                    "Transport to medical facility",
                ],
                "regulations": ["Factory-Act-1948-Sec36", "OISD-STD-116"],
            },
            "medical_emergency": {
                "title": "Medical Emergency Response", "priority": "HIGH",
                "steps": [
                    "Call plant medical center / ambulance",
                    "Provide first aid / basic life support",
                    "Do NOT move victim unless area is unsafe",
                    "Keep victim warm and comfortable",
                    "Provide details to medical team on arrival",
                    "Notify next of kin through HR department",
                ],
                "regulations": ["Factory-Act-1948-Sec7A"],
            },
        }
        protocol = protocols.get(incident_type, protocols[_rp["default_emergency_type"]])
        protocol["type"] = incident_type
        protocol["timestamp"] = datetime.now().isoformat()
        return protocol
