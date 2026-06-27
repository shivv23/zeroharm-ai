import numpy as np
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config_loader import get_zones, get_sensor_defaults, get_worker_names, get_plant_name, get_agent_settings, get_sensor_types, get_equipment_types
import constants as C

_zones = get_zones()
_sensor_cfg = get_sensor_defaults()
_worker_names = get_worker_names()
_as = get_agent_settings()["synthetic_data"]
_sensor_types = get_sensor_types()

np.random.seed(_as["random_seed"])
random.seed(_as["random_seed"])


class SyntheticDataGenerator:
    def __init__(self, plant_name: str = C.PLANT_NAME):
        self.plant_name = plant_name
        self.zones = _zones
        self.sensors = self._create_sensors()
        self.active_permits = []
        self.workers = {w: {"active": False, "zone": None, "shift": None} for w in _worker_names}
        self.incident_history = []
        self.time_step = 0
        self.compound_event_active = False
        self.compound_event_timer = 0

    def _create_sensors(self) -> Dict:
        sensors = {}
        for zone in self.zones:
            zone_id = zone["id"]
            for stype in _sensor_types:
                sid = f"SENSOR-{zone_id}-{stype}"
                cfg = _sensor_cfg["defaults"].get(stype, {})
                base_risk = zone["risk_baseline"]
                lo, hi = cfg.get("baseline_range", [0, 1])
                base_val = random.uniform(lo, hi)
                sensors[sid] = {
                    "id": sid,
                    "type": stype,
                    "zone_id": zone_id,
                    "zone_name": zone["name"],
                    "unit": cfg.get("unit", ""),
                    "value": base_val,
                    "baseline": base_val,
                    "threshold": cfg.get("threshold", 0),
                    "critical": cfg.get("critical", 0),
                    "status": C.SENSOR_STATUS_NORMAL,
                    "risk_score": 0.0,
                }
        return sensors

    def _get_zone_by_id(self, zone_id: str) -> Dict:
        for z in self.zones:
            if z["id"] == zone_id:
                return z
        return self.zones[0]

    def _update_sensor(self, sensor_id: str):
        s = self.sensors[sensor_id]
        zone = self._get_zone_by_id(s["zone_id"])
        base_risk = zone["risk_baseline"]
        stype = s["type"]
        cfg = _sensor_cfg["defaults"].get(stype, {})

        noise = np.random.normal(0, _sensor_cfg["noise_std"])
        if stype == "O2":
            s["value"] += np.random.normal(0, _sensor_cfg["oxygen_noise_std"])
            s["value"] = np.clip(s["value"], _sensor_cfg["oxygen_clip_min"], _sensor_cfg["oxygen_clip_max"])
            s["status"] = C.SENSOR_STATUS_CRITICAL if s["value"] < s["critical"] else C.SENSOR_STATUS_WARNING if s["value"] < s["threshold"] else C.SENSOR_STATUS_NORMAL
        elif stype in ["LEL", "CO", "H2S", "VOC", "NO2"]:
            drift = max(0, np.random.exponential(_sensor_cfg["exponential_drift_factor"] * base_risk))
            s["value"] = s["baseline"] + drift
            s["status"] = C.SENSOR_STATUS_CRITICAL if s["value"] >= s["critical"] else C.SENSOR_STATUS_WARNING if s["value"] >= s["threshold"] else C.SENSOR_STATUS_NORMAL
        elif stype == "Temperature":
            s["value"] += np.random.normal(0, _sensor_cfg["temperature_noise_std"])
            s["value"] = np.clip(s["value"], _sensor_cfg["temperature_clip_min"], _sensor_cfg["temperature_clip_max"])
            s["status"] = C.SENSOR_STATUS_CRITICAL if s["value"] >= s["critical"] else C.SENSOR_STATUS_WARNING if s["value"] >= s["threshold"] else C.SENSOR_STATUS_NORMAL
        elif stype == "Pressure":
            s["value"] += np.random.normal(0, _sensor_cfg["pressure_noise_std"])
            s["value"] = np.clip(s["value"], _sensor_cfg["pressure_clip_min"], _sensor_cfg["pressure_clip_max"])
            s["status"] = C.SENSOR_STATUS_CRITICAL if s["value"] >= s["critical"] else C.SENSOR_STATUS_WARNING if s["value"] >= s["threshold"] else C.SENSOR_STATUS_NORMAL

        sensor_risk = 0.0
        if stype == "O2":
            if s["value"] < s["critical"]:
                sensor_risk = 1.0
            elif s["value"] < s["threshold"]:
                sensor_risk = 0.7
        else:
            if s["value"] >= s["critical"]:
                sensor_risk = 1.0
            elif s["value"] >= s["threshold"]:
                sensor_risk = 0.7
            elif s["value"] >= s["threshold"] * _sensor_cfg["risk_approaching_weight"]:
                sensor_risk = 0.3
        s["risk_score"] = min(1.0, max(0.0, sensor_risk + base_risk * _sensor_cfg["risk_noise_weight"] * noise))

    def _get_active_permits_in_zone(self, zone_id: str) -> List[Dict]:
        return [p for p in self.active_permits if p["zone_id"] == zone_id and p["status"] == "active"]

    def _generate_permit(self) -> Optional[Dict]:
        if random.random() > _as["permit_generation_prob"]:
            return None
        zone = random.choice(self.zones)
        ptype = random.choice(self.active_permits) if self.active_permits else C.DEFAULT_PERMIT_TYPE
        ptype = random.choice([C.DEFAULT_PERMIT_TYPE, "Confined Space Entry", "Height Work", "Excavation", "Electrical", "Lockout-Tagout", "Critical Lift", "Radiography"])
        start = datetime.now() + timedelta(minutes=random.randint(-30, 30))
        end = start + timedelta(hours=random.randint(_as["permit_min_hours"], _as["permit_max_hours"]))
        workers_assigned = random.sample(_worker_names, random.randint(_as["min_workers"], _as["max_workers"]))
        permit = {
            "id": f"PTW-{uuid.uuid4().hex[:8].upper()}",
            "type": ptype,
            "zone_id": zone["id"],
            "zone_name": zone["name"],
            "description": f"{ptype} in {zone['name']}",
            "status": "active",
            "issued_at": start.isoformat(),
            "expires_at": end.isoformat(),
            "workers": workers_assigned,
            "risk_level": "Low",
            "conditions_check": True,
        }
        if ptype == "Hot Work" and zone["hazard_class"] in ["High", "Extreme"]:
            permit["risk_level"] = "Critical"
        elif ptype == "Confined Space Entry":
            permit["risk_level"] = "High"
        return permit

    def _check_compound_conditions(self) -> Optional[Dict]:
        _csw = _as.get("compound_risk_severity_weights", {})
        _sev_thresh = _as.get("compound_risk_severity_threshold", 0.3)
        _baseline_mult = _as.get("compound_risk_baseline_multiplier", 0.3)
        findings = []
        for zone in self.zones:
            zone_id = zone["id"]
            permits = self._get_active_permits_in_zone(zone_id)
            if not permits:
                continue
            zone_sensors = {s["type"]: s for sid, s in self.sensors.items() if s["zone_id"] == zone_id}
            for permit in permits:
                ptype = permit["type"]
                risks = []
                severity = 0.0
                if ptype == "Confined Space Entry":
                    o2 = zone_sensors.get("O2")
                    lel = zone_sensors.get("LEL")
                    h2s = zone_sensors.get("H2S")
                    if o2 and o2["status"] != C.SENSOR_STATUS_NORMAL:
                        risks.append(f"O2 level {o2['value']:.1f}% ({o2['status']}) during confined space entry")
                        severity += _csw.get("confined_space_o2", 0.4)
                    if lel and lel["status"] != C.SENSOR_STATUS_NORMAL:
                        risks.append(f"LEL at {lel['value']:.1f}% during confined space entry")
                        severity += _csw.get("confined_space_lel", 0.3)
                    if h2s and h2s["status"] != C.SENSOR_STATUS_NORMAL:
                        risks.append(f"H2S at {h2s['value']:.1f}ppm during confined space entry")
                        severity += _csw.get("confined_space_h2s", 0.3)
                elif ptype == "Hot Work":
                    lel = zone_sensors.get("LEL")
                    voc = zone_sensors.get("VOC")
                    if lel and lel["status"] != C.SENSOR_STATUS_NORMAL:
                        risks.append(f"LEL at {lel['value']:.1f}% during hot work")
                        severity += _csw.get("hot_work_lel", 0.5)
                    if voc and voc["status"] != C.SENSOR_STATUS_NORMAL:
                        risks.append(f"VOC at {voc['value']:.1f}ppm during hot work")
                        severity += _csw.get("hot_work_voc", 0.3)
                elif ptype == "Height Work":
                    temp = zone_sensors.get("Temperature")
                    if temp and temp["status"] == C.SENSOR_STATUS_CRITICAL:
                        risks.append(f"Extreme heat ({temp['value']:.0f}°C) during height work")
                        severity += _csw.get("height_work_temp", 0.3)
                if risks and severity > _sev_thresh:
                    findings.append({
                        "zone_id": zone_id,
                        "zone_name": zone["name"],
                        "permit_id": permit["id"],
                        "permit_type": ptype,
                        "risks": risks,
                        "severity": min(1.0, severity),
                        "compound_risk_score": min(1.0, severity + zone["risk_baseline"] * _baseline_mult),
                        "recommendation": self._get_recommendation(ptype, risks),
                        "timestamp": datetime.now().isoformat(),
                    })
        return findings if findings else None

    def _get_recommendation(self, permit_type: str, risks: List[str]) -> str:
        if "LEL" in str(risks) and "Hot Work" in permit_type:
            return C.RECOMMENDATION_TEXTS.get("hot_work_lel", "IMMEDIATE SUSPENSION: Flammable atmosphere detected during hot work.")
        if "O2" in str(risks) and "Confined Space" in permit_type:
            return C.RECOMMENDATION_TEXTS.get("confined_space_o2", "IMMEDIATE SUSPENSION: Unsafe oxygen level for confined space entry.")
        if "H2S" in str(risks):
            return C.RECOMMENDATION_TEXTS.get("h2s", "IMMEDIATE SUSPENSION: Toxic gas detected.")
        return C.RECOMMENDATION_TEXTS.get("default", "REVIEW REQUIRED: Multiple risk factors detected.")

    def _simulate_compound_event(self):
        if self.compound_event_active:
            self.compound_event_timer -= 1
            if self.compound_event_timer <= 0:
                self.compound_event_active = False
            return
        if random.random() > _as["compound_event_prob"]:
            return
        zone = random.choice([z for z in self.zones if z["hazard_class"] in ["High", "Extreme"]])
        zone_id = zone["id"]
        zone_sensors = {s["type"]: sid for sid, s in self.sensors.items() if s["zone_id"] == zone_id}
        _cer = _sensor_cfg.get("compound_event_ranges", {})
        _ce_permits = _sensor_cfg.get("compound_event_permit_types", ["Confined Space Entry", "Hot Work"])
        _ce_hours = _sensor_cfg.get("compound_event_duration_hours", 4)
        _ce_workers = _sensor_cfg.get("compound_event_worker_count", 2)
        for stype, (lo, hi) in _cer.items():
            if stype in zone_sensors:
                self.sensors[zone_sensors[stype]]["value"] = random.uniform(lo, hi)
                self.sensors[zone_sensors[stype]]["status"] = C.SENSOR_STATUS_WARNING
        ptype = random.choice(_ce_permits)
        self.active_permits.append({
            "id": f"PTW-EVENT-{uuid.uuid4().hex[:6].upper()}",
            "type": ptype,
            "zone_id": zone_id,
            "zone_name": zone["name"],
            "description": f"{ptype} in {zone['name']} (INCIDENT SCENARIO)",
            "status": "active",
            "issued_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=_ce_hours)).isoformat(),
            "workers": random.sample(_worker_names, _ce_workers),
            "risk_level": "Critical",
        })
        self.compound_event_active = True
        self.compound_event_timer = _as["compound_event_timer"]

    def step(self) -> Dict:
        self.time_step += 1
        for sid in self.sensors:
            self._update_sensor(sid)
        new_permit = self._generate_permit()
        if new_permit:
            self.active_permits.append(new_permit)
        self.active_permits = [p for p in self.active_permits if p["status"] == "active"]
        for p in self.active_permits:
            try:
                exp = datetime.fromisoformat(p["expires_at"])
                if datetime.now() > exp:
                    p["status"] = "completed"
            except (ValueError, TypeError):
                pass
        self.active_permits = [p for p in self.active_permits if p["status"] == "active"]
        self._simulate_compound_event()
        compound_risks = self._check_compound_conditions()
        zone_risk_scores = self._compute_zone_risk_scores()
        sensor_keys = ["id", "type", "zone_id", "zone_name", "value", "unit", "threshold", "critical", "status", "risk_score"]
        return {
            "timestamp": datetime.now().isoformat(),
            "time_step": self.time_step,
            "sensors": {sid: {k: v for k, v in s.items() if k in sensor_keys} for sid, s in self.sensors.items()},
            "active_permits": self.active_permits,
            "compound_risks": compound_risks,
            "zone_risk_scores": zone_risk_scores,
            "plant_name": self.plant_name,
        }

    def _compute_zone_risk_scores(self) -> Dict[str, float]:
        scores = {}
        for zone in self.zones:
            zid = zone["id"]
            zone_sensors = [s for sid, s in self.sensors.items() if s["zone_id"] == zid]
            sensor_risk = np.mean([s["risk_score"] for s in zone_sensors]) if zone_sensors else 0
            permit_risk = 0.0
            zone_permits = self._get_active_permits_in_zone(zid)
            for p in zone_permits:
                if p["risk_level"] == "Critical":
                    permit_risk += _as["permit_risk_critical"]
                elif p["risk_level"] == "High":
                    permit_risk += _as["permit_risk_high"]
                elif p["risk_level"] == "Medium":
                    permit_risk += _as["permit_risk_medium"]
            permit_risk = min(1.0, permit_risk)
            compound_boost = 0.0
            if self.compound_event_active and zone["hazard_class"] in ["High", "Extreme"]:
                compound_boost = _as["compound_event_boost"]
            compound_risk_check = self._check_compound_conditions()
            if compound_risk_check:
                for cr in compound_risk_check:
                    if cr["zone_id"] == zid:
                        compound_boost = max(compound_boost, cr["compound_risk_score"] * _as["compound_risk_score_weight"])
            scores[zid] = min(1.0, sensor_risk * _as["zone_risk_sensor_weight"] + permit_risk * _as["zone_risk_permit_weight"] + zone["risk_baseline"] * _as["zone_risk_baseline_weight"] + compound_boost)
        return scores

    def apply_scenario_overrides(self, normal_state: Dict, scenario_state: Dict) -> Dict:
        for sid, sdata in scenario_state.get("sensors", {}).items():
            if sid in normal_state.get("sensors", {}):
                normal_state["sensors"][sid] = sdata
        scenario_permits = scenario_state.get("active_permits", [])
        scenario_permit_ids = {p["id"] for p in scenario_permits}
        normal_permits = [p for p in normal_state.get("active_permits", []) if p["id"] not in scenario_permit_ids]
        normal_state["active_permits"] = normal_permits + scenario_permits
        return normal_state

    def get_plant_layout_data(self) -> Dict:
        return {
            "zones": [{"id": z["id"], "name": z["name"], "x": z["x"], "y": z["y"],
                        "width": z["width"], "height": z["height"],
                        "hazard_class": z["hazard_class"]} for z in self.zones],
            "plant_name": self.plant_name,
        }


if __name__ == "__main__":
    gen = SyntheticDataGenerator()
    for _ in range(50):
        state = gen.step()
        print(f"Step {state['time_step']}: Compound risks: {len(state['compound_risks']) if state['compound_risks'] else 0}")
