from typing import Dict, List, Any

try:
    from sklearn.ensemble import IsolationForest
    import numpy as np
    _sklearn_available = True
except ImportError:
    _sklearn_available = False


class SensorAnomalyDetector:
    def __init__(self, contamination: float = 0.1):
        self._model = None
        self._contamination = contamination
        self._history: Dict[str, List[float]] = {}

    def feed_sensor(self, sensor_id: str, value: float) -> None:
        if sensor_id not in self._history:
            self._history[sensor_id] = []
        self._history[sensor_id].append(value)
        if len(self._history[sensor_id]) > 100:
            self._history[sensor_id] = self._history[sensor_id][-100:]

    def detect(self, sensor_id: str, value: float) -> Dict[str, Any]:
        if not _sklearn_available:
            return {"anomaly": False, "note": "sklearn not available"}

        hist = self._history.get(sensor_id, [])
        if len(hist) < 10:
            return {"anomaly": False, "note": "insufficient history"}

        recent = hist[-20:] + [value]
        X = np.array(recent).reshape(-1, 1)
        model = IsolationForest(contamination=self._contamination, random_state=42)
        preds = model.fit_predict(X)
        is_anomaly = preds[-1] == -1

        mean_val = float(np.mean(hist))
        std_val = float(np.std(hist)) if len(hist) > 1 else 0.0

        return {
            "anomaly": bool(is_anomaly),
            "sensor_id": sensor_id,
            "current_value": value,
            "mean": round(mean_val, 4),
            "std": round(std_val, 4),
            "z_score": round(abs(value - mean_val) / (std_val + 1e-8), 2),
        }

    def scan_all(self, sensors: Dict[str, Any]) -> List[Dict]:
        results = []
        for sid, s in sensors.items():
            val = s.get("value", 0)
            self.feed_sensor(sid, val)
            result = self.detect(sid, val)
            if result.get("anomaly"):
                results.append(result)
        return results
