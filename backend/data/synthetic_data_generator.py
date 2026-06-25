import numpy as np
import pandas as pd
import json
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

PLANT_ZONES = [
    {"id": "Z01", "name": "Coke Oven Battery", "x": 0.1, "y": 0.15, "width": 0.25, "height": 0.2, "hazard_class": "Extreme", "risk_baseline": 0.85},
    {"id": "Z02", "name": "Blast Furnace Area", "x": 0.45, "y": 0.1, "width": 0.2, "height": 0.3, "hazard_class": "Extreme", "risk_baseline": 0.9},
    {"id": "Z03", "name": "BOS / Steelmaking", "x": 0.75, "y": 0.15, "width": 0.2, "height": 0.25, "hazard_class": "High", "risk_baseline": 0.7},
    {"id": "Z04", "name": "Continuous Casting", "x": 0.1, "y": 0.45, "width": 0.3, "height": 0.2, "hazard_class": "Medium", "risk_baseline": 0.4},
    {"id": "Z05", "name": "Hot Rolling Mill", "x": 0.55, "y": 0.5, "width": 0.35, "height": 0.2, "hazard_class": "High", "risk_baseline": 0.65},
    {"id": "Z06", "name": "Raw Material Yard", "x": 0.05, "y": 0.75, "width": 0.25, "height": 0.2, "hazard_class": "Medium", "risk_baseline": 0.35},
    {"id": "Z07", "name": "Gas Holder Area", "x": 0.7, "y": 0.75, "width": 0.25, "height": 0.2, "hazard_class": "Extreme", "risk_baseline": 0.9},
    {"id": "Z08", "name": "Central Control Room", "x": 0.4, "y": 0.38, "width": 0.12, "height": 0.1, "hazard_class": "Low", "risk_baseline": 0.05},
    {"id": "Z09", "name": "Maintenance Workshop", "x": 0.4, "y": 0.75, "width": 0.2, "height": 0.15, "hazard_class": "Low", "risk_baseline": 0.15},
    {"id": "Z10", "name": "Cooling Tower Area", "x": 0.1, "y": 0.3, "width": 0.15, "height": 0.12, "hazard_class": "Low", "risk_baseline": 0.1},
]

SENSOR_TYPES = ["CO", "O2", "H2S", "LEL", "Temperature", "Pressure", "VOC", "NO2"]
PERMIT_TYPES = ["Confined Space Entry", "Hot Work", "Height Work", "Excavation", "Electrical", "Lockout-Tagout", "Critical Lift", "Radiography"]
EQUIPMENT_TAGS = [f"EQ-{i:04d}" for i in range(1, 51)]
WORKER_NAMES = [
    "Rajesh Kumar", "Suresh Patel", "Amit Singh", "Vikram Reddy", "Manoj Joshi",
    "Ravi Shankar", "Dinesh Verma", "Priya Sharma", "Anita Desai", "Sunil Rao",
    "Karthik Nair", "Prakash Mishra", "Neha Gupta", "Rahul Saxena", "Deepak Yadav",
    "Sanjay Mehta", "Arun Pillai", "Divya Chauhan", "Vijay Thakur", "Rakesh Pandey"
]

np.random.seed(42)
random.seed(42)


