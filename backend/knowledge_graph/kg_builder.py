import networkx as nx
from typing import Dict, List, Optional, Any

from config_loader import get_regulatory_standards, get_agent_settings


class IndustrialKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.oisd_standards = get_regulatory_standards()
        _kg = get_agent_settings().get("knowledge_graph", {}).get("risk_patterns", {})
        self._risk_patterns = {
            ("Confined Space Entry", "O2"): {
                "risk": "Oxygen deficiency during confined space entry",
                "regulation": "Factory-Act-1948-Sec36",
                "critical_threshold": _kg.get("confined_space_o2_threshold", 19.0)
            },
            ("Hot Work", "LEL"): {
                "risk": "Flammable atmosphere during hot work",
                "regulation": "Factory-Act-1948-Sec37",
                "critical_threshold": _kg.get("hot_work_lel_threshold", 10.0)
            },
            ("Confined Space Entry", "H2S"): {
                "risk": "Toxic gas during confined space entry",
                "regulation": "Factory-Act-1948-Sec36",
                "critical_threshold": _kg.get("confined_space_h2s_threshold", 5.0)
            },
            ("Confined Space Entry", "LEL"): {
                "risk": "Flammable atmosphere during confined space entry",
                "regulation": "Factory-Act-1948-Sec37",
                "critical_threshold": _kg.get("confined_space_lel_threshold", 10.0)
            },
            ("Hot Work", "CO"): {
                "risk": "Carbon monoxide during hot work",
                "regulation": "Factory-Act-1948-Sec37",
                "critical_threshold": _kg.get("hot_work_co_threshold", 50.0)
            },
        }
        self._build_schema()

    def _build_schema(self):
        self.graph.add_node("schema", type="meta", description="Industrial Safety Knowledge Graph")
        for entity in ["ZONE", "EQUIPMENT", "SENSOR", "PERMIT", "WORKER", "INCIDENT", "HAZARD", "REGULATION"]:
            self.graph.add_node(entity, type="entity_class", description=f"Industrial Safety entity: {entity}")

    def add_zone(self, zone_id: str, name: str, hazard_class: str, x: float, y: float):
        self.graph.add_node(zone_id, type="ZONE", name=name, hazard_class=hazard_class, x=x, y=y)

    def add_equipment(self, eq_id: str, name: str, zone_id: str, equipment_type: str):
        self.graph.add_node(eq_id, type="EQUIPMENT", name=name, equipment_type=equipment_type, zone_id=zone_id)
        self.graph.add_edge(eq_id, zone_id, relation="LOCATED_IN")

    def add_sensor(self, sensor_id: str, sensor_type: str, zone_id: str, threshold: float, critical: float):
        self.graph.add_node(sensor_id, type="SENSOR", sensor_type=sensor_type, zone_id=zone_id,
                            threshold=threshold, critical=critical)
        self.graph.add_edge(sensor_id, zone_id, relation="MONITORS_ZONE")

    def add_permit(self, permit_id: str, permit_type: str, zone_id: str, risk_level: str,
                   workers: List[str], issued_at: str):
        self.graph.add_node(permit_id, type="PERMIT", permit_type=permit_type, zone_id=zone_id,
                            risk_level=risk_level, issued_at=issued_at)
        self.graph.add_edge(permit_id, zone_id, relation="ACTIVE_IN")
        for w in workers:
            worker_node = f"WORKER-{w.replace(' ', '_')}"
            if not self.graph.has_node(worker_node):
                self.graph.add_node(worker_node, type="WORKER", name=w)
            self.graph.add_edge(permit_id, worker_node, relation="ASSIGNS")

    def add_regulation(self, standard_id: str, description: str, applicable_hazard_types: List[str]):
        self.graph.add_node(standard_id, type="REGULATION", description=description,
                            applicable_hazard_types=applicable_hazard_types)

    def add_hazard_relationship(self, permit_type: str, sensor_type: str, regulation_id: str, risk_description: str):
        rel_id = f"HAZARD-{permit_type}-{sensor_type}"
        self.graph.add_node(rel_id, type="HAZARD", permit_type=permit_type,
                            sensor_type=sensor_type, risk_description=risk_description)
        self.graph.add_edge(rel_id, regulation_id, relation="REGULATED_BY")

    def query_compound_risk_paths(self, zone_id: str, active_permit_types: List[str],
                                   sensor_readings: Dict[str, float]) -> List[Dict]:
        findings = []
        for ptype in active_permit_types:
            for (risk_ptype, sensor_type), info in self._risk_patterns.items():
                if ptype == risk_ptype and sensor_type in sensor_readings:
                    value = sensor_readings[sensor_type]
                    is_o2 = sensor_type == "O2"
                    if (value > info["critical_threshold"] if not is_o2 else value < info["critical_threshold"]):
                        severity = min(1.0, abs(value - info["critical_threshold"]) / info["critical_threshold"])
                        findings.append({
                            "zone_id": zone_id, "permit_type": ptype, "sensor_type": sensor_type,
                            "risk": info["risk"], "value": value,
                            "threshold": info["critical_threshold"], "severity": severity,
                            "regulation": info["regulation"],
                            "regulation_text": self.oisd_standards.get(info["regulation"], ""),
                        })
        return findings

    def get_regulatory_context(self, hazard_type: str) -> List[Dict]:
        results = []
        for node, data in self.graph.nodes(data=True):
            if data.get("type") == "HAZARD" and hazard_type.lower() in str(data).lower():
                for _, neighbor, edge_data in self.graph.edges(node, data=True):
                    if edge_data.get("relation") == "REGULATED_BY":
                        reg_data = self.graph.nodes[neighbor]
                        results.append({
                            "standard": neighbor, "description": reg_data.get("description", ""),
                            "risk": data.get("risk_description", ""),
                        })
        if not results:
            for std_id, desc in self.oisd_standards.items():
                if hazard_type.lower() in std_id.lower() or hazard_type.lower() in desc.lower():
                    results.append({
                        "standard": std_id, "description": desc,
                        "risk": f"Regulatory guidance applicable to {hazard_type}",
                    })
        return results

    def to_dict(self) -> Dict:
        nodes = []
        for node, data in self.graph.nodes(data=True):
            if data.get("type") and data["type"] != "entity_class" and node != "schema":
                nodes.append({"id": node, **data})
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({"source": u, "target": v, "relation": data.get("relation", "")})
        return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    kg = IndustrialKnowledgeGraph()
    for z in [
        {"id": "Z01", "name": "Coke Oven Battery", "hazard_class": "Extreme", "x": 0.1, "y": 0.15},
        {"id": "Z02", "name": "Blast Furnace Area", "hazard_class": "Extreme", "x": 0.45, "y": 0.1},
        {"id": "Z07", "name": "Gas Holder Area", "hazard_class": "Extreme", "x": 0.7, "y": 0.75},
    ]:
        kg.add_zone(**z)
    for reg_id, desc in list(kg.oisd_standards.items())[:5]:
        kg.add_regulation(reg_id, desc, ["gas_leak", "fire", "confined_space"])
    print("Knowledge Graph built with", kg.graph.number_of_nodes(), "nodes and", kg.graph.number_of_edges(), "edges")
    findings = kg.query_compound_risk_paths("Z01", ["Confined Space Entry"], {"O2": 18.2, "LEL": 12.0})
    for f in findings:
        print(f"  RISK: {f['risk']} (severity: {f['severity']:.2f}) -> {f['regulation']}")
