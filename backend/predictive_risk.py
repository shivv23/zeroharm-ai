from typing import List, Dict
import numpy as np

try:
    from sklearn.linear_model import LinearRegression
    _sklearn_available = True
except ImportError:
    _sklearn_available = False

import constants as C


class PredictiveRiskForecaster:
    def __init__(self, window: int = 10):
        self.window = window
        self._history: List[float] = []

    def feed(self, score: float) -> None:
        self._history.append(score)
        if len(self._history) > self.window * 3:
            self._history = self._history[-self.window * 3:]

    def forecast(self, steps: int = 5) -> Dict:
        if len(self._history) < self.window or not _sklearn_available:
            return {"forecast": [], "trend": "insufficient_data", "next_risk": None}

        recent = self._history[-self.window:]
        X = np.arange(len(recent)).reshape(-1, 1)
        y = np.array(recent)
        model = LinearRegression()
        model.fit(X, y)
        future_X = np.arange(len(recent), len(recent) + steps).reshape(-1, 1)
        preds = model.predict(future_X).clip(0, 1).tolist()

        slope = model.coef_[0]
        if slope > 0.02:
            trend = "rising"
        elif slope < -0.02:
            trend = "falling"
        else:
            trend = "stable"

        return {
            "forecast": [round(p, 4) for p in preds],
            "trend": trend,
            "slope": round(float(slope), 4),
            "next_risk": round(preds[0], 4) if len(preds) > 0 else None,
            "current_risk": round(float(recent[-1]), 4),
        }
