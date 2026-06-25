from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

REGULATORY_DOCUMENTS = {
    "OISD-STD-105": {
        "id": "OISD-STD-105",
        "title": "Fire Protection Facilities for Petroleum Depots, Terminals & Cross Country Pipelines",
        "content": """This standard provides requirements for fire protection facilities including fire water systems, 
        foam systems, portable extinguishers, and automatic detection systems. Key requirements include:
        - Fire water storage capacity shall be sufficient for 4 hours of continuous operation
        - Foam concentrate storage shall be sufficient for the largest single fire scenario
        - Fixed fire monitors shall be spaced at maximum 15m intervals in process areas
        - Hydrant spacing shall not exceed 30m in process areas and 45m in storage areas
        - All fire protection systems shall be tested weekly and maintained as per manufacturer recommendations""",
        "keywords": ["fire protection", "water storage", "foam", "hydrant", "monitor", "testing"],
    },
    "OISD-STD-116": {
        "id": "OISD-STD-116",
        "title": "Fire Prevention and Protection System for Oil and Gas Installations",
        "content": """This standard covers design, installation, and maintenance of fire prevention and protection systems.
        Key requirements include:
        - Gas detection systems shall be provided in all enclosed process areas
        - Fire and gas detection systems shall activate audible and visual alarms
        - Emergency shutdown systems (ESD) shall be fail-safe design
        - Fireproofing shall be applied to structural supports for vessels containing hydrocarbons
        - Passive fire protection shall be maintained in good condition at all times""",
        "keywords": ["gas detection", "alarm", "ESD", "fireproofing", "passive protection"],
    },
    "OISD-STD-118": {
        "id": "OISD-STD-118",
        "title": "Layout Requirements for Oil and Gas Installations",
        "content": """This standard specifies minimum distances between equipment, storage tanks, and boundaries.
        Key requirements include:
        - Minimum 15m between process equipment and ignition sources
        - Minimum 30m between LPG storage and plant boundary
        - Access roads shall be minimum 6m wide with turning radius of 12m
        - Emergency assembly points shall be located at safe distances upwind of process areas
        - Hazardous area classification drawings shall be maintained and updated""",
        "keywords": ["layout", "spacing", "access", "assembly point", "hazardous area"],
    },
    "Factory-Act-1948-Sec36": {
        "id": "Factory-Act-1948-Sec36",
        "title": "Precautions Against Dangerous Fumes and Lack of Oxygen in Confined Spaces",
        "content": """36. No person shall be required to enter any chamber, tank, vat, pit, pipe, flue or other confined 
        space unless it has been certified by a competent person that it is safe to enter. The following precautions 
        shall be observed:
        (a) The confined space shall be thoroughly ventilated before entry
        (b) Adequate arrangements shall be made for the testing of the atmosphere for dangerous fumes and oxygen content
        (c) Suitable breathing apparatus and life belts shall be provided and maintained
        (d) A person trained in first aid and rescue procedures shall be stationed outside the confined space
        (e) All electrical equipment used inside confined spaces shall be of approved safety type""",
        "keywords": ["confined space", "oxygen", "fumes", "ventilation", "breathing apparatus", "rescue"],
    },
    "Factory-Act-1948-Sec37": {
        "id": "Factory-Act-1948-Sec37",
        "title": "Explosive or Inflammable Dust, Gas - Precautions Against Explosions",
        "content": """37. Where any manufacturing process produces dust, gas, fume or vapour of such character and 
        extent as to be liable to explode on ignition, all practicable measures shall be taken to:
        (a) Prevent the accumulation of such dust, gas, fume or vapour
        (b) Exclude all possible sources of ignition
        (c) Provide and maintain effective appliances for extinguishing any fire
        (d) Effective measures shall be taken to prevent the explosion by enclosure of the plant and 
        by effective dust and fume extraction systems""",
        "keywords": ["explosion", "ignition", "dust", "gas", "extinguishing", "enclosure"],
    },
    "ISO-45001-Clause6": {
        "id": "ISO-45001-Clause6",
        "title": "ISO 45001: Planning - Hazard Identification and Risk Assessment",
        "content": """Clause 6.1: The organization shall establish, implement and maintain a process for hazard 
        identification and OH&S risk assessment. This process shall take into account:
        a) Routine and non-routine activities and situations
        b) Emergency situations
        c) People including workers, contractors, and visitors
        d) Changes in the organization, operations, or legal requirements
        The organization shall maintain documented information of hazards, OH&S risks, and actions to address them.""",
        "keywords": ["hazard identification", "risk assessment", "planning", "OH&S"],
    },
}

