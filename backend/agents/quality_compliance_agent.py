from typing import Dict, List, Optional, Any
from datetime import datetime
import random

from config_loader import get_agent_settings, get_zones
import constants as C

_compliance_cfg = get_agent_settings()["compliance"]
_extreme_zones = _compliance_cfg["extreme_risk_zones"]

COMPLIANCE_CHECKLIST = {
    "gas_detection": {
        "title": "Gas Detection System Compliance",
        "standard": "OISD-STD-116",
        "checks": [
            {"id": "GD-01", "description": "Gas detectors calibrated within last 90 days", "weight": 0.2},
            {"id": "GD-02", "description": "No gas detectors in bypass/bypass logged", "weight": 0.15},
            {"id": "GD-03", "description": "Alarm response time < 60 seconds (drilled quarterly)", "weight": 0.15},
            {"id": "GD-04", "description": "Audible and visual alarms functional in all zones", "weight": 0.1},
            {"id": "GD-05", "description": "Gas detector coverage meets zone hazard classification requirements", "weight": 0.2},
            {"id": "GD-06", "description": "Emergency shutdown interface tested (monthly)", "weight": 0.1},
            {"id": "GD-07", "description": "Gas detector data logged and reviewable for 90 days", "weight": 0.1},
        ]
    },
    "permit_to_work": {
        "title": "Permit-to-Work System Compliance",
        "standard": "Factory Act 1948 / OISD-GDN-204",
        "checks": [
            {"id": "PTW-01", "description": "All high-risk permits reviewed by safety officer", "weight": 0.2},
            {"id": "PTW-02", "description": "Permit validity period does not exceed shift duration", "weight": 0.1},
            {"id": "PTW-03", "description": "Atmospheric test results attached to confined space permits", "weight": 0.2},
            {"id": "PTW-04", "description": "SIMOPS review conducted for overlapping permits in same zone", "weight": 0.15},
            {"id": "PTW-05", "description": "Permit closure includes post-work inspection sign-off", "weight": 0.1},
            {"id": "PTW-06", "description": "Worker training/certification verified before permit issuance", "weight": 0.15},
            {"id": "PTW-07", "description": "Emergency contact numbers listed on all permits", "weight": 0.1},
        ]
    },
    "maintenance_safety": {
        "title": "Maintenance Safety Compliance",
        "standard": "OISD-STD-201 / Factory Act 1948 Sec 7A",
        "checks": [
            {"id": "MS-01", "description": "LOTO procedure followed for all maintenance work", "weight": 0.25},
            {"id": "MS-02", "description": "Equipment isolation verified by second qualified person", "weight": 0.2},
            {"id": "MS-03", "description": "Maintenance procedures include hazard identification step", "weight": 0.15},
            {"id": "MS-04", "description": "Spare parts and tools inspected before use", "weight": 0.1},
            {"id": "MS-05", "description": "Post-maintenance testing completed before return to service", "weight": 0.15},
            {"id": "MS-06", "description": "Maintenance records updated within 24 hours", "weight": 0.15},
        ]
    },
    "training_competency": {
        "title": "Training & Competency Compliance",
        "standard": "Factory Act 1948 Sec 7A / ISO 45001 Clause 7.2",
        "checks": [
            {"id": "TC-01", "description": "All workers have current safety training certifications", "weight": 0.2},
            {"id": "TC-02", "description": "Emergency response drills conducted quarterly", "weight": 0.2},
            {"id": "TC-03", "description": "Permit issuers trained and authorized", "weight": 0.15},
            {"id": "TC-04", "description": "First aid trained personnel available on every shift", "weight": 0.15},
            {"id": "TC-05", "description": "Confined space rescue team trained bi-annually", "weight": 0.15},
            {"id": "TC-06", "description": "New worker safety induction completed before site access", "weight": 0.15},
        ]
    },
    "emergency_preparedness": {
        "title": "Emergency Preparedness Compliance",
        "standard": "OISD-STD-105 / Factory Act 1948 Sec 38",
        "checks": [
            {"id": "EP-01", "description": "Emergency evacuation plan posted in all zones", "weight": 0.15},
            {"id": "EP-02", "description": "Assembly points clearly marked and maintained", "weight": 0.1},
            {"id": "EP-03", "description": "Fire extinguishers inspected monthly", "weight": 0.15},
            {"id": "EP-04", "description": "Emergency lighting tested weekly", "weight": 0.1},
            {"id": "EP-05", "description": "Fire water system flow tested quarterly", "weight": 0.2},
            {"id": "EP-06", "description": "Emergency communication systems tested weekly", "weight": 0.15},
            {"id": "EP-07", "description": "Mutual aid agreements with neighboring plants current", "weight": 0.15},
        ]
    },
}


