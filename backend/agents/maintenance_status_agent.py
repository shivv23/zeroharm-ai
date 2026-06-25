from typing import Dict, List, Optional, Any
from datetime import datetime
import random


class MaintenanceStatusAgent:
    def __init__(self, agent_id: str = "maintenance_agent_1"):
        self.agent_id = agent_id
        self.name = "Maintenance Status Agent"
        self.status = "idle"
        self.equipment_status = {}
        self._seed_equipment()

    def _seed_equipment(self):
        zones = ["Z01", "Z02", "Z03", "Z04", "Z05", "Z06", "Z07"]
        eq_types = ["Pump", "Valve", "Compressor", "Tank", "Heat Exchanger", "Conveyor", "Fan", "Boiler"]
        for z in zones:
            for i in range(3, 6):
                eq_id = f"EQ-{z}-{i:03d}"
                eq_type = random.choice(eq_types)
                self.equipment_status[eq_id] = {
                    "id": eq_id,
                    "name": f"{eq_type} #{i}",
                    "type": eq_type,
                    "zone_id": z,
                    "status": "operational",
                    "maintenance_mode": False,
                    "last_maintenance": (datetime.now().isoformat()),
                    "next_maintenance_due": (datetime.now().isoformat()),
                    "bypass_active": False,
                    "failure_probability": random.uniform(0.01, 0.15),
                }

    def set_maintenance_mode(self, eq_id: str, active: bool):
        if eq_id in self.equipment_status:
            self.equipment_status[eq_id]["maintenance_mode"] = active
            self.equipment_status[eq_id]["bypass_active"] = active

    def analyze(self, state: Dict) -> Dict:
        self.status = "analyzing"
        active_permits = state.get("active_permits", [])
        findings = {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "equipment_in_maintenance": [],
            "equipment_bypassed": [],
            "maintenance_equipment_with_permits": [],
            "zone_maintenance_map": {},
            "summary": "",
            "severity": "normal",
        }
        for eq_id, eq in self.equipment_status.items():
            zone_id = eq["zone_id"]
            if eq["maintenance_mode"] or eq["bypass_active"]:
                entry = {"id": eq_id, "name": eq["name"], "type": eq["type"],
                         "zone_id": zone_id, "maintenance_mode": eq["maintenance_mode"],
                         "bypass_active": eq["bypass_active"]}
                findings["equipment_in_maintenance"].append(entry)
                if zone_id not in findings["zone_maintenance_map"]:
                    findings["zone_maintenance_map"][zone_id] = []
                findings["zone_maintenance_map"][zone_id].append(entry)
                zone_permits = [p for p in active_permits if p.get("zone_id") == zone_id]
                if zone_permits:
                    findings["maintenance_equipment_with_permits"].append({
                        "equipment": entry,
                        "permits": [{"id": p.get("id"), "type": p.get("type"), "risk_level": p.get("risk_level")}
                                    for p in zone_permits],
                        "zone_id": zone_id,
                    })
        if findings["maintenance_equipment_with_permits"]:
            findings["severity"] = "high"
            count = len(findings["maintenance_equipment_with_permits"])
            findings["summary"] = f"ALERT: {count} equipment in maintenance/bypass with active work permits in same zone"
        elif findings["equipment_in_maintenance"]:
            findings["severity"] = "info"
            findings["summary"] = f"INFO: {len(findings['equipment_in_maintenance'])} equipment in maintenance"
        else:
            findings["summary"] = "NORMAL: No maintenance conflicts detected"
        self.status = "completed"
        return findings