SAFETY_BEST_PRACTICES = [
    {
        "title": "Hot Work Near Combustibles",
        "content": "Hot work permits require that all combustible materials within 11m of the work area be moved or covered with fire-resistant blankets. A fire watch with extinguisher shall be present for at least 30 minutes after work completion.",
        "applicable_permit_types": ["Hot Work"],
    },
    {
        "title": "Confined Space Atmospheric Testing",
        "content": "Prior to confined space entry, oxygen level must be between 19.5% and 23.5%, LEL must be less than 10% of LFL, and toxic gases (H2S, CO) must be below PEL limits. Continuous monitoring is required during occupancy.",
        "applicable_permit_types": ["Confined Space Entry"],
    },
    {
        "title": "Simultaneous Operations (SIMOPS) Control",
        "content": "When multiple work permits are active in the same zone, a SIMOPS review shall be conducted to identify interaction risks. Hot work and confined space entry shall not be performed simultaneously within 30m of each other.",
        "applicable_permit_types": ["Hot Work", "Confined Space Entry", "Height Work"],
    },
    {
        "title": "Lockout-Tagout (LOTO) Verification",
        "content": "Before maintenance work begins, all energy sources must be isolated and locked. A LOTO verification by a qualified person is required. Each worker shall apply their personal lock before work commences.",
        "applicable_permit_types": ["Lockout-Tagout", "Electrical", "Maintenance"],
    },
    {
        "title": "Emergency Evacuation Protocol",
        "content": "Upon activation of emergency alarm, all workers shall proceed to the designated assembly point. Headcount shall be completed within 3 minutes. Rescue teams shall not enter hazardous areas without proper PPE and gas monitoring.",
        "applicable_permit_types": [],
    },
]


class RAGPipeline:
    def __init__(self):
        self.documents = REGULATORY_DOCUMENTS
        self.best_practices = SAFETY_BEST_PRACTICES
        self.vector_store = {}

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        query_lower = query.lower()
        results = []
        for doc_id, doc in self.documents.items():
            score = 0
            for kw in doc["keywords"]:
                if kw.lower() in query_lower:
                    score += 0.3
            if query_lower in doc["title"].lower():
                score += 0.5
            if query_lower in doc["content"].lower():
                score += 0.2
            if score > 0:
                results.append({"type": "regulatory", "id": doc_id, "title": doc["title"],
                                "content": doc["content"], "score": round(score, 2)})
        for bp in self.best_practices:
            score = 0
            if query_lower in bp["title"].lower():
                score += 0.4
            if query_lower in bp["content"].lower():
                score += 0.2
            for at in bp["applicable_permit_types"]:
                if at.lower() in query_lower:
                    score += 0.3
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
            if lel > 10:
                findings["compliant"] = False
                findings["violations"].append(f"LEL at {lel:.1f}% exceeds 10% safe limit for hot work")
                findings["recommendations"].append("Suspend hot work immediately. Purge area and verify LEL < 10% before resuming.")
            voc = sensor_readings.get("VOC", 0)
            if voc > 25:
                findings["violations"].append(f"VOC at {voc:.1f}ppm indicates flammable atmosphere")
                findings["recommendations"].append("Increase ventilation and re-test atmosphere before continuing hot work.")
        elif permit_type == "Confined Space Entry":
            o2 = sensor_readings.get("O2", 20.9)
            if o2 < 19.5:
                findings["compliant"] = False
                findings["violations"].append(f"O2 at {o2:.1f}% below 19.5% safe entry threshold")
                findings["recommendations"].append("Stop entry. Ventilate confined space until O2 is restored above 19.5%.")
            if o2 > 23.5:
                findings["compliant"] = False
                findings["violations"].append(f"O2 at {o2:.1f}% above 23.5% - oxygen-enriched atmosphere")
                findings["recommendations"].append("Stop entry. Investigate oxygen enrichment source.")
            h2s = sensor_readings.get("H2S", 0)
            if h2s > 5:
                findings["compliant"] = False
                findings["violations"].append(f"H2S at {h2s:.1f}ppm exceeds safe limit for confined space")
                findings["recommendations"].append("H2S hazard detected. Respiratory protection required before entry.")
        elif permit_type == "Height Work":
            temp = sensor_readings.get("Temperature", 30)
            if temp > 50:
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
                "title": "Gas Leak Emergency Response",
                "priority": "IMMEDIATE",
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
                "title": "Fire Emergency Response",
                "priority": "IMMEDIATE",
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
                "title": "Confined Space Rescue Emergency",
                "priority": "IMMEDIATE",
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
                "title": "Medical Emergency Response",
                "priority": "HIGH",
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
        protocol = protocols.get(incident_type, protocols["medical_emergency"])
        protocol["type"] = incident_type
        protocol["timestamp"] = datetime.now().isoformat()
        return protocol
