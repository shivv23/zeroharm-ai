from typing import Dict, List, Optional, Any
from datetime import datetime
import copy
import random

ZONE_NAMES = {"Z01": "Coke Oven Battery", "Z02": "Blast Furnace Area", "Z03": "BOS / Steelmaking",
              "Z04": "Continuous Casting", "Z05": "Hot Rolling Mill", "Z06": "Raw Material Yard",
              "Z07": "Gas Holder Area", "Z08": "Central Control Room", "Z09": "Maintenance Workshop",
              "Z10": "Cooling Tower Area"}


SCENARIOS = {
    "vizag_replay": {
        "name": "Vizag 2025 Replay",
        "description": "Recreates the conditions that led to the Vizag Steel Plant explosion: gas pressure warnings + maintenance bypass + hot work permit in coke oven battery",
        "changes": {
            "Z01": {
                "LEL": (25, 38),
                "CO": (120, 200),
                "Temperature": (55, 75),
            },
            "Z07": {
                "LEL": (5, 12),
                "Pressure": (1.8, 2.3),
            },
        },
        "permits_to_add": [
            {"type": "Hot Work", "zone_id": "Z01", "risk_level": "Critical"},
            {"type": "Maintenance", "zone_id": "Z01", "risk_level": "High"},
        ],
        "expected_alert": "COMPOUND_RISK: Hot work + gas accumulation + maintenance in Z01",
    },
    "confined_space_near_miss": {
        "name": "Confined Space Near-Miss",
        "description": "Simulates O2 depletion in a confined space entry scenario with simultaneous H2S presence",
        "changes": {
            "Z01": {
                "O2": (16.5, 18.2),
                "H2S": (8, 18),
                "LEL": (3, 8),
            },
        },
        "permits_to_add": [
            {"type": "Confined Space Entry", "zone_id": "Z01", "risk_level": "Critical"},
        ],
        "expected_alert": "COMPOUND_RISK: Unsafe oxygen + toxic gas during confined space entry",
    },
    "gas_leak_cascade": {
        "name": "Gas Leak Cascade",
        "description": "Simulates a CO gas leak that spreads from Coke Oven to adjacent zones",
        "changes": {
            "Z01": {
                "CO": (250, 400),
                "LEL": (15, 30),
            },
            "Z10": {
                "CO": (80, 150),
            },
            "Z04": {
                "CO": (30, 60),
            },
        },
        "permits_to_add": [],
        "expected_alert": "CRITICAL: CO gas leak spreading across multiple zones",
    },
    "fire_scenario": {
        "name": "Fire in Gas Holder Area",
        "description": "Simulates a fire starting in the Gas Holder Area with rapid temperature rise and pressure increase",
        "changes": {
            "Z07": {
                "Temperature": (120, 250),
                "Pressure": (2.5, 3.5),
                "LEL": (40, 70),
                "CO": (300, 500),
            },
            "Z03": {
                "Temperature": (55, 80),
            },
        },
        "permits_to_add": [
            {"type": "Hot Work", "zone_id": "Z07", "risk_level": "Critical"},
        ],
        "expected_alert": "FIRE + EXPLOSION risk in Gas Holder Area",
    },
    "maintenance_mishap": {
        "name": "Maintenance LOTO Failure",
        "description": "Simulates a LOTO failure where equipment is returned to service while maintenance is still in progress",
        "changes": {
            "Z09": {
                "Temperature": (30, 45),
                "Pressure": (0.5, 1.5),
            },
        },
        "permits_to_add": [
            {"type": "Lockout-Tagout", "zone_id": "Z09", "risk_level": "High"},
            {"type": "Electrical", "zone_id": "Z09", "risk_level": "Critical"},
        ],
        "expected_alert": "Critical equipment returned to service during active maintenance",
    },
}


