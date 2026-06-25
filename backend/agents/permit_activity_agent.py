from typing import Dict, List, Optional, Any
from datetime import datetime


class PermitActivityAgent:
    def __init__(self, agent_id: str = "permit_activity_1"):
        self.agent_id = agent_id
        self.name = "Permit Activity Agent"
        self.status = "idle"

    def analyze(self, state: Dict) -> Dict:
        self.status = "analyzing"
        permits = state.get("active_permits", [])
        findings = {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "total_active_permits": len(permits),
            "permits_by_type": {},
            "permits_by_zone": {},
            "permits_by_risk": {},
            "high_risk_permits": [],
            "overlapping_zone_permits": [],
            "summary": "",
            "severity": "normal",
        }
        if not permits:
            findings["summary"] = "NORMAL: No active permits"
            findings["severity"] = "normal"
            self.status = "completed"
            return findings
        for p in permits:
            ptype = p.get("type", "Unknown")
            zone_id = p.get("zone_id", "Unknown")
            risk = p.get("risk_level", "Low")
            findings["permits_by_type"][ptype] = findings["permits_by_type"].get(ptype, 0) + 1
            findings["permits_by_zone"][zone_id] = findings["permits_by_zone"].get(zone_id, 0) + 1
            findings["permits_by_risk"][risk] = findings["permits_by_risk"].get(risk, 0) + 1
            if risk in ["Critical", "High"]:
                findings["high_risk_permits"].append({
                    "id": p.get("id", ""),
                    "type": ptype,
                    "zone_id": zone_id,
                    "zone_name": p.get("zone_name", ""),
                    "risk_level": risk,
                    "workers": p.get("workers", []),
                    "description": p.get("description", ""),
                })
        zone_permit_count = findings["permits_by_zone"]
        for zid, count in zone_permit_count.items():
            if count > 1:
                zone_permits = [p for p in permits if p.get("zone_id") == zid]
                types = [p.get("type", "Unknown") for p in zone_permits]
                findings["overlapping_zone_permits"].append({
                    "zone_id": zid,
                    "zone_name": zone_permits[0].get("zone_name", ""),
                    "permit_count": count,
                    "permit_types": types,
                    "risk_levels": [p.get("risk_level", "Low") for p in zone_permits],
                })
        high_risk_count = len(findings["high_risk_permits"])
        overlap_count = len(findings["overlapping_zone_permits"])
        if high_risk_count > 0:
            findings["severity"] = "warning"
            findings["summary"] = f"WARNING: {high_risk_count} high/critical risk permits active across {len(findings['permits_by_zone'])} zones"
        if overlap_count > 0:
            findings["severity"] = "high"
            findings["summary"] = f"ALERT: {overlap_count} zones with overlapping permits ({high_risk_count} high-risk)"
        if findings["permits_by_risk"].get("Critical", 0) > 0:
            findings["severity"] = "critical"
        self.status = "completed"
        return findings