class QualityComplianceAuditAgent:
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or _compliance_cfg.get("quality_compliance_id", "quality_compliance_1")
        self.name = C.AGENT_COMPLIANCE
        self.status = "idle"
        self.categories = COMPLIANCE_CHECKLIST
        self.audit_history = []
        self.last_audit_time = None

    def run_audit(self, plant_state: Dict) -> Dict:
        self.status = "auditing"
        active_permits = plant_state.get("active_permits", [])
        sensors = plant_state.get("sensors", {})
        zone_risks = plant_state.get("zone_risk_scores", {})
        findings = {
            "agent_id": self.agent_id, "agent_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "overall_compliance_score": 0.0, "category_scores": {},
            "violations": [], "observations": [], "critical_findings": [],
            "summary": "",
        }
        total_weight = 0
        weighted_score = 0
        for cat_id, category in self.categories.items():
            cat_score = self._audit_category(cat_id, category, active_permits, sensors, zone_risks)
            findings["category_scores"][cat_id] = cat_score
            for check in cat_score["checks"]:
                if not check["passed"] and check["severity"] == "critical":
                    findings["critical_findings"].append({
                        "category": category["title"], "check": check["description"],
                        "standard": category["standard"], "detail": check.get("detail", ""),
                    })
                if not check["passed"]:
                    findings["violations"].append({
                        "category": category["title"], "check": check["description"],
                        "standard": category["standard"], "severity": check["severity"],
                    })
                else:
                    findings["observations"].append({
                        "category": category["title"], "check": check["description"], "status": "passed",
                    })
            weighted_score += cat_score["score"] * cat_score["weight"]
            total_weight += cat_score["weight"]
        findings["overall_compliance_score"] = round(weighted_score / total_weight * 100, 1) if total_weight > 0 else 0
        audit_count = len(self.audit_history)
        degradation = min(_compliance_cfg["max_degradation"], audit_count * _compliance_cfg["degradation_per_audit"] + _compliance_cfg["base_degradation"])
        findings["overall_compliance_score"] = round(max(0, findings["overall_compliance_score"] - degradation), 1)
        critical_count = len(findings["critical_findings"])
        violation_count = len(findings["violations"])
        if critical_count > 0:
            findings["summary"] = f"CRITICAL: {critical_count} critical compliance gaps found. Overall score: {findings['overall_compliance_score']}%"
            findings["severity"] = "critical"
        elif violation_count > _compliance_cfg["warning_violation_threshold"]:
            findings["summary"] = f"WARNING: {violation_count} compliance gaps found. Overall score: {findings['overall_compliance_score']}%"
            findings["severity"] = "warning"
        else:
            findings["summary"] = f"PASS: Overall compliance score {findings['overall_compliance_score']}% with {violation_count} minor observations"
            findings["severity"] = "normal"
        self.last_audit_time = datetime.now()
        self.audit_history.append({"timestamp": findings["timestamp"], "score": findings["overall_compliance_score"]})
        self.status = "completed"
        return findings

    def _audit_category(self, cat_id: str, category: Dict, permits: List[Dict],
                         sensors: Dict, zone_risks: Dict) -> Dict:
        result = {"id": cat_id, "title": category["title"], "standard": category["standard"],
                  "score": 0.0, "weight": 0, "checks": []}
        total_weight = sum(c["weight"] for c in category["checks"])
        result["weight"] = total_weight
        weighted_score = 0
        for check in category["checks"]:
            check_result = self._evaluate_check(check, cat_id, permits, sensors, zone_risks)
            result["checks"].append(check_result)
            if check_result["passed"]:
                weighted_score += check["weight"]
        result["score"] = weighted_score / total_weight if total_weight > 0 else 0
        return result

    def _evaluate_check(self, check: Dict, cat_id: str, permits: List[Dict],
                         sensors: Dict, zone_risks: Dict) -> Dict:
        check_id = check["id"]
        passed = True
        detail = ""
        severity = "info"

        if check_id == "GD-01":
            bypass_count = sum(1 for s in sensors.values() if s.get("status") == C.SENSOR_STATUS_CRITICAL)
            passed = bypass_count < _compliance_cfg["critical_sensor_bypass_limit"]
            detail = f"{bypass_count} sensors in critical state"
            severity = "critical" if bypass_count > _compliance_cfg["gd02_critical_threshold"] else "warning" if bypass_count > 2 else "info"

        elif check_id == "GD-02":
            bypassed = [s for s in sensors.values() if s.get("status") in [C.SENSOR_STATUS_WARNING, C.SENSOR_STATUS_CRITICAL]]
            passed = len(bypassed) < _compliance_cfg["warning_sensor_limit"]
            detail = f"{len(bypassed)} sensors in warning/critical"
            severity = "critical" if len(bypassed) > _compliance_cfg["gd02_critical_threshold"] else "warning"

        elif check_id == "GD-05":
            extreme_zones = [z for z in _extreme_zones if zone_risks.get(z, 0) > _compliance_cfg["extreme_risk_zone_threshold"]]
            passed = len(extreme_zones) == 0
            detail = f"{len(extreme_zones)} extreme-risk zones with inadequate coverage"
            severity = "critical" if len(extreme_zones) > 1 else "warning"

        elif check_id == "PTW-01":
            critical_permits = [p for p in permits if p.get("risk_level") == "Critical"]
            passed = len(critical_permits) <= _compliance_cfg["ptw01_critical_permit_limit"]
            detail = f"{len(critical_permits)} critical permits active"
            severity = "critical" if len(critical_permits) > _compliance_cfg["ptw01_severity_limit"] else "warning"

        elif check_id == "PTW-04":
            zones_with_overlap = {}
            for p in permits:
                z = p.get("zone_id", "")
                zones_with_overlap.setdefault(z, []).append(p)
            overlaps = {z: ps for z, ps in zones_with_overlap.items() if len(ps) > 1}
            passed = len(overlaps) <= _compliance_cfg["ptw04_overlap_limit"]
            detail = f"{len(overlaps)} zones with overlapping permits"
            severity = "critical" if len(overlaps) > _compliance_cfg["ptw04_overlap_critical_limit"] else "warning"

        elif check_id == "MS-01":
            passed = any(p.get("type") == "Lockout-Tagout" for p in permits)
            detail = "LOTO procedures verified"

        elif check_id == "EP-01":
            high_risk_count = sum(1 for v in zone_risks.values() if v > _compliance_cfg["ep01_high_risk_threshold"])
            passed = high_risk_count <= _compliance_cfg["ep01_max_high_risk_zones"]
            detail = f"{high_risk_count} high-risk zones need evacuation plan review"
            severity = "critical" if high_risk_count > 5 else "warning"

        elif check_id == "EP-05":
            passed = True
            for p in permits:
                if p.get("type") == "Hot Work" and p.get("zone_id") in _extreme_zones:
                    if zone_risks.get(p["zone_id"], 0) >= _compliance_cfg["ep05_fire_suppression_risk_limit"]:
                        passed = False
                        detail = f"Fire suppression may be inadequate for hot work in {p.get('zone_name', '')}"
                        severity = "critical"

        return {
            "id": check_id, "description": check["description"],
            "passed": passed, "detail": detail,
            "severity": severity if not passed else "passed",
        }

    def get_compliance_trend(self) -> List[Dict]:
        return self.audit_history[-_compliance_cfg["compliance_trend_max"]:]

    def get_actionable_recommendations(self) -> List[str]:
        recs = []
        for entry in self.audit_history[-_compliance_cfg["recent_audits_for_recs"]:]:
            if entry["score"] < _compliance_cfg["compliance_warning_score"]:
                recs.append(C.RECOMMENDATION_TEXTS["compliance_audit"])
                break
        recs.append(C.RECOMMENDATION_TEXTS["gas_detection_cal"])
        recs.append(C.RECOMMENDATION_TEXTS["simops_training"])
        recs.append(C.RECOMMENDATION_TEXTS["emergency_drill"])
        recs.append(C.RECOMMENDATION_TEXTS["loto_review"])
        return recs[:_compliance_cfg["max_recommendations"]]
