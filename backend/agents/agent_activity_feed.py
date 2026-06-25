from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class AgentActivityFeed:
    def __init__(self, max_entries: int = 100):
        self.entries = []
        self.max_entries = max_entries
        self.sequence = 0

    def add_entry(self, agent_name: str, action: str, status: str,
                   detail: str = "", severity: str = "info", zone_id: str = "") -> Dict:
        self.sequence += 1
        entry = {
            "id": f"ACT-{uuid.uuid4().hex[:6].upper()}",
            "seq": self.sequence,
            "timestamp": datetime.now().isoformat(),
            "time_display": datetime.now().strftime("%H:%M:%S"),
            "agent": agent_name,
            "action": action,
            "status": status,
            "detail": detail,
            "severity": severity,
            "zone_id": zone_id,
        }
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        return entry

    def log_sensor_scan(self, sensor_count: int, critical_count: int, warning_count: int):
        status = "critical" if critical_count > 0 else "warning" if warning_count > 0 else "normal"
        detail = f"Scanned {sensor_count} sensors — {critical_count} critical, {warning_count} warning"
        return self.add_entry("Sensor Monitor Agent", "Sensor Health Scan", status, detail, status)

    def log_permit_audit(self, total_permits: int, high_risk: int, overlaps: int):
        status = "critical" if high_risk > 2 else "warning" if high_risk > 0 else "normal"
        detail = f"Audited {total_permits} permits — {high_risk} high-risk, {overlaps} zone overlaps"
        return self.add_entry("Permit Activity Agent", "Permit Audit", status, detail, status)

    def log_maintenance_check(self, in_maintenance: int, conflicts: int):
        status = "critical" if conflicts > 0 else "info"
        detail = f"Checked {in_maintenance} equipment in maintenance — {conflicts} permit conflicts" if conflicts > 0 else f"Checked {in_maintenance} equipment — no conflicts"
        return self.add_entry("Maintenance Status Agent", "Maintenance Cross-Check", status, detail, status)

    def log_compound_risk(self, zone_name: str, risk_count: int, recommendation: str):
        entry = self.add_entry("Compound Risk Detection Engine", "Compound Risk Alert",
                                "critical", f"{risk_count} compound risks in {zone_name}: {recommendation[:80]}...",
                                "critical")
        return entry

    def log_compliance_audit(self, score: float, violations: int, criticals: int):
        status = "critical" if criticals > 0 else "warning" if violations > 3 else "normal"
        detail = f"Compliance score: {score}% — {violations} violations, {criticals} critical findings"
        return self.add_entry("Quality & Compliance Audit Agent", "Compliance Audit", status, detail, status)

    def log_emergency(self, incident_type: str, zone_name: str):
        return self.add_entry("Emergency Response Orchestrator",
                               f"{incident_type.replace('_', ' ').title()} Triggered",
                               "critical", f"Emergency response initiated in {zone_name}", "critical")

    def log_risk_update(self, risk_score: float, severity: str, zone_count: int):
        return self.add_entry("Risk Fusion Supervisor", "Risk Score Update", severity,
                               f"Overall risk: {risk_score:.3f} — {zone_count} zones evaluated", severity)

    def log_system(self, message: str):
        return self.add_entry("ZeroHarm System", "System Event", "info", message, "info")

    def get_recent(self, count: int = 20) -> List[Dict]:
        return list(reversed(self.entries[-count:]))

    def get_by_severity(self, severity: str) -> List[Dict]:
        return [e for e in reversed(self.entries) if e["severity"] == severity]

    def clear(self):
        self.entries = []
