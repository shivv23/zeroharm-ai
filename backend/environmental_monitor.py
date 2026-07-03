from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random
import math

from config_loader import get_zones


LIMITS = {
    "co2": {"unit": "ppm", "limit": 5000, "warning": 4000, "label": "CO\u2082"},
    "co": {"unit": "ppm", "limit": 50, "warning": 35, "label": "CO"},
    "nox": {"unit": "ppm", "limit": 25, "warning": 15, "label": "NO\u2093"},
    "sox": {"unit": "ppm", "limit": 20, "warning": 12, "label": "SO\u2093"},
    "pm25": {"unit": "\u00b5g/m\u00b3", "limit": 60, "warning": 40, "label": "PM2.5"},
    "pm10": {"unit": "\u00b5g/m\u00b3", "limit": 100, "warning": 70, "label": "PM10"},
    "ozone": {"unit": "ppm", "limit": 0.12, "warning": 0.08, "label": "O\u2083"},
    "noise": {"unit": "dB", "limit": 85, "warning": 75, "label": "Noise"},
    "ph": {"unit": "", "limit_min": 6.5, "limit_max": 8.5, "label": "pH"},
    "tds": {"unit": "mg/L", "limit": 2000, "warning": 1500, "label": "TDS"},
    "turbidity": {"unit": "NTU", "limit": 5, "warning": 3, "label": "Turbidity"},
}


class EnvironmentalMonitor:
    def __init__(self):
        self.zones = get_zones()
        self._history: Dict[str, List[float]] = {}
        self._latest: Dict[str, float] = {}

    def update_from_sensors(self, sensors: Dict[str, Dict]) -> Dict:
        now = datetime.now()
        results = {}

        for metric_id, info in LIMITS.items():
            base_value = self._default_value(metric_id)
            sensor_influence = self._sensor_influence(metric_id, sensors)
            value = round(base_value + sensor_influence, 2)
            value = max(0, value)

            self._latest[metric_id] = value
            if metric_id not in self._history:
                self._history[metric_id] = []
            self._history[metric_id].append(value)
            if len(self._history[metric_id]) > 100:
                self._history[metric_id] = self._history[metric_id][-100:]

            results[metric_id] = {
                "value": value,
                "unit": info["unit"],
                "limit": info.get("limit"),
                "limit_min": info.get("limit_min"),
                "limit_max": info.get("limit_max"),
                "warning": info.get("warning"),
                "label": info["label"],
                "status": self._status(metric_id, value, info),
                "timestamp": now.isoformat(),
            }
        return results

    def _default_value(self, metric_id: str) -> float:
        defaults = {
            "co2": 420, "co": 8, "nox": 10, "sox": 5,
            "pm25": 30, "pm10": 55, "ozone": 0.04,
            "noise": 65, "ph": 7.2, "tds": 800, "turbidity": 2.0,
        }
        return defaults.get(metric_id, 0)

    def _sensor_influence(self, metric_id: str, sensors: Dict) -> float:
        sensor_map = {
            "co2": "CO2", "co": "CO", "nox": "NO2",
            "sox": "H2S", "pm25": "VOC", "pm10": "VOC",
            "ozone": "O2", "noise": "Temperature",
        }
        sensor_type = sensor_map.get(metric_id)
        if not sensor_type:
            return random.uniform(-1, 1)
        relevant = [
            s for s in sensors.values()
            if s.get("type") == sensor_type
        ]
        if not relevant:
            return random.uniform(-1, 1)
        avg_val = sum(s.get("value", 0) for s in relevant) / len(relevant)
        return avg_val * 0.1

    def _status(self, metric_id: str, value: float, info: Dict) -> str:
        limit = info.get("limit")
        warning = info.get("warning")
        limit_min = info.get("limit_min")
        limit_max = info.get("limit_max")

        if limit_min is not None and limit_max is not None:
            if value < limit_min or value > limit_max:
                return "critical"
            if value < limit_min * 1.1 or value > limit_max * 0.9:
                return "warning"
            return "normal"

        if limit and value > limit:
            return "critical"
        if warning and value > warning:
            return "warning"
        return "normal"

    def get_latest(self, sensors: Optional[Dict] = None) -> Dict:
        if sensors:
            return self.update_from_sensors(sensors)
        return self._latest

    def get_history(self, metric_id: str, hours: int = 24) -> List[Dict]:
        raw = self._history.get(metric_id, [])
        info = LIMITS.get(metric_id, {"unit": ""})
        now = datetime.now()
        return [
            {"timestamp": (now - timedelta(hours=hours - i)).isoformat(),
             "value": v, "unit": info["unit"]}
            for i, v in enumerate(raw[-hours:])
        ]

    def get_summary(self, sensors: Optional[Dict] = None) -> Dict:
        metrics = self.get_latest(sensors)
        critical = sum(1 for m in metrics.values() if m.get("status") == "critical")
        warning = sum(1 for m in metrics.values() if m.get("status") == "warning")
        normal = sum(1 for m in metrics.values() if m.get("status") == "normal")
        return {
            "total_metrics": len(metrics),
            "critical": critical,
            "warning": warning,
            "normal": normal,
            "overall_status": "critical" if critical > 0 else "warning" if warning > 0 else "normal",
            "metrics": metrics,
            "updated_at": datetime.now().isoformat(),
        }

    def get_compliance(self, sensors: Optional[Dict] = None) -> Dict:
        metrics = self.get_latest(sensors)
        standards = [
            {"standard": "CPCB (India)", "metrics_applicable": ["pm25", "pm10", "nox", "sox", "noise"]},
            {"standard": "OSHA (US)", "metrics_applicable": ["co", "co2", "noise", "ozone"]},
            {"standard": "EPA (US)", "metrics_applicable": ["pm25", "pm10", "ozone", "sox"]},
            {"standard": "ISO 14001", "metrics_applicable": list(metrics.keys())},
        ]
        for std in standards:
            relevant = [m for m in std["metrics_applicable"] if m in metrics]
            non_compliant = [m for m in relevant if metrics[m]["status"] == "critical"]
            std["compliant"] = len(non_compliant) == 0
            std["total_applicable"] = len(relevant)
            std["non_compliant_count"] = len(non_compliant)
            std["non_compliant_metrics"] = non_compliant
        return {"standards": standards}
