from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import hashlib
import json


INCIDENT_RECORDS = [
    {
        "id": "INC-2023-001",
        "date": "2023-03-15",
        "type": "gas_leak",
        "zone": "Coke Oven Battery",
        "description": "CO gas leak during coke pushing operation. 3 workers hospitalized due to gas inhalation.",
        "root_cause": "Inadequate maintenance of gas collection system. Seal failure on coke oven door.",
        "contributing_factors": ["Preventive maintenance overdue by 45 days", "No continuous gas monitoring in area",
                                  "Workers not wearing portable gas detectors"],
        "regulatory_action": "Show cause notice issued under Factory Act 1948 Sec 37",
        "severity": "major",
        "lessons": "Ensure continuous CO monitoring in coke oven battery area. Mandatory portable gas detectors.",
    },
    {
        "id": "INC-2023-002",
        "date": "2023-07-22",
        "type": "confined_space",
        "zone": "Blast Furnace Area",
        "description": "Worker collapsed inside blast furnace tuyere during inspection. Rescued by emergency team.",
        "root_cause": "Confined space permit issued without atmospheric testing. O2 level was 17.2%.",
        "contributing_factors": ["Permit issuer did not verify atmospheric test results",
                                  "Standby personnel not present", "No ventilation established before entry"],
        "regulatory_action": "Penalty under Factory Act 1948 Sec 36. Plant management fined Rs 5 Lakh.",
        "severity": "critical",
        "lessons": "Mandatory O2 and LEL testing before confined space entry. Two-person rule for all confined space work.",
    },
    {
        "id": "INC-2024-001",
        "date": "2024-01-10",
        "type": "fire",
        "zone": "Gas Holder Area",
        "description": "Fire broke out near gas holder during hot work maintenance. Contained within 20 minutes.",
        "root_cause": "Hot work permit issued 15m from gas holder without gas test. LEL of 12% detected post-incident.",
        "contributing_factors": ["SIMOPS review not conducted", "Fire watch not posted",
                                  "Gas detection system was in bypass mode for maintenance"],
        "regulatory_action": "Investigation under OISD-STD-116. Recommendations issued for LOTO procedures.",
        "severity": "major",
        "lessons": "No hot work within 30m of gas holders. Gas detection bypass requires special approval and continuous monitoring.",
    },
    {
        "id": "INC-2024-002",
        "date": "2024-04-05",
        "type": "near_miss",
        "zone": "Continuous Casting",
        "description": "Molten steel spill near water cooling lines. Potential steam explosion averted by quick response.",
        "root_cause": "Ladle refractory failure due to inadequate pre-heating procedure.",
        "contributing_factors": ["Temperature monitoring system not calibrated",
                                  "Operator bypassed pre-heat alarm", "No spare refractory available"],
        "regulatory_action": "Internal investigation only. No regulatory action.",
        "severity": "near_miss",
        "lessons": "Temperature monitoring calibration schedule to be strictly followed. Alarm bypass requires supervisor authorization.",
    },
    {
        "id": "INC-2024-003",
        "date": "2024-08-18",
        "type": "gas_leak",
        "zone": "Coke Oven Battery",
        "description": "H2S gas leak during coke oven charging. 15 workers evacuated. No injuries.",
        "root_cause": "Charging hole cover not properly sealed. Coal charging sequence disrupted causing gas release.",
        "contributing_factors": ["Shift changeover communication failure",
                                  "Charging sequence not followed as per SOP", "Gas alarms not responded to for 4 minutes"],
        "regulatory_action": "Plant issued improvement notice under Factory Act.",
        "severity": "moderate",
        "lessons": "Shift changeover protocols to include safety-critical equipment status. Gas alarm response time target: <60 seconds.",
    },
    {
        "id": "INC-2025-001",
        "date": "2025-01-20",
        "type": "explosion",
        "zone": "Coke Oven Battery",
        "description": "EXPLOSION in coke oven battery. 8 workers killed, 12 injured. Entrapped gases ignited during maintenance.",
        "root_cause": "Gas pressure sensors showed warning signals but no intelligence layer connected readings to operational decisions. Maintenance activity proceeded despite abnormal gas accumulation.",
        "contributing_factors": ["Permit-to-work issued without checking real-time sensor data",
                                  "Gas detection system alarms were silenced due to frequent false alarms",
                                  "Maintenance supervisor not informed of gas pressure anomalies",
                                  "No cross-referencing between permit system and SCADA data"],
        "regulatory_action": "DGMS and Factory Inspectorate investigation. Plant operations suspended.",
        "severity": "catastrophic",
        "lessons": "PROFOUND: Sensor data without intelligence layer is noise. Compound risk detection (permit + gas + maintenance) could have prevented this. NEVER silence alarms without investigating root cause.",
    },
    {
        "id": "INC-2025-002",
        "date": "2025-05-12",
        "type": "near_miss",
        "zone": "Hot Rolling Mill",
        "description": "Roller bearing seized causing coil ejection. No injuries but equipment damage of Rs 2 Cr.",
        "root_cause": "Lubrication system failure. Vibration sensor data showed trend for 72 hours but no action taken.",
        "contributing_factors": ["Predictive maintenance alerts ignored",
                                  "Spare bearing not in inventory", "Operator training gap on vibration analysis"],
        "regulatory_action": "None (internal).",
        "severity": "moderate",
        "lessons": "Predictive maintenance alerts must have escalation protocol if not acknowledged within 24 hours.",
    },
    {
        "id": "INC-2025-003",
        "date": "2025-09-01",
        "type": "confined_space",
        "zone": "Raw Material Yard",
        "description": "Worker overcome by nitrogen atmosphere in bin during cleaning. Fatal.",
        "root_cause": "Lockout-Tagout not properly applied. Nitrogen purge line was not isolated.",
        "contributing_factors": ["LOTO procedure not followed", "No atmospheric testing before entry",
                                  "Permit did not specify nitrogen hazard", "Standby personnel untrained in rescue"],
        "regulatory_action": "Criminal case filed under Factory Act 1948. Safety officer arrested.",
        "severity": "catastrophic",
        "lessons": "LOTO verification must include cross-check by second qualified person. Never rely on single-person verification.",
    },
]


