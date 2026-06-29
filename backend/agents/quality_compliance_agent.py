from typing import Dict, List, Optional
from datetime import datetime

from config_loader import get_agent_settings, get_compliance_checklist
import constants as C

_compliance_cfg = get_agent_settings()["compliance"]
_extreme_zones = _compliance_cfg["extreme_risk_zones"]

COMPLIANCE_CHECKLIST = get_compliance_checklist()


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
                if not check["passed"] and check["severity"] == C.SEVERITY_CRITICAL:
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
            findings["severity"] = C.SEVERITY_CRITICAL
        elif violation_count > _compliance_cfg["warning_violation_threshold"]:
            findings["summary"] = f"WARNING: {violation_count} compliance gaps found. Overall score: {findings['overall_compliance_score']}%"
            findings["severity"] = C.SENSOR_STATUS_WARNING
        else:
            findings["summary"] = f"PASS: Overall compliance score {findings['overall_compliance_score']}% with {violation_count} minor observations"
            findings["severity"] = C.SENSOR_STATUS_NORMAL
        self.last_audit_time = datetime.now()
        self.audit_history.append({"timestamp": findings["timestamp"], "score": findings["overall_compliance_score"]})
        if len(self.audit_history) > 500:
            self.audit_history = self.audit_history[-500:]
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
        severity = C.SEVERITY_INFO

        if check_id == "GD-01":
            bypass_count = sum(1 for s in sensors.values() if s.get("status") == C.SENSOR_STATUS_CRITICAL)
            passed = bypass_count < _compliance_cfg["critical_sensor_bypass_limit"]
            detail = f"{bypass_count} sensors in critical state"
            severity = C.SEVERITY_CRITICAL if bypass_count > _compliance_cfg["gd02_critical_threshold"] else C.SENSOR_STATUS_WARNING if bypass_count > 2 else C.SEVERITY_INFO

        elif check_id == "GD-02":
            bypassed = [s for s in sensors.values() if s.get("status") in [C.SENSOR_STATUS_WARNING, C.SENSOR_STATUS_CRITICAL]]
            passed = len(bypassed) < _compliance_cfg["warning_sensor_limit"]
            detail = f"{len(bypassed)} sensors in warning/critical"
            severity = C.SEVERITY_CRITICAL if len(bypassed) > _compliance_cfg["gd02_critical_threshold"] else C.SENSOR_STATUS_WARNING

        elif check_id == "GD-05":
            extreme_zones = [z for z in _extreme_zones if zone_risks.get(z, 0) > _compliance_cfg["extreme_risk_zone_threshold"]]
            passed = len(extreme_zones) == 0
            detail = f"{len(extreme_zones)} extreme-risk zones with inadequate coverage"
            severity = C.SEVERITY_CRITICAL if len(extreme_zones) > 1 else C.SENSOR_STATUS_WARNING

        elif check_id == "PTW-01":
            critical_permits = [p for p in permits if p.get("risk_level") == "Critical"]
            passed = len(critical_permits) <= _compliance_cfg["ptw01_critical_permit_limit"]
            detail = f"{len(critical_permits)} critical permits active"
            severity = C.SEVERITY_CRITICAL if len(critical_permits) > _compliance_cfg["ptw01_severity_limit"] else C.SENSOR_STATUS_WARNING

        elif check_id == "PTW-04":
            zones_with_overlap = {}
            for p in permits:
                z = p.get("zone_id", "")
                zones_with_overlap.setdefault(z, []).append(p)
            overlaps = {z: ps for z, ps in zones_with_overlap.items() if len(ps) > 1}
            passed = len(overlaps) <= _compliance_cfg["ptw04_overlap_limit"]
            detail = f"{len(overlaps)} zones with overlapping permits"
            severity = C.SEVERITY_CRITICAL if len(overlaps) > _compliance_cfg["ptw04_overlap_critical_limit"] else C.SENSOR_STATUS_WARNING

        elif check_id == "MS-01":
            passed = any(p.get("type") == "Lockout-Tagout" for p in permits)
            detail = "LOTO procedures verified"

        elif check_id == "EP-01":
            high_risk_count = sum(1 for v in zone_risks.values() if v > _compliance_cfg["ep01_high_risk_threshold"])
            passed = high_risk_count <= _compliance_cfg["ep01_max_high_risk_zones"]
            detail = f"{high_risk_count} high-risk zones need evacuation plan review"
            severity = C.SEVERITY_CRITICAL if high_risk_count > 5 else C.SENSOR_STATUS_WARNING

        elif check_id == "EP-05":
            passed = True
            for p in permits:
                if p.get("type") == "Hot Work" and p.get("zone_id") in _extreme_zones:
                    if zone_risks.get(p["zone_id"], 0) >= _compliance_cfg["ep05_fire_suppression_risk_limit"]:
                        passed = False
                        detail = f"Fire suppression may be inadequate for hot work in {p.get('zone_name', '')}"
                        severity = C.SEVERITY_CRITICAL

        return {
            "id": check_id, "description": check["description"],
            "passed": passed, "detail": detail,
            "severity": severity if not passed else C.SEVERITY_PASSED,
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
