from typing import Dict, List
from datetime import datetime
import copy
import random

from config_loader import get_zones, get_scenarios
import constants as C

_zones_dict = {z["id"]: z["name"] for z in get_zones()}


class WhatIfSimulator:
    def __init__(self):
        self.name = C.AGENT_WHAT_IF
        self.scenarios = get_scenarios()
        self.active_scenario = None
        self.custom_scenarios = []
        self._default_threshold = C.SENSOR_DEFAULT_THRESHOLD
        self._default_critical = C.SENSOR_DEFAULT_CRITICAL
        self._risk_bonus = C.SIM_RISK_BONUS_ADDER
        self._ptw_id_range = C.SIM_PTW_ID_RANGE
        self._ptw_custom_id_range = C.SIM_PTW_CUSTOM_ID_RANGE
        self._default_zone = C.SIM_DEFAULT_ZONE
        self._sim_worker = C.SIM_WORKER_NAME
        self._custom_worker = C.SIM_CUSTOM_WORKER_NAME

    def list_scenarios(self) -> List[Dict]:
        return [{"id": sid, **sc} for sid, sc in self.scenarios.items()]

    def _apply_sensor_status(self, s: Dict, new_val: float):
        stype = s.get("type", "")
        threshold = s.get("threshold", self._default_threshold)
        critical_val = s.get("critical", self._default_critical)
        s["value"] = round(new_val, 2)
        if stype == "O2":
            s["status"] = C.SENSOR_STATUS_CRITICAL if new_val < critical_val else C.SENSOR_STATUS_WARNING if new_val < threshold else C.SENSOR_STATUS_NORMAL
        else:
            s["status"] = C.SENSOR_STATUS_CRITICAL if new_val >= critical_val else C.SENSOR_STATUS_WARNING if new_val >= threshold else C.SENSOR_STATUS_NORMAL
        s["risk_score"] = min(1.0, abs(new_val - threshold) / threshold + self._risk_bonus)

    def _build_permit(self, pinfo: Dict, scenario_id: str, scenario_name: str) -> Dict:
        lo, hi = self._ptw_id_range
        return {
            "id": f"PTW-SCEN-{scenario_id[:4].upper()}-{random.randint(lo, hi)}",
            "type": pinfo.get("type", C.DEFAULT_PERMIT_TYPE),
            "zone_id": pinfo.get("zone_id", self._default_zone),
            "zone_name": _zones_dict.get(pinfo.get("zone_id", ""), ""),
            "description": f"{pinfo.get('type', 'Work')} ({scenario_name})",
            "status": "active",
            "risk_level": pinfo.get("risk_level", "High"),
            "issued_at": datetime.now().isoformat(),
            "workers": [self._sim_worker],
            "conditions_check": False,
        }

    def apply_scenario(self, scenario_id: str, plant_state: Dict) -> Dict:
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            return {"error": f"Scenario {scenario_id} not found"}
        self.active_scenario = scenario_id
        modified = copy.deepcopy(plant_state)
        for zone_id, sensor_changes in scenario.get("changes", {}).items():
            for sensor_type, (low, high) in sensor_changes.items():
                for sid, s in modified.get("sensors", {}).items():
                    if s.get("zone_id") == zone_id and s.get("type") == sensor_type:
                        self._apply_sensor_status(s, random.uniform(low, high))
                        break
        for pinfo in scenario.get("permits_to_add", []):
            modified.setdefault("active_permits", []).append(self._build_permit(pinfo, scenario_id, scenario["name"]))
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
                        self._apply_sensor_status(s, random.uniform(low, high))
                        break
        for pinfo in permits_to_add:
            clo, chi = self._ptw_custom_id_range
            permit = {
                "id": f"PTW-CUSTOM-{random.randint(clo, chi)}",
                "type": pinfo.get("type", C.DEFAULT_PERMIT_TYPE),
                "zone_id": pinfo.get("zone_id", self._default_zone),
                "zone_name": _zones_dict.get(pinfo.get("zone_id", ""), ""),
                "description": f"{pinfo.get('type', 'Work')} (Custom Scenario)",
                "status": "active",
                "risk_level": pinfo.get("risk_level", "High"),
                "issued_at": datetime.now().isoformat(),
                "workers": [self._custom_worker],
                "conditions_check": False,
            }
            modified.setdefault("active_permits", []).append(permit)
        modified["scenario_active"] = True
        modified["scenario_name"] = name
        return modified

    def create_custom_scenario(self, name: str, description: str, changes: Dict) -> str:
        sid = f"custom_{len(self.custom_scenarios) + 1}"
        self.custom_scenarios.append({
            "id": sid, "name": name, "description": description,
            "changes": changes, "permits_to_add": [], "expected_alert": "Custom scenario applied",
        })
        if len(self.custom_scenarios) > 50:
            self.custom_scenarios = self.custom_scenarios[-50:]
        return sid
