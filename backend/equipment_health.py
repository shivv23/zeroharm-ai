from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math

from config_loader import get_zones


class EquipmentHealthMonitor:
    def __init__(self):
        self.zones = get_zones()

    def assess_equipment(self, plant_state: Optional[Dict] = None) -> List[Dict]:
        sensors = plant_state.get("sensors", {}) if plant_state else {}
        permits = plant_state.get("active_permits", []) if plant_state else {}

        equipment_map = self._build_equipment(sensors, permits)
        for eq in equipment_map:
            eq["health_score"] = self._compute_health_score(eq, sensors)
            eq["failure_risk"] = self._compute_failure_risk(eq["health_score"])
            eq["remaining_useful_life_days"] = self._estimate_rul(eq["health_score"])
            eq["maintenance_priority"] = self._maintenance_priority(
                eq["health_score"], eq["failure_risk"]
            )
            eq["recommended_action"] = self._recommended_action(
                eq["health_score"], eq["failure_risk"]
            )
        return sorted(equipment_map, key=lambda x: x.get("failure_risk", 0), reverse=True)

    def _build_equipment(self, sensors: Dict, permits: List) -> List[Dict]:
        eq_types = {
            "coke_oven": {"name": "Coke Oven Battery", "zone_id": "Z01", "critical": True},
            "blast_furnace": {"name": "Blast Furnace", "zone_id": "Z02", "critical": True},
            "bos_converter": {"name": "BOS Converter", "zone_id": "Z03", "critical": True},
            "caster": {"name": "Continuous Caster", "zone_id": "Z04", "critical": True},
            "reheating_furnace": {"name": "Reheating Furnace", "zone_id": "Z05", "critical": True},
            "gas_holder": {"name": "Gas Holder", "zone_id": "Z07", "critical": True},
            "cooling_tower": {"name": "Cooling Tower", "zone_id": "Z10", "critical": False},
            "compressor": {"name": "Air Compressor", "zone_id": "Z06", "critical": False},
        }
        equipment = []
        for eq_id, info in eq_types.items():
            zone_sensors = [
                s for s in sensors.values()
                if s.get("zone_id") in (info["zone_id"], next(
                    (z["name"] for z in self.zones if z["id"] == info["zone_id"]), ""
                ))
            ]
            sensor_types = set(s.get("type", "") for s in zone_sensors)
            has_vibration = any("Vibration" in str(s.get("type", "")) for s in zone_sensors)
            equipment.append({
                "id": eq_id,
                "name": info["name"],
                "zone_id": info["zone_id"],
                "critical": info["critical"],
                "sensor_count": len(zone_sensors),
                "sensor_types": list(sensor_types),
                "has_vibration_monitoring": has_vibration,
                "active_permits_nearby": sum(
                    1 for p in permits if p.get("zone_id") == info["zone_id"]
                ),
            })
        return equipment

    def _compute_health_score(self, eq: Dict, sensors: Dict) -> float:
        if eq["sensor_count"] == 0:
            return 50.0

        zone_sensors = [
            s for s in sensors.values()
            if s.get("zone_id") in (eq["zone_id"], next(
                (z["name"] for z in self.zones if z["id"] == eq["zone_id"]), ""
            ))
        ]
        if not zone_sensors:
            return 60.0

        penalties = 0.0
        for s in zone_sensors:
            status = s.get("status", "normal")
            if status == "critical":
                penalties += 25
            elif status == "warning":
                penalties += 10

            val = s.get("value", 0)
            threshold = s.get("critical_threshold", 0)
            if threshold > 0 and val > threshold * 0.8:
                penalties += 5

        score = max(0, 100 - penalties)
        return round(score, 1)

    def _compute_failure_risk(self, health_score: float) -> float:
        return round(max(0, min(1, (100 - health_score) / 100)), 2)

    def _estimate_rul(self, health_score: float) -> int:
        if health_score >= 90:
            return 365
        if health_score >= 75:
            return 180
        if health_score >= 60:
            return 90
        if health_score >= 40:
            return 30
        if health_score >= 20:
            return 7
        return 1

    def _maintenance_priority(self, health_score: float, failure_risk: float) -> str:
        if health_score < 30 or failure_risk > 0.7:
            return "critical"
        if health_score < 60 or failure_risk > 0.4:
            return "high"
        if health_score < 80:
            return "medium"
        return "low"

    def _recommended_action(self, health_score: float, failure_risk: float) -> str:
        if health_score < 20:
            return "Immediate shutdown and replacement required"
        if health_score < 40:
            return "Schedule emergency maintenance within 24 hours"
        if health_score < 60:
            return "Plan maintenance within 1 week"
        if health_score < 80:
            return "Schedule routine maintenance within 30 days"
        return "Continue normal operations — monitor regularly"

    def get_summary(self, equipment_list: List[Dict]) -> Dict:
        total = len(equipment_list)
        healthy = sum(1 for e in equipment_list if e.get("health_score", 0) >= 80)
        warning = sum(1 for e in equipment_list if 40 <= e.get("health_score", 0) < 80)
        critical = sum(1 for e in equipment_list if e.get("health_score", 0) < 40)
        avg_health = round(
            sum(e.get("health_score", 0) for e in equipment_list) / total, 1
        ) if total else 0
        return {
            "total": total,
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "average_health": avg_health,
            "high_risk_count": sum(1 for e in equipment_list if e.get("failure_risk", 0) > 0.5),
        }