class SyntheticDataGenerator:
    def __init__(self, plant_name: str = "Visakhapatnam Steel Plant"):
        self.plant_name = plant_name
        self.zones = PLANT_ZONES
        self.sensors = self._create_sensors()
        self.active_permits = []
        self.workers = {w: {"active": False, "zone": None, "shift": None} for w in WORKER_NAMES}
        self.incident_history = []
        self.time_step = 0
        self.compound_event_active = False
        self.compound_event_timer = 0

    def _create_sensors(self) -> Dict:
        sensors = {}
        for zone in self.zones:
            zone_id = zone["id"]
            for stype in SENSOR_TYPES:
                sid = f"SENSOR-{zone_id}-{stype}"
                base_risk = zone["risk_baseline"]
                if stype == "LEL":
                    base_val = random.uniform(1, 8)
                    unit = "%LEL"
                    threshold = 20
                    critical = 40
                elif stype == "CO":
                    base_val = random.uniform(5, 30)
                    unit = "ppm"
                    threshold = 100
                    critical = 200
                elif stype == "O2":
                    base_val = random.uniform(19.5, 21.0)
                    unit = "%"
                    threshold = 19.0
                    critical = 18.0
                elif stype == "H2S":
                    base_val = random.uniform(0, 2)
                    unit = "ppm"
                    threshold = 10
                    critical = 20
                elif stype == "Temperature":
                    base_val = random.uniform(25, 45)
                    unit = "°C"
                    threshold = 65
                    critical = 85
                elif stype == "Pressure":
                    base_val = random.uniform(0.8, 1.2)
                    unit = "bar"
                    threshold = 1.8
                    critical = 2.5
                elif stype == "VOC":
                    base_val = random.uniform(0, 5)
                    unit = "ppm"
                    threshold = 50
                    critical = 100
                elif stype == "NO2":
                    base_val = random.uniform(0, 0.5)
                    unit = "ppm"
                    threshold = 3
                    critical = 5
                sensors[sid] = {
                    "id": sid,
                    "type": stype,
                    "zone_id": zone_id,
                    "zone_name": zone["name"],
                    "unit": unit,
                    "value": base_val,
                    "baseline": base_val,
                    "threshold": threshold,
                    "critical": critical,
                    "status": "normal",
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

        noise = np.random.normal(0, 0.08)
        if s["type"] == "O2":
            s["value"] += np.random.normal(0, 0.05)
            s["value"] = np.clip(s["value"], 15.0, 22.0)
            s["status"] = "critical" if s["value"] < s["critical"] else "warning" if s["value"] < s["threshold"] else "normal"
        elif s["type"] in ["LEL", "CO", "H2S", "VOC", "NO2"]:
            drift = max(0, np.random.exponential(0.02 * base_risk))
            s["value"] = s["baseline"] + drift
            s["status"] = "critical" if s["value"] >= s["critical"] else "warning" if s["value"] >= s["threshold"] else "normal"
        elif s["type"] == "Temperature":
            s["value"] += np.random.normal(0, 1.0)
            s["value"] = np.clip(s["value"], 20, 120)
            s["status"] = "critical" if s["value"] >= s["critical"] else "warning" if s["value"] >= s["threshold"] else "normal"
        elif s["type"] == "Pressure":
            s["value"] += np.random.normal(0, 0.03)
            s["value"] = np.clip(s["value"], 0.5, 3.0)
            s["status"] = "critical" if s["value"] >= s["critical"] else "warning" if s["value"] >= s["threshold"] else "normal"

        sensor_risk = 0.0
        if s["type"] == "O2":
            if s["value"] < s["critical"]:
                sensor_risk = 1.0
            elif s["value"] < s["threshold"]:
                sensor_risk = 0.7
        else:
            if s["value"] >= s["critical"]:
                sensor_risk = 1.0
            elif s["value"] >= s["threshold"]:
                sensor_risk = 0.7
            elif s["value"] >= s["threshold"] * 0.6:
                sensor_risk = 0.3
        s["risk_score"] = min(1.0, sensor_risk + base_risk * 0.2 * noise)

    def _get_active_permits_in_zone(self, zone_id: str) -> List[Dict]:
        return [p for p in self.active_permits if p["zone_id"] == zone_id and p["status"] == "active"]

    def _generate_permit(self) -> Optional[Dict]:
        if random.random() > 0.15:
            return None
        zone = random.choice(self.zones)
        ptype = random.choice(PERMIT_TYPES)
        start = datetime.now() + timedelta(minutes=random.randint(-30, 30))
        end = start + timedelta(hours=random.randint(1, 8))
        workers_assigned = random.sample(WORKER_NAMES, random.randint(1, 4))
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
                    if o2 and o2["status"] != "normal":
                        risks.append(f"O2 level {o2['value']:.1f}% ({o2['status']}) during confined space entry")
                        severity += 0.4
                    if lel and lel["status"] != "normal":
                        risks.append(f"LEL at {lel['value']:.1f}% during confined space entry")
                        severity += 0.3
                    if h2s and h2s["status"] != "normal":
                        risks.append(f"H2S at {h2s['value']:.1f}ppm during confined space entry")
                        severity += 0.3
                elif ptype == "Hot Work":
                    lel = zone_sensors.get("LEL")
                    voc = zone_sensors.get("VOC")
                    if lel and lel["status"] != "normal":
                        risks.append(f"LEL at {lel['value']:.1f}% during hot work")
                        severity += 0.5
                    if voc and voc["status"] != "normal":
                        risks.append(f"VOC at {voc['value']:.1f}ppm during hot work")
                        severity += 0.3
                elif ptype == "Height Work":
                    temp = zone_sensors.get("Temperature")
                    if temp and temp["status"] == "critical":
                        risks.append(f"Extreme heat ({temp['value']:.0f}°C) during height work")
                        severity += 0.3
                if risks and severity > 0.3:
                    findings.append({
                        "zone_id": zone_id,
                        "zone_name": zone["name"],
                        "permit_id": permit["id"],
                        "permit_type": ptype,
                        "risks": risks,
                        "severity": min(1.0, severity),
                        "compound_risk_score": min(1.0, severity + zone["risk_baseline"] * 0.3),
                        "recommendation": self._get_recommendation(ptype, risks),
                        "timestamp": datetime.now().isoformat(),
                    })
        return findings if findings else None

    def _get_recommendation(self, permit_type: str, risks: List[str]) -> str:
        if "LEL" in str(risks) and "Hot Work" in permit_type:
            return "IMMEDIATE SUSPENSION: Flammable atmosphere detected during hot work. Evacuate area and purge before any further work."
        if "O2" in str(risks) and "Confined Space" in permit_type:
            return "IMMEDIATE SUSPENSION: Unsafe oxygen level for confined space entry. Stop entry, ventilate area, and re-test atmosphere."
        if "H2S" in str(risks):
            return "IMMEDIATE SUSPENSION: Toxic gas detected. Evacuate area. Respiratory protection required before any re-entry."
        return "REVIEW REQUIRED: Multiple risk factors detected. Supervisor assessment needed before work continues."

    def _simulate_compound_event(self):
        if self.compound_event_active:
            self.compound_event_timer -= 1
            if self.compound_event_timer <= 0:
                self.compound_event_active = False
            return
        if random.random() > 0.05:
            return
        zone = random.choice([z for z in self.zones if z["hazard_class"] in ["High", "Extreme"]])
        zone_id = zone["id"]
        zone_sensors = {s["type"]: sid for sid, s in self.sensors.items() if s["zone_id"] == zone_id}
        if "LEL" in zone_sensors:
            self.sensors[zone_sensors["LEL"]]["value"] = random.uniform(22, 38)
            self.sensors[zone_sensors["LEL"]]["status"] = "warning"
        if "CO" in zone_sensors:
            self.sensors[zone_sensors["CO"]]["value"] = random.uniform(110, 190)
            self.sensors[zone_sensors["CO"]]["status"] = "warning"
        if "O2" in zone_sensors:
            self.sensors[zone_sensors["O2"]]["value"] = random.uniform(18.0, 18.9)
            self.sensors[zone_sensors["O2"]]["status"] = "warning"
        if "VOC" in zone_sensors:
            self.sensors[zone_sensors["VOC"]]["value"] = random.uniform(30, 60)
            self.sensors[zone_sensors["VOC"]]["status"] = "warning"
        permit_types_for_event = ["Confined Space Entry", "Hot Work"]
        ptype = random.choice(permit_types_for_event)
        self.active_permits.append({
            "id": f"PTW-EVENT-{uuid.uuid4().hex[:6].upper()}",
            "type": ptype,
            "zone_id": zone_id,
            "zone_name": zone["name"],
            "description": f"{ptype} in {zone['name']} (INCIDENT SCENARIO)",
            "status": "active",
            "issued_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=4)).isoformat(),
            "workers": random.sample(WORKER_NAMES, 2),
            "risk_level": "Critical",
        })
        self.compound_event_active = True
        self.compound_event_timer = 10

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
            except:
                pass
        self.active_permits = [p for p in self.active_permits if p["status"] == "active"]
        self._simulate_compound_event()
        compound_risks = self._check_compound_conditions()
        zone_risk_scores = self._compute_zone_risk_scores()
        return {
            "timestamp": datetime.now().isoformat(),
            "time_step": self.time_step,
            "sensors": {sid: {k: v for k, v in s.items() if k in ["id", "type", "zone_id", "zone_name", "value", "unit", "threshold", "critical", "status", "risk_score"]} for sid, s in self.sensors.items()},
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
                    permit_risk += 0.5
                elif p["risk_level"] == "High":
                    permit_risk += 0.3
                elif p["risk_level"] == "Medium":
                    permit_risk += 0.15
            permit_risk = min(1.0, permit_risk)
            compound_boost = 0.0
            if self.compound_event_active and zone["hazard_class"] in ["High", "Extreme"]:
                compound_boost = 0.3
            compound_risk_check = self._check_compound_conditions()
            if compound_risk_check:
                for cr in compound_risk_check:
                    if cr["zone_id"] == zid:
                        compound_boost = max(compound_boost, cr["compound_risk_score"] * 0.5)
            scores[zid] = min(1.0, sensor_risk * 0.5 + permit_risk * 0.3 + zone["risk_baseline"] * 0.15 + compound_boost)
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
