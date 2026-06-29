import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import constants as C


class IncidentInvestigation:
    def __init__(self):
        self.investigations = {}
        self.capas = {}
        self._load_configs()

    def _load_configs(self):
        config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
        capa_path = os.path.join(config_dir, "capa_categories.json")
        tmpl_path = os.path.join(config_dir, "investigation_templates.json")
        self.capa_config = {"action_types": [], "status_flow": [], "severity_levels": [], "root_cause_categories": []}
        self.investigation_templates = {"5_why_template": {}, "fishbone_categories": [], "report_sections": []}
        if os.path.exists(capa_path):
            with open(capa_path) as f:
                self.capa_config = json.load(f)
        if os.path.exists(tmpl_path):
            with open(tmpl_path) as f:
                self.investigation_templates = json.load(f)

    def create_investigation(self, incident_data: Dict) -> Dict:
        inv_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now().isoformat()
        investigation = {
            "id": inv_id,
            "status": "open",
            "created_at": now,
            "updated_at": now,
            "incident_data": incident_data,
            "description": incident_data.get("description", incident_data.get("type", "Unknown incident")),
            "findings": [],
            "capas": [],
            "five_why": self.generate_5_why(incident_data.get("description", "")),
            "fishbone": self.generate_fishbone(incident_data.get("type", "generic")),
        }
        self.investigations[inv_id] = investigation
        return investigation

    def add_finding(self, investigation_id: str, finding: Dict) -> Optional[Dict]:
        inv = self.investigations.get(investigation_id)
        if not inv:
            return None
        finding_id = f"FND-{uuid.uuid4().hex[:6].upper()}"
        finding["id"] = finding_id
        finding["created_at"] = datetime.now().isoformat()
        inv["findings"].append(finding)
        inv["updated_at"] = datetime.now().isoformat()
        return finding

    def generate_5_why(self, incident_description: str) -> Dict:
        template = dict(self.investigation_templates.get("5_why_template", {}))
        template["incident_description"] = incident_description
        template["why_1"] = {"question": "Why did this incident occur?", "answer": ""}
        template["why_2"] = {"question": "Why did that happen?", "answer": ""}
        template["why_3"] = {"question": "What underlying condition allowed this?", "answer": ""}
        template["why_4"] = {"question": "Why was that condition present?", "answer": ""}
        template["why_5"] = {"question": "What is the systemic root cause?", "answer": ""}
        template["root_cause"] = ""
        template["corrective_actions"] = []
        return template

    def generate_fishbone(self, incident_type: str) -> Dict:
        categories = self.investigation_templates.get("fishbone_categories", [
            "People", "Process", "Equipment", "Environment", "Management", "Measurement"
        ])
        fishbone = {"incident_type": incident_type, "categories": {}}
        for cat in categories:
            fishbone["categories"][cat] = {"factors": [], "description": ""}
        return fishbone

    def create_capa(self, investigation_id: str, finding: Dict, action_type: str,
                    description: str, owner: str, deadline: str) -> Optional[Dict]:
        inv = self.investigations.get(investigation_id)
        if not inv:
            return None
        capa_id = f"CAPA-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now().isoformat()
        capa_item = {
            "id": capa_id,
            "investigation_id": investigation_id,
            "finding": finding,
            "action_type": action_type if action_type in self.capa_config.get("action_types", []) else "corrective",
            "description": description,
            "owner": owner,
            "deadline": deadline,
            "status": "open",
            "created_at": now,
            "updated_at": now,
            "closed_at": None,
            "verification_notes": "",
        }
        self.capas[capa_id] = capa_item
        inv["capas"].append(capa_id)
        inv["updated_at"] = now
        return capa_item

    def update_capa_status(self, capa_id: str, status: str) -> Optional[Dict]:
        capa = self.capas.get(capa_id)
        if not capa:
            return None
        valid_statuses = self.capa_config.get("status_flow", ["open", "in_progress", "completed", "verified", "closed"])
        if status not in valid_statuses:
            return None
        capa["status"] = status
        capa["updated_at"] = datetime.now().isoformat()
        if status == "closed":
            capa["closed_at"] = datetime.now().isoformat()
        return capa

    def list_investigations(self) -> List[Dict]:
        return [self.get_investigation(iid) for iid in self.investigations if self.get_investigation(iid)]

    def get_investigation(self, investigation_id: str) -> Optional[Dict]:
        inv = self.investigations.get(investigation_id)
        if not inv:
            return None
        result = dict(inv)
        result["capas"] = [self.capas.get(cid) for cid in inv.get("capas", []) if self.capas.get(cid)]
        return result

    def get_open_capas(self) -> List[Dict]:
        open_statuses = self.capa_config.get("status_flow", [])[:2]
        return [c for c in self.capas.values() if c["status"] in open_statuses]

    def get_capa_statistics(self) -> Dict:
        total = len(self.capas)
        if total == 0:
            return {"total": 0, "open": 0, "in_progress": 0, "completed": 0, "verified": 0, "closed": 0,
                    "overdue": 0, "completion_rate": 0.0}
        status_counts = {"open": 0, "in_progress": 0, "completed": 0, "verified": 0, "closed": 0}
        now = datetime.now()
        overdue = 0
        for c in self.capas.values():
            s = c["status"]
            if s in status_counts:
                status_counts[s] += 1
            if s not in ("closed", "verified") and c.get("deadline"):
                try:
                    dl = datetime.fromisoformat(c["deadline"])
                    if dl < now:
                        overdue += 1
                except (ValueError, TypeError):
                    pass
        closed_count = status_counts.get("closed", 0)
        completion_rate = round((closed_count / total) * 100, 1) if total > 0 else 0.0
        return {"total": total, **status_counts, "overdue": overdue, "completion_rate": completion_rate}

    def get_investigation_report(self, investigation_id: str) -> Optional[Dict]:
        inv = self.get_investigation(investigation_id)
        if not inv:
            return None
        now = datetime.now().isoformat()
        findings = inv.get("findings", [])
        capas = inv.get("capas", [])
        open_capas = [c for c in capas if c["status"] != "closed"]
        closed_capas = [c for c in capas if c["status"] == "closed"]
        report = {
            "report_id": f"RPT-{investigation_id}",
            "generated_at": now,
            "investigation_id": investigation_id,
            "executive_summary": {
                "incident": inv.get("description"),
                "status": inv.get("status"),
                "findings_count": len(findings),
                "total_capas": len(capas),
                "open_capas": len(open_capas),
                "closed_capas": len(closed_capas),
            },
            "incident_details": {
                "description": inv.get("description"),
                "created_at": inv.get("created_at"),
                "incident_data": inv.get("incident_data"),
            },
            "root_cause_analysis": {
                "five_why": inv.get("five_why"),
                "fishbone": inv.get("fishbone"),
                "findings": findings,
            },
            "capa_plan": capas,
            "timeline": [
                {"event": "Investigation created", "timestamp": inv.get("created_at")},
                {"event": "Report generated", "timestamp": now},
            ],
            "conclusion": {
                "summary": f"Investigation {investigation_id} {'completed' if len(open_capas) == 0 else 'in progress'}",
                "recommendations": [c.get("description") for c in capas if c["status"] != "closed"],
            },
        }
        return report
