from typing import Dict, List
from config_loader import get_incident_records

INCIDENT_COST_MAP = {
    "catastrophic": {"cost": 5_000_000, "label": "Catastrophic"},
    "critical": {"cost": 1_000_000, "label": "Critical"},
    "major": {"cost": 500_000, "label": "Major"},
    "moderate": {"cost": 100_000, "label": "Moderate"},
    "near_miss": {"cost": 50_000, "label": "Near Miss"},
}

REGULATORY_FINES = {
    "Factory Act": 50000,
    "OISD": 100000,
    "DGMS": 200000,
}


def compute_cost_of_safety(alerts: List[Dict] = None, active_permits: List[Dict] = None) -> Dict:
    incidents = get_incident_records()

    total_incident_cost = 0
    total_fines = 0
    severity_counts = {}
    zone_costs = {}
    yearly_costs = {}

    for inc in incidents:
        sev = inc.get("severity", "moderate")
        cost_info = INCIDENT_COST_MAP.get(sev, {"cost": 50000, "label": "Unknown"})
        cost = cost_info["cost"]
        total_incident_cost += cost
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

        zone = inc.get("zone", "Unknown")
        zone_costs[zone] = zone_costs.get(zone, 0) + cost

        year = inc.get("date", "")[:4] if inc.get("date") else "unknown"
        yearly_costs[year] = yearly_costs.get(year, 0) + cost

        reg_action = inc.get("regulatory_action", "")
        for reg_name, fine in REGULATORY_FINES.items():
            if reg_name in reg_action:
                total_fines += fine

    total_cost = total_incident_cost + total_fines

    alert_cost = (len(alerts or []) * 5000)
    permit_risk_cost = sum(5000 for p in (active_permits or []) if p.get("risk_level", "").lower() in ("critical", "high"))
    ongoing_risk_cost = alert_cost + permit_risk_cost

    return {
        "total_cost": total_cost,
        "total_fines": total_fines,
        "total_incident_cost": total_incident_cost,
        "ongoing_risk_cost": ongoing_risk_cost,
        "severity_breakdown": severity_counts,
        "zone_costs": zone_costs,
        "yearly_costs": yearly_costs,
        "total_incidents": len(incidents),
        "cost_per_incident_avg": round(total_incident_cost / max(len(incidents), 1)),
        "prevention_savings_estimate": round(ongoing_risk_cost * 12),
    }
