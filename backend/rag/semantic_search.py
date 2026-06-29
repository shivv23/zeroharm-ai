from typing import Dict, List
from datetime import datetime
import numpy as np

from config_loader import get_rag_documents, get_safety_practices, get_emergency_templates, get_agent_settings
import constants as C

_rp = get_agent_settings()["rag_pipeline"]

class SemanticSearchPipeline:
    def __init__(self):
        self.documents = get_rag_documents()
        self.best_practices = get_safety_practices()
        self._model = None
        self._embeddings = None
        self._metadata = None
        self._build_index()

    def _build_index(self):
        self._metadata = []
        for doc_id, doc in self.documents.items():
            text = f"{doc['title']} {doc['content']}"
            self._metadata.append({
                "type": "regulatory", "id": doc_id, "title": doc["title"],
                "content": doc["content"], "text": text
            })
        for bp in self.best_practices:
            text = f"{bp['title']} {bp['content']}"
            self._metadata.append({
                "type": "best_practice", "title": bp["title"],
                "content": bp["content"], "text": text
            })

    def _lazy_load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')
                texts = [m["text"] for m in self._metadata]
                self._embeddings = model.encode(texts, convert_to_numpy=True)
                self._model = model
            except ImportError:
                self._model = False

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        self._lazy_load()
        if self._model is False:
            return self._keyword_search(query, top_k)
        query_emb = self._model.encode([query], convert_to_numpy=True)
        scores = np.dot(self._embeddings, query_emb.T).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            meta = self._metadata[idx]
            result = {k: v for k, v in meta.items() if k != "text"}
            result["score"] = round(float(scores[idx]), 4)
            results.append(result)
        return results

    def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        query_lower = query.lower()
        results = []
        for doc_id, doc in self.documents.items():
            score = 0
            for kw in doc["keywords"]:
                if kw.lower() in query_lower:
                    score += _rp["keyword_match_score"]
            if query_lower in doc["title"].lower():
                score += _rp["title_match_score"]
            if query_lower in doc["content"].lower():
                score += _rp["content_match_score"]
            if score > 0:
                results.append({"type": "regulatory", "id": doc_id, "title": doc["title"],
                                "content": doc["content"], "score": round(score, 2)})
        for bp in self.best_practices:
            score = 0
            if query_lower in bp["title"].lower():
                score += _rp["best_practice_title_score"]
            if query_lower in bp["content"].lower():
                score += _rp["best_practice_content_score"]
            for at in bp["applicable_permit_types"]:
                if at.lower() in query_lower:
                    score += _rp["best_practice_permit_type_score"]
            if score > 0:
                results.append({"type": "best_practice", "title": bp["title"],
                                "content": bp["content"], "score": round(score, 2)})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def query_permit_compliance(self, permit_type: str, zone_hazard_class: str,
                                 sensor_readings: Dict[str, float]) -> Dict:
        findings = {"permit_type": permit_type, "compliant": True, "violations": [], "recommendations": []}
        if permit_type == "Hot Work":
            lel = sensor_readings.get("LEL", 0)
            if lel > _rp["hot_work_lel_limit"]:
                findings["compliant"] = False
                findings["violations"].append(f"LEL at {lel:.1f}% exceeds {_rp['hot_work_lel_limit']}% safe limit for hot work")
                findings["recommendations"].append("Suspend hot work immediately. Purge area and verify LEL < 10% before resuming.")
            voc = sensor_readings.get("VOC", 0)
            if voc > _rp["hot_work_voc_limit"]:
                findings["compliant"] = False
                findings["violations"].append(f"VOC at {voc:.1f}ppm indicates flammable atmosphere")
                findings["recommendations"].append("Increase ventilation and re-test atmosphere before continuing hot work.")
        elif permit_type == "Confined Space Entry":
            o2 = sensor_readings.get("O2", 20.9)
            if o2 < _rp["o2_safe_lower"]:
                findings["compliant"] = False
                findings["violations"].append(f"O2 at {o2:.1f}% below {_rp['o2_safe_lower']}% safe entry threshold")
                findings["recommendations"].append("Stop entry. Ventilate confined space until O2 is restored above 19.5%.")
            if o2 > _rp["o2_safe_upper"]:
                findings["compliant"] = False
                findings["violations"].append(f"O2 at {o2:.1f}% above {_rp['o2_safe_upper']}% - oxygen-enriched atmosphere")
                findings["recommendations"].append("Stop entry. Investigate oxygen enrichment source.")
            h2s = sensor_readings.get("H2S", 0)
            if h2s > _rp["h2s_safe_limit"]:
                findings["compliant"] = False
                findings["violations"].append(f"H2S at {h2s:.1f}ppm exceeds safe limit for confined space")
                findings["recommendations"].append("H2S hazard detected. Respiratory protection required before entry.")
        elif permit_type == "Height Work":
            temp = sensor_readings.get("Temperature", 30)
            if temp > _rp["height_work_temp_limit"]:
                findings["compliant"] = False
                findings["violations"].append(f"Temperature at {temp:.0f}°C exceeds safe working limit for height work")
                findings["recommendations"].append("Postpone height work until temperature decreases to safe level.")
        regulatory_docs = self.search(f"{permit_type} safety compliance", top_k=2)
        findings["applicable_regulations"] = regulatory_docs
        findings["timestamp"] = datetime.now().isoformat()
        return findings

    def query_emergency_protocol(self, incident_type: str) -> Dict:
        protocols = get_emergency_templates()
        default_type = _rp["default_emergency_type"]
        protocol = dict(protocols.get(incident_type, protocols.get(default_type, {})))
        protocol["type"] = incident_type
        protocol["timestamp"] = datetime.now().isoformat()
        return protocol
