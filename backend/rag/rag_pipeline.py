from typing import Dict, List
from datetime import datetime

from config_loader import get_rag_documents, get_safety_practices, get_agent_settings, get_emergency_templates
from rag.semantic_search import SemanticSearchPipeline
import constants as C

class RAGPipeline:
    def __init__(self):
        self._rp = get_agent_settings().get("rag_pipeline", {})
        self.documents = get_rag_documents()
        self.best_practices = get_safety_practices()
        self.vector_store = {}
        self.semantic = SemanticSearchPipeline()

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        if top_k is None:
            top_k = self._rp.get("default_top_k", C.DEFAULT_TOP_K)
        return self.semantic.search(query, top_k=top_k)

    def query_permit_compliance(self, permit_type: str, zone_hazard_class: str,
                                 sensor_readings: Dict[str, float]) -> Dict:
        return self.semantic.query_permit_compliance(permit_type, zone_hazard_class, sensor_readings)

    def query_emergency_protocol(self, incident_type: str) -> Dict:
        return self.semantic.query_emergency_protocol(incident_type)
