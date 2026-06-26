from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import hashlib
import json

from config_loader import get_incident_records, get_zones, get_agent_settings
import constants as C

_ips = get_agent_settings()["incident_patterns"]


class IncidentPatternIntelligence:
    def __init__(self):
        self.incidents = get_incident_records()
        self.patterns = self._discover_patterns()
        self._zone_name_map = {z["id"]: z["name"] for z in get_zones()}

    def _discover_patterns(self) -> List[Dict]:
        patterns = []
        zone_incidents = {}
        cause_incidents = {}
        type_combinations = {}
        for inc in self.incidents:
            zone = inc["zone"]
            zone_incidents.setdefault(zone, []).append(inc)
            for cause in inc["contributing_factors"]:
                normalized_cause = cause.lower().strip()
                cause_incidents.setdefault(normalized_cause, []).append(inc)
            combo_key = f"{inc['type']}+{inc['zone']}"
            type_combinations.setdefault(combo_key, []).append(inc)

        for zone, incidents in zone_incidents.items():
            if len(incidents) >= 2:
                max_severity = max(_ips["severity_order"].get(i["severity"], 0) for i in incidents)
                severity_label = _ips["severity_labels"].get(str(max_severity), "INFO")
                patterns.append({
                    "type": "RECURRING_ZONE", "zone": zone,
                    "incident_count": len(incidents), "incidents": [i["id"] for i in incidents],
                    "description": f"{zone} has recorded {len(incidents)} incidents - highest in plant",
                    "severity": severity_label,
                    "recommendation": f"Zone-specific safety review recommended for {zone}. Review controls, increase monitoring frequency.",
                })

        for cause, incidents in sorted(cause_incidents.items(), key=lambda x: len(x[1]), reverse=True)[:_ips["top_causes_limit"]]:
            if len(incidents) >= 2:
                patterns.append({
                    "type": "RECURRING_CAUSE", "cause": cause,
                    "incident_count": len(incidents), "incidents": [i["id"] for i in incidents],
                    "description": f"'{cause}' contributed to {len(incidents)} incidents",
                    "severity": "HIGH",
                    "recommendation": f"Address root cause: {cause}. Develop targeted preventive action plan.",
                })

        for combo, incidents in type_combinations.items():
            if len(incidents) >= 2:
                inc_type, zone = combo.split("+", 1)
                patterns.append({
                    "type": "TYPE_ZONE_PATTERN", "zone": zone, "incident_type": inc_type,
                    "incident_count": len(incidents),
                    "description": f"{inc_type.replace('_', ' ').title()} has occurred {len(incidents)} times in {zone}",
                    "severity": "MEDIUM",
                    "recommendation": f"Review {inc_type.replace('_', ' ')} controls for {zone}. Consider additional engineering controls.",
                })

        patterns.sort(key=lambda x: _ips["pattern_sort_order"].get(x["severity"], 5))
        return patterns

    def get_all_patterns(self) -> List[Dict]:
        return self.patterns

    def get_zone_patterns(self, zone_id: str) -> List[Dict]:
        return [p for p in self.patterns if p.get("zone", "").startswith(zone_id)]

    def get_prevention_recommendations(self, zone_id: str, permit_type: str) -> List[str]:
        zone_name = self._zone_name_map.get(zone_id, "")
        recommendations = []
        for inc in self.incidents:
            if zone_name and inc["zone"] == zone_name:
                recommendations.extend(inc["lessons"].split(". "))
            if permit_type.replace("_", " ").lower() in inc["description"].lower():
                recommendations.extend(inc["lessons"].split(". "))
        for p in self.patterns:
            if p.get("zone") == zone_name and p.get("recommendation"):
                recommendations.append(p["recommendation"])
        return list(set(recommendations))[:_ips["max_prevention_recs"]]

    def get_statistics(self) -> Dict:
        type_counts = {}
        severity_counts = {}
        zone_counts = {}
        for inc in self.incidents:
            type_counts[inc["type"]] = type_counts.get(inc["type"], 0) + 1
            severity_counts[inc["severity"]] = severity_counts.get(inc["severity"], 0) + 1
            zone_counts[inc["zone"]] = zone_counts.get(inc["zone"], 0) + 1
        return {
            "total_incidents": len(self.incidents),
            "by_type": type_counts,
            "by_severity": severity_counts,
            "by_zone": zone_counts,
            "top_contributing_factors": self._get_top_factors(),
        }

    def _get_top_factors(self) -> List[Dict]:
        factor_counts = {}
        for inc in self.incidents:
            for factor in inc["contributing_factors"]:
                factor_counts[factor] = factor_counts.get(factor, 0) + 1
        sorted_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"factor": f, "count": c} for f, c in sorted_factors[:_ips["top_causes_limit"]]]
