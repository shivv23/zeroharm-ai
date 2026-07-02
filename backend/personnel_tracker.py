from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

from config_loader import get_zones, get_worker_names


class PersonnelTracker:
    def __init__(self):
        self.zones = get_zones()
        self.workers = get_worker_names()
        self._locations: Dict[str, Dict] = {}
        self._mustered: Dict[str, bool] = {}
        self._hazard_exposure: Dict[str, List[Dict]] = {}
        self._init_locations()

    def _init_locations(self):
        for w in self.workers:
            zone = random.choice(self.zones)
            self._locations[w] = {
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "last_seen": datetime.now().isoformat(),
                "status": "active",
            }
            self._mustered[w] = False
            self._hazard_exposure[w] = []

    def update_location(self, worker_name: str, zone_id: str):
        zone = next((z for z in self.zones if z["id"] == zone_id), None)
        if not zone:
            return
        self._locations[worker_name] = {
            "zone_id": zone_id,
            "zone_name": zone["name"],
            "last_seen": datetime.now().isoformat(),
            "status": "active",
        }
        hazard_class = zone.get("hazard_class", "").lower()
        if hazard_class in ("extreme", "high"):
            self._hazard_exposure[worker_name].append({
                "zone_id": zone_id, "zone_name": zone["name"],
                "entered_at": datetime.now().isoformat(),
                "hazard_class": hazard_class,
            })

    def trigger_mustering(self, emergency_zone_id: str = None):
        for w in self.workers:
            loc = self._locations.get(w, {})
            is_in_danger_zone = (
                emergency_zone_id and loc.get("zone_id") == emergency_zone_id
            )
            if is_in_danger_zone:
                self._mustered[w] = False
            else:
                self._mustered[w] = True
        return self.get_mustering_status(emergency_zone_id)

    def mark_mustered(self, worker_name: str):
        if worker_name in self._mustered:
            self._mustered[worker_name] = True

    def get_mustering_status(self, emergency_zone_id: str = None) -> Dict:
        total = len(self.workers)
        mustered = sum(1 for v in self._mustered.values() if v)
        missing = total - mustered
        in_danger = []
        if emergency_zone_id:
            in_danger = [
                {"name": w, "zone_id": loc.get("zone_id"), "zone_name": loc.get("zone_name")}
                for w, loc in self._locations.items()
                if loc.get("zone_id") == emergency_zone_id
            ]
        return {
            "total_personnel": total,
            "mustered": mustered,
            "missing": missing,
            "mustered_pct": round(mustered / total * 100, 1) if total else 0,
            "in_danger_zone": in_danger,
            "missing_personnel": [
                w for w, v in self._mustered.items() if not v
            ] if missing <= 10 else f"{missing} personnel not yet mustered",
            "emergency_zone_id": emergency_zone_id,
        }

    def get_all_locations(self) -> List[Dict]:
        return [
            {
                "name": w,
                "zone_id": loc.get("zone_id"),
                "zone_name": loc.get("zone_name"),
                "last_seen": loc.get("last_seen"),
                "status": loc.get("status"),
                "mustered": self._mustered.get(w, False),
            }
            for w, loc in self._locations.items()
        ]

    def get_zone_occupancy(self) -> List[Dict]:
        occupancy = {}
        for w, loc in self._locations.items():
            zid = loc.get("zone_id", "unknown")
            if zid not in occupancy:
                occupancy[zid] = {
                    "zone_id": zid,
                    "zone_name": loc.get("zone_name", "Unknown"),
                    "count": 0,
                    "personnel": [],
                }
            occupancy[zid]["count"] += 1
            occupancy[zid]["personnel"].append(w)
        return sorted(occupancy.values(), key=lambda x: x["count"], reverse=True)

    def get_hazard_exposure_report(self) -> Dict:
        report = {}
        for w, exposures in self._hazard_exposure.items():
            high_hazard = [e for e in exposures if e.get("hazard_class") in ("extreme", "high")]
            if high_hazard:
                report[w] = {
                    "total_exposures": len(exposures),
                    "high_hazard_exposures": len(high_hazard),
                    "recent": high_hazard[-3:] if high_hazard else [],
                }
        return {
            "workers_with_exposure": len(report),
            "details": report,
        }

    def get_personnel_count(self) -> int:
        return len(self.workers)
