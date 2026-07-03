from typing import Dict, List, Optional
from datetime import datetime
import json
import os


OBSERVATION_TYPES = [
    "unsafe_condition", "unsafe_act", "near_miss", "hazardous_material_spill",
    "equipment_damage", "housekeeping", "ppe_violation", "environmental_concern",
    "ergonomic_hazard", "electrical_hazard",
]

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]


class SafetyObservationSystem:
    def __init__(self):
        self._storage_path = os.path.join(os.path.dirname(__file__), "data", "observations.json")
        self._ensure_storage()
        self._observations = self._load()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        if not os.path.exists(self._storage_path):
            with open(self._storage_path, "w") as f:
                json.dump([], f)

    def _load(self) -> List[Dict]:
        try:
            with open(self._storage_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save(self):
        with open(self._storage_path, "w") as f:
            json.dump(self._observations[-500:], f, indent=2)

    def submit(self, observation_type: str, zone_id: str, description: str,
               severity: str = "medium", submitted_by: str = "Anonymous",
               location_detail: str = "") -> Dict:
        obs = {
            "id": f"OBS-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self._observations)+1}",
            "type": observation_type,
            "zone_id": zone_id,
            "description": description,
            "severity": severity,
            "submitted_by": submitted_by,
            "location_detail": location_detail,
            "submitted_at": datetime.now().isoformat(),
            "status": "open",
            "reviewed_by": None,
            "reviewed_at": None,
            "resolution": None,
        }
        self._observations.append(obs)
        self._save()
        return obs

    def review(self, obs_id: str, reviewer: str, resolution: str, status: str = "closed"):
        for obs in self._observations:
            if obs["id"] == obs_id:
                obs["status"] = status
                obs["reviewed_by"] = reviewer
                obs["reviewed_at"] = datetime.now().isoformat()
                obs["resolution"] = resolution
                self._save()
                return obs
        return None

    def get_open(self) -> List[Dict]:
        return [o for o in self._observations if o.get("status") == "open"]

    def get_by_zone(self, zone_id: str) -> List[Dict]:
        return [o for o in self._observations if o.get("zone_id") == zone_id]

    def get_all(self, limit: int = 50) -> List[Dict]:
        return self._observations[-limit:][::-1]

    def get_trends(self) -> Dict:
        type_counts = {}
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        zone_counts = {}
        status_counts = {"open": 0, "in_review": 0, "closed": 0}
        monthly_counts = {}

        for obs in self._observations:
            t = obs.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

            sev = obs.get("severity", "medium")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

            z = obs.get("zone_id", "unknown")
            zone_counts[z] = zone_counts.get(z, 0) + 1

            st = obs.get("status", "open")
            status_counts[st] = status_counts.get(st, 0) + 1

            month = obs.get("submitted_at", "")[:7]
            monthly_counts[month] = monthly_counts.get(month, 0) + 1

        return {
            "total": len(self._observations),
            "by_type": type_counts,
            "by_severity": severity_counts,
            "by_zone": zone_counts,
            "by_status": status_counts,
            "monthly": dict(sorted(monthly_counts.items())),
            "open_count": status_counts.get("open", 0),
        }

    def get_observation_types(self) -> List[Dict]:
        return [{"id": t, "label": t.replace("_", " ").title()} for t in OBSERVATION_TYPES]
