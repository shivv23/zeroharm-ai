from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from config_loader import get_agent_settings
import constants as C

_af = get_agent_settings()["activity_feed"]


class AgentActivityFeed:
    def __init__(self, max_entries: int = None):
        self.entries = []
        self.max_entries = max_entries or _af["max_entries"]
        self.sequence = 0

    def add_entry(self, agent_name: str, action: str, status: str,
                   detail: str = "", severity: str = C.SEVERITY_INFO, zone_id: str = "") -> Dict:
        self.sequence += 1
        entry = {
            "id": f"{C.ACTIVITY_ID_PREFIX}{uuid.uuid4().hex[:6].upper()}",
            "seq": self.sequence,
            "timestamp": datetime.now().isoformat(),
            "time_display": datetime.now().strftime("%H:%M:%S"),
            "agent": agent_name, "action": action, "status": status,
            "detail": detail, "severity": severity, "zone_id": zone_id,
        }
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        return entry

    def log_sensor_scan(self, sensor_count: int, critical_count: int, warning_count: int):
        status = C.SEVERITY_CRITICAL if critical_count > 0 else C.SENSOR_STATUS_WARNING if warning_count > 0 else C.SENSOR_STATUS_NORMAL
        detail = f"Scanned {sensor_count} sensors — {critical_count} critical, {warning_count} warning"
        return self.add_entry(C.AGENT_SENSOR_MONITOR, "Sensor Health Scan", status, detail, status)

    def log_permit_audit(self, total_permits: int, high_risk: int, overlaps: int):
        status = C.SEVERITY_CRITICAL if high_risk > _af["high_risk_critical_threshold"] else C.SENSOR_STATUS_WARNING if high_risk > 0 else C.SENSOR_STATUS_NORMAL
        detail = f"Audited {total_permits} permits — {high_risk} high-risk, {overlaps} zone overlaps"
        return self.add_entry(C.AGENT_PERMIT_ACTIVITY, "Permit Audit", status, detail, status)

    def log_maintenance_check(self, in_maintenance: int, conflicts: int):
        status = C.SEVERITY_CRITICAL if conflicts > 0 else C.SEVERITY_INFO
        detail = f"Checked {in_maintenance} equipment in maintenance — {conflicts} permit conflicts" if conflicts > 0 else f"Checked {in_maintenance} equipment — no conflicts"
        return self.add_entry(C.AGENT_MAINTENANCE_STATUS, "Maintenance Cross-Check", status, detail, status)

    def log_compound_risk(self, zone_name: str, risk_count: int, recommendation: str):
        return self.add_entry(C.AGENT_COMPOUND_RISK, "Compound Risk Alert",
                              C.SEVERITY_CRITICAL, f"{risk_count} compound risks in {zone_name}: {recommendation[:_af['recommendation_truncate_length']]}...", C.SEVERITY_CRITICAL)

    def log_compliance_audit(self, score: float, violations: int, criticals: int):
        status = C.SEVERITY_CRITICAL if criticals > 0 else C.SENSOR_STATUS_WARNING if violations > _af["compliance_violation_warning"] else C.SENSOR_STATUS_NORMAL
        detail = f"Compliance score: {score}% — {violations} violations, {criticals} critical findings"
        return self.add_entry(C.AGENT_COMPLIANCE, "Compliance Audit", status, detail, status)

    def log_emergency(self, incident_type: str, zone_name: str):
        return self.add_entry(C.AGENT_EMERGENCY,
                              f"{incident_type.replace('_', ' ').title()} Triggered",
                              C.SEVERITY_CRITICAL, f"Emergency response initiated in {zone_name}", C.SEVERITY_CRITICAL)

    def log_risk_update(self, risk_score: float, severity: str, zone_count: int):
        return self.add_entry(C.AGENT_FUSION, "Risk Score Update", severity,
                              f"Overall risk: {risk_score:.3f} — {zone_count} zones evaluated", severity)

    def log_system(self, message: str):
        return self.add_entry(C.AGENT_SYSTEM, "System Event", C.SEVERITY_INFO, message, C.SEVERITY_INFO)

    def get_recent(self, count: int = None) -> List[Dict]:
        count = count or _af["default_recent_count"]
        return list(reversed(self.entries[-count:]))

    def get_by_severity(self, severity: str) -> List[Dict]:
        return [e for e in reversed(self.entries) if e["severity"] == severity]

    def clear(self):
        self.entries = []
