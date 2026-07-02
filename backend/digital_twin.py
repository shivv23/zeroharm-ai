from typing import Dict, List, Optional
from datetime import datetime
from config_loader import get_zones


class DigitalTwinAggregator:
    def __init__(self):
        self.zones = get_zones()

    def build_dashboard(self, plant_state: Optional[Dict] = None,
                        risk_result: Optional[Dict] = None,
                        compliance_result: Optional[Dict] = None,
                        health_index: Optional[Dict] = None,
                        risk_trend: Optional[List] = None,
                        alerts: Optional[List] = None,
                        activity_feed: Optional[List] = None) -> Dict:
        state = plant_state or {}
        sensors = state.get("sensors", {})
        permits = state.get("active_permits", [])
        zone_risk_scores = state.get("zone_risk_scores", {})

        sensor_health = self._sensor_health_metrics(sensors)
        permit_metrics = self._permit_metrics(permits)
        zone_metrics = self._zone_metrics(zone_risk_scores)
        kpi = self._compute_kpis(sensor_health, permit_metrics, zone_metrics,
                                  risk_result, alerts)
        status_summary = self._generate_status_summary(
            health_index, risk_result, sensor_health, alerts
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "plant_name": "Visakhapatnam Steel Plant",
            "kpi": kpi,
            "sensors": sensor_health,
            "permits": permit_metrics,
            "zones": zone_metrics,
            "alerts": {
                "total": len(alerts or []),
                "critical": sum(1 for a in (alerts or []) if a.get("severity") == "critical"),
                "high": sum(1 for a in (alerts or []) if a.get("severity") == "high"),
                "warning": sum(1 for a in (alerts or []) if a.get("severity") == "warning"),
            },
            "health_index": health_index or {"overall": 0, "label": "Unknown"},
            "risk_score": (risk_result or {}).get("risk_score", 0),
            "severity": (risk_result or {}).get("severity", "normal"),
            "compliance_score": (compliance_result or {}).get("overall_compliance_score", 0),
            "status_summary": status_summary,
            "trend_direction": self._trend_direction(risk_trend),
        }

    def _sensor_health_metrics(self, sensors: Dict) -> Dict:
        total = len(sensors)
        if total == 0:
            return {"total": 0, "online": 0, "offline": 0, "warning": 0, "critical": 0,
                    "online_pct": 0, "health_score": 0}
        online = sum(1 for s in sensors.values() if s.get("status") == "normal")
        warning = sum(1 for s in sensors.values() if s.get("status") == "warning")
        critical = sum(1 for s in sensors.values() if s.get("status") == "critical")
        offline = total - online - warning - critical
        health_score = round((online + warning * 0.5) / total * 100, 1)
        return {
            "total": total, "online": online, "offline": offline,
            "warning": warning, "critical": critical,
            "online_pct": round(online / total * 100, 1),
            "health_score": health_score,
        }

    def _permit_metrics(self, permits: List) -> Dict:
        total = len(permits)
        if total == 0:
            return {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "risk_score": 0}
        critical = sum(1 for p in permits if p.get("risk_level", "").lower() == "critical")
        high = sum(1 for p in permits if p.get("risk_level", "").lower() == "high")
        medium = sum(1 for p in permits if p.get("risk_level", "").lower() == "medium")
        low = sum(1 for p in permits if p.get("risk_level", "").lower() == "low")
        risk_score = round((critical * 4 + high * 3 + medium * 2 + low * 1) / (total * 4) * 100, 1)
        return {"total": total, "critical": critical, "high": high,
                "medium": medium, "low": low, "risk_score": risk_score}

    def _zone_metrics(self, zone_scores: Dict) -> List[Dict]:
        metrics = []
        for z in self.zones:
            zid = z["id"]
            score = zone_scores.get(zid, 0)
            metrics.append({
                "id": zid, "name": z["name"], "score": score,
                "hazard_class": z.get("hazard_class", ""),
            })
        return sorted(metrics, key=lambda x: x["score"], reverse=True)

    def _compute_kpis(self, sensor_health: Dict, permit_metrics: Dict,
                       zone_metrics: List[Dict], risk_result: Optional[Dict],
                       alerts: Optional[List]) -> Dict:
        avg_zone_risk = round(
            sum(z["score"] for z in zone_metrics) / max(len(zone_metrics), 1), 3
        ) if zone_metrics else 0
        return {
            "sensor_health_score": sensor_health.get("health_score", 0),
            "permit_risk_score": permit_metrics.get("risk_score", 0),
            "avg_zone_risk": avg_zone_risk,
            "overall_risk": (risk_result or {}).get("risk_score", 0),
            "total_alerts": len(alerts or []),
            "critical_alerts": sum(1 for a in (alerts or []) if a.get("severity") == "critical"),
            "zone_count": len(zone_metrics),
            "normal_zones": sum(1 for z in zone_metrics if z["score"] < 0.3),
            "warning_zones": sum(1 for z in zone_metrics if 0.3 <= z["score"] < 0.6),
            "critical_zones": sum(1 for z in zone_metrics if z["score"] >= 0.6),
        }

    def _generate_status_summary(self, health_index: Optional[Dict],
                                  risk_result: Optional[Dict],
                                  sensor_health: Dict, alerts: Optional[List]) -> Dict:
        lines = []
        severity = (risk_result or {}).get("severity", "normal")
        health_pct = (health_index or {}).get("overall", 0)

        if severity == "critical":
            lines.append({"level": "critical", "text": "CRITICAL: Compound risk condition detected"})
        elif severity == "high":
            lines.append({"level": "warning", "text": "High risk levels require attention"})
        elif health_pct >= 70 and sensor_health.get("health_score", 0) >= 70:
            lines.append({"level": "ok", "text": "Plant operating within normal parameters"})
        else:
            lines.append({"level": "info", "text": "Routine monitoring in progress"})

        if alerts:
            critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
            if critical_alerts:
                lines.append({
                    "level": "critical",
                    "text": f"{len(critical_alerts)} critical alert(s) require immediate action",
                })
        return {"lines": lines, "overall": severity}

    def _trend_direction(self, risk_trend: Optional[List]) -> str:
        if not risk_trend or len(risk_trend) < 5:
            return "insufficient_data"
        recent = risk_trend[-5:]
        if recent[-1] > recent[0] * 1.1:
            return "increasing"
        if recent[-1] < recent[0] * 0.9:
            return "decreasing"
        return "stable"
