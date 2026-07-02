from typing import Dict, List, Optional
import re

import constants as C
from config_loader import get_incident_records


class ChatAssistant:
    def __init__(self):
        self.incidents = get_incident_records()

    def _find_zone(self, text: str) -> Optional[str]:
        zones = {
            "coke oven": "Z01", "coke oven battery": "Z01",
            "blast furnace": "Z02", "blast furnace area": "Z02",
            "steelmaking": "Z03", "bos": "Z03",
            "continuous casting": "Z04", "casting": "Z04",
            "hot rolling": "Z05", "rolling mill": "Z05",
            "raw material": "Z06", "material yard": "Z06",
            "gas holder": "Z07", "gas holder area": "Z07",
            "control room": "Z08", "central control": "Z08",
            "maintenance workshop": "Z09", "workshop": "Z09",
            "cooling tower": "Z10",
        }
        lower = text.lower()
        for name, zid in zones.items():
            if name in lower:
                return zid
        return None

    def _classify_intent(self, message: str) -> str:
        lower = message.lower()
        if any(w in lower for w in ["risk", "danger", "hazard", "safe"]):
            return "risk"
        if any(w in lower for w in ["alert", "alarm", "critical", "warning"]):
            return "alerts"
        if any(w in lower for w in ["permit", "ptw", "work permit", "hot work"]):
            return "permits"
        if any(w in lower for w in ["compliance", "audit", "regulation", "standard"]):
            return "compliance"
        if any(w in lower for w in ["incident", "accident", "happen", "history", "past"]):
            return "incident"
        if any(w in lower for w in ["health", "overall", "plant status", "summary"]):
            return "health"
        if any(w in lower for w in ["emergency", "evacuate", "drill"]):
            return "emergency"
        if any(w in lower for w in ["trend", "forecast", "predict", "future"]):
            return "forecast"
        if any(w in lower for w in ["cost", "money", "fine", "penalty", "financial"]):
            return "cost"
        return "general"

    async def answer(self, message: str, plant_state: Optional[Dict] = None,
                     risk_result: Optional[Dict] = None,
                     compliance_result: Optional[Dict] = None,
                     health_index: Optional[Dict] = None,
                     risk_trend: Optional[List] = None,
                     alerts: Optional[List] = None) -> Dict:
        intent = self._classify_intent(message)
        zone_id = self._find_zone(message)
        zone_scores = (plant_state or {}).get("zone_risk_scores", {})

        if intent == "risk":
            if zone_id:
                score = zone_scores.get(zone_id, "unknown")
                return {"intent": intent, "answer": f"Zone {zone_id} risk score is {score}.", "data": {"zone": zone_id, "score": score}}
            score = (risk_result or {}).get("risk_score", "unknown")
            sev = (risk_result or {}).get("severity", "unknown")
            return {"intent": intent, "answer": f"Plant-wide risk: {sev.upper()} at score {score}.", "data": {"score": score, "severity": sev}}

        if intent == "alerts":
            count = len(alerts or [])
            critical = sum(1 for a in (alerts or []) if a.get("severity") == "critical")
            return {"intent": intent, "answer": f"There are {count} active alerts ({critical} critical).", "data": {"total": count, "critical": critical, "alerts": alerts}}

        if intent == "permits":
            permits = (plant_state or {}).get("active_permits", [])
            return {"intent": intent, "answer": f"{len(permits)} active permits.", "data": {"count": len(permits), "permits": permits}}

        if intent == "compliance":
            score = (compliance_result or {}).get(C.OVERALL_COMPLIANCE_SCORE_KEY, "unknown")
            return {"intent": intent, "answer": f"Overall compliance score: {score}%.", "data": {"score": score}}

        if intent == "incident":
            if self.incidents:
                last = self.incidents[-1]
                return {"intent": intent, "answer": f"Last incident: {last.get('description', 'N/A')}", "data": last}
            return {"intent": intent, "answer": "No incident records found.", "data": {}}

        if intent == "health":
            label = (health_index or {}).get("label", "unknown")
            overall = (health_index or {}).get("overall", "unknown")
            return {"intent": intent, "answer": f"Plant health: {label} ({overall}%).", "data": health_index}

        if intent == "emergency":
            return {"intent": intent, "answer": "Emergency response protocols are active. Check the Emergency tab for details.", "data": {}}

        if intent == "forecast":
            trend_len = len(risk_trend or [])
            return {"intent": intent, "answer": f"Risk trend tracked over {trend_len} readings. Check Forecast tab for ML prediction.", "data": {"readings": trend_len}}

        if intent == "cost":
            return {"intent": intent, "answer": "Use the Cost of Safety dashboard for detailed financial analytics.", "data": {}}

        return {"intent": "general", "answer": f"I understand you're asking about '{message[:80]}'. Try asking about risk, alerts, permits, compliance, incidents, or plant health.", "data": {}}