class IncidentPatternIntelligence:
    def __init__(self):
        self.incidents = INCIDENT_RECORDS
        self.patterns = self._discover_patterns()

    def _discover_patterns(self) -> List[Dict]:
        patterns = []
        zone_incidents = {}
        cause_incidents = {}
        type_combinations = {}
        for inc in self.incidents:
            zone = inc["zone"]
            if zone not in zone_incidents:
                zone_incidents[zone] = []
            zone_incidents[zone].append(inc)
            for cause in inc["contributing_factors"]:
                normalized_cause = cause.lower().strip()
                if normalized_cause not in cause_incidents:
                    cause_incidents[normalized_cause] = []
                cause_incidents[normalized_cause].append(inc)
            combo_key = f"{inc['type']}+{inc['zone']}"
            if combo_key not in type_combinations:
                type_combinations[combo_key] = []
            type_combinations[combo_key].append(inc)
        for zone, incidents in zone_incidents.items():
            if len(incidents) >= 2:
                severity_order = {"catastrophic": 5, "critical": 4, "major": 3, "moderate": 2, "near_miss": 1}
                max_severity = max(severity_order.get(i["severity"], 0) for i in incidents)
                severity_label = {5: "CRITICAL", 4: "HIGH", 3: "MEDIUM", 2: "LOW", 1: "INFO"}.get(max_severity, "INFO")
                patterns.append({
                    "type": "RECURRING_ZONE",
                    "zone": zone,
                    "incident_count": len(incidents),
                    "incidents": [i["id"] for i in incidents],
                    "description": f"{zone} has recorded {len(incidents)} incidents - highest in plant",
                    "severity": severity_label,
                    "recommendation": f"Zone-specific safety review recommended for {zone}. Review controls, increase monitoring frequency.",
                })
        for cause, incidents in sorted(cause_incidents.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            if len(incidents) >= 2:
                patterns.append({
                    "type": "RECURRING_CAUSE",
                    "cause": cause,
                    "incident_count": len(incidents),
                    "incidents": [i["id"] for i in incidents],
                    "description": f"'{cause}' contributed to {len(incidents)} incidents",
                    "severity": "HIGH",
                    "recommendation": f"Address root cause: {cause}. Develop targeted preventive action plan.",
                })
        for combo, incidents in type_combinations.items():
            if len(incidents) >= 2:
                inc_type, zone = combo.split("+", 1)
                patterns.append({
                    "type": "TYPE_ZONE_PATTERN",
                    "zone": zone,
                    "incident_type": inc_type,
                    "incident_count": len(incidents),
                    "description": f"{inc_type.replace('_', ' ').title()} has occurred {len(incidents)} times in {zone}",
                    "severity": "MEDIUM",
                    "recommendation": f"Review {inc_type.replace('_', ' ')} controls for {zone}. Consider additional engineering controls.",
                })
        patterns.sort(key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}.get(x["severity"], 5))
        return patterns

    def get_all_patterns(self) -> List[Dict]:
        return self.patterns

    def get_zone_patterns(self, zone_id: str) -> List[Dict]:
        return [p for p in self.patterns if p.get("zone", "").startswith(zone_id)]

    def get_prevention_recommendations(self, zone_id: str, permit_type: str) -> List[str]:
        zone_name = {"Z01": "Coke Oven Battery", "Z02": "Blast Furnace Area", "Z07": "Gas Holder Area"}.get(zone_id, "")
        recommendations = []
        for inc in self.incidents:
            if zone_name and inc["zone"] == zone_name:
                recommendations.extend(inc["lessons"].split(". "))
            if permit_type.replace("_", " ").lower() in inc["description"].lower():
                recommendations.extend(inc["lessons"].split(". "))
        for p in self.patterns:
            if p.get("zone") == zone_name and p.get("recommendation"):
                recommendations.append(p["recommendation"])
        return list(set(recommendations))[:5]

    def get_statistics(self) -> Dict:
        type_counts = {}
        severity_counts = {}
        zone_counts = {}
        for inc in self.incidents:
            type_counts[inc["type"]] = type_counts.get(inc["type"], 0) + 1
            severity_counts[inc["severity"]] = severity_counts.get(inc["severity"], 0) + 1
            zone_counts[inc["zone"]] = zone_counts.get(inc["zone"], 0) + 1
        return {
            "total_incidents": len(self.incidents),
            "by_type": type_counts,
            "by_severity": severity_counts,
            "by_zone": zone_counts,
            "top_contributing_factors": self._get_top_factors(),
        }

    def _get_top_factors(self) -> List[Dict]:
        factor_counts = {}
        for inc in self.incidents:
            for factor in inc["contributing_factors"]:
                factor_counts[factor] = factor_counts.get(factor, 0) + 1
        sorted_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"factor": f, "count": c} for f, c in sorted_factors[:5]]
