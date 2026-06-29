import json
import os

_config_dir = os.path.join(os.path.dirname(__file__), "config")
_cache = {}

def load_config(name):
    if name not in _cache:
        path = os.path.join(_config_dir, f"{name}.json")
        try:
            with open(path, "r") as f:
                _cache[name] = json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"Config file not found: {path}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in config file {path}: {e}")
        except PermissionError as e:
            raise RuntimeError(f"Permission denied reading config file {path}: {e}")
    return _cache[name]

def get_zones():
    return load_config("zones")

def get_sensor_defaults():
    return load_config("sensors")

def get_scenarios():
    return load_config("scenarios")

def get_regulatory_standards():
    return load_config("regulatory_standards")

def get_emergency_templates():
    return load_config("emergency_templates")

def get_incident_records():
    return load_config("incident_records")

def get_rag_documents():
    return load_config("rag_documents")

def get_safety_practices():
    return load_config("safety_practices")

def get_compliance_checklist():
    return load_config("compliance_checklist")

def get_agent_settings():
    return load_config("agent_settings")

def get_sensor_types():
    return load_config("sensors")["types"]

def get_worker_names():
    return [
        "Rajesh Kumar", "Suresh Patel", "Amit Singh", "Vikram Reddy", "Manoj Joshi",
        "Ravi Shankar", "Dinesh Verma", "Priya Sharma", "Anita Desai", "Sunil Rao",
        "Karthik Nair", "Prakash Mishra", "Neha Gupta", "Rahul Saxena", "Deepak Yadav",
        "Sanjay Mehta", "Arun Pillai", "Divya Chauhan", "Vijay Thakur", "Rakesh Pandey",
    ]

def get_vision_settings():
    return load_config("vision_settings")

def get_plant_name():
    return "Visakhapatnam Steel Plant"