class WhatIfSimulator:
    def __init__(self):
        self.name = "What-If Scenario Simulator"
        self.scenarios = SCENARIOS
        self.active_scenario = None
        self.custom_scenarios = []

    def list_scenarios(self) -> List[Dict]:
        return [{"id": sid, **sc} for sid, sc in self.scenarios.items()]

    def apply_scenario(self, scenario_id: str, plant_state: Dict) -> Dict:
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            return {"error": f"Scenario {scenario_id} not found"}
        self.active_scenario = scenario_id
        modified = copy.deepcopy(plant_state)
        for zone_id, sensor_changes in scenario["changes"].items():
            for sensor_type, (low, high) in sensor_changes.items():
                for sid, s in modified.get("sensors", {}).items():
                    if s.get("zone_id") == zone_id and s.get("type") == sensor_type:
                        new_val = random.uniform(low, high)
                        s["value"] = round(new_val, 2)
                        if sensor_type == "O2":
                            threshold = s.get("threshold", 19.0)
                            critical = s.get("critical", 18.0)
                            s["status"] = "critical" if new_val < critical else "warning" if new_val < threshold else "normal"
                        else:
                            threshold = s.get("threshold", 20)
                            critical = s.get("critical", 40)
                            s["status"] = "critical" if new_val >= critical else "warning" if new_val >= threshold else "normal"
                        s["risk_score"] = min(1.0, abs(new_val - threshold) / threshold + 0.2)
                        break
        for permit_info in scenario.get("permits_to_add", []):
            permit = {
                "id": f"PTW-SCEN-{scenario_id[:4].upper()}-{random.randint(100, 999)}",
                "type": permit_info["type"],
                "zone_id": permit_info["zone_id"],
                "zone_name": ZONE_NAMES.get(permit_info["zone_id"], ""),
                "description": f"{permit_info['type']} ({scenario['name']})",
                "status": "active",
                "risk_level": permit_info.get("risk_level", "High"),
                "issued_at": datetime.now().isoformat(),
                "workers": ["Simulation Operator"],
                "conditions_check": False,
            }
            modified.setdefault("active_permits", []).append(permit)
        modified["scenario_active"] = True
        modified["scenario_name"] = scenario["name"]
        modified["scenario_description"] = scenario["description"]
        modified["scenario_expected_alert"] = scenario.get("expected_alert", "")
        return modified

    def reset_scenario(self, plant_state: Dict, original_generator) -> Dict:
        self.active_scenario = None
        return original_generator.step()

    def apply_custom(self, plant_state: Dict, changes: Dict, permits_to_add: List[Dict], name: str = "Custom Scenario") -> Dict:
        modified = copy.deepcopy(plant_state)
        for zone_id, sensor_changes in changes.items():
            for sensor_type, (low, high) in sensor_changes.items():
                for sid, s in modified.get("sensors", {}).items():
                    if s.get("zone_id") == zone_id and s.get("type") == sensor_type:
                        new_val = random.uniform(low, high)
                        s["value"] = round(new_val, 2)
                        if sensor_type == "O2":
                            threshold = s.get("threshold", 19.0)
                            critical = s.get("critical", 18.0)
                            s["status"] = "critical" if new_val < critical else "warning" if new_val < threshold else "normal"
                        else:
                            threshold = s.get("threshold", 20)
                            critical = s.get("critical", 40)
                            s["status"] = "critical" if new_val >= critical else "warning" if new_val >= threshold else "normal"
                        s["risk_score"] = min(1.0, abs(new_val - threshold) / threshold + 0.2)
                        break
        for pinfo in permits_to_add:
            permit = {
                "id": f"PTW-CUSTOM-{random.randint(1000, 9999)}",
                "type": pinfo.get("type", "Hot Work"),
                "zone_id": pinfo.get("zone_id", "Z01"),
                "zone_name": ZONE_NAMES.get(pinfo.get("zone_id", ""), ""),
                "description": f"{pinfo.get('type', 'Work')} (Custom Scenario)",
                "status": "active",
                "risk_level": pinfo.get("risk_level", "High"),
                "issued_at": datetime.now().isoformat(),
                "workers": ["Scenario Operator"],
                "conditions_check": False,
            }
            modified.setdefault("active_permits", []).append(permit)
        modified["scenario_active"] = True
        modified["scenario_name"] = name
        return modified

    def create_custom_scenario(self, name: str, description: str, changes: Dict) -> str:
        sid = f"custom_{len(self.custom_scenarios) + 1}"
        self.custom_scenarios.append({
            "id": sid,
            "name": name,
            "description": description,
            "changes": changes,
            "permits_to_add": [],
            "expected_alert": "Custom scenario applied",
        })
        return sid
