#!/usr/bin/env python3
"""Quick verification script to test all agent components."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

def test_data_generator():
    print("Testing Synthetic Data Generator...")
    from data.synthetic_data_generator import SyntheticDataGenerator
    gen = SyntheticDataGenerator()
    state = gen.step()
    assert len(state["sensors"]) >= 80, f"Expected 80+ sensors, got {len(state['sensors'])}"
    assert "zone_risk_scores" in state, "Missing zone_risk_scores"
    assert "compound_risks" in state, "Missing compound_risks"
    print(f"  PASS: {len(state['sensors'])} sensors, {len(state['active_permits'])} permits")
    return state

def test_knowledge_graph():
    print("Testing Knowledge Graph...")
    from knowledge_graph.kg_builder import IndustrialKnowledgeGraph
    kg = IndustrialKnowledgeGraph()
    from config_loader import get_zones
    zones = get_zones()
    for z in zones[:3]:
        kg.add_zone(z["id"], z["name"], z["hazard_class"], z["x"], z["y"])
    findings = kg.query_compound_risk_paths("Z01", ["Confined Space Entry"], {"O2": 18.2})
    assert len(findings) > 0, "Expected compound risk findings"
    print(f"  PASS: {kg.graph.number_of_nodes()} nodes, {len(findings)} risk paths found")
    return kg

def test_compound_risk_engine():
    print("Testing Compound Risk Detection Engine...")
    from agents.compound_risk_engine import CompoundRiskDetectionEngine
    from data.synthetic_data_generator import SyntheticDataGenerator
    engine = CompoundRiskDetectionEngine()
    gen = SyntheticDataGenerator()
    state = gen.step()
    result = engine.run(state)
    assert "risk_score" in result, "Missing risk_score"
    assert "severity" in result, "Missing severity"
    assert "alerts" in result, "Missing alerts"
    assert "sensor_analysis" in result, "Missing sensor_analysis"
    assert "permit_analysis" in result, "Missing permit_analysis"
    assert "maintenance_analysis" in result, "Missing maintenance_analysis"
    print(f"  PASS: risk_score={result['risk_score']}, severity={result['severity']}, alerts={len(result['alerts'])}")
    return result

def test_rag_pipeline():
    print("Testing RAG Pipeline...")
    from rag.rag_pipeline import RAGPipeline
    rag = RAGPipeline()
    results = rag.search("confined space oxygen", top_k=2)
    assert len(results) > 0, "Expected search results"
    print(f"  PASS: {len(results)} results for 'confined space oxygen'")
    compliance = rag.query_permit_compliance("Confined Space Entry", "High", {"O2": 18.1, "H2S": 2.0})
    assert "compliant" in compliance, "Missing compliant status"
    assert "violations" in compliance, "Missing violations"
    print(f"  PASS: Permit compliance check -> compliant={compliance['compliant']}, violations={len(compliance['violations'])}")
    return rag

def test_emergency_orchestrator():
    print("Testing Emergency Response Orchestrator...")
    from orchestrator.emergency_response import EmergencyResponseOrchestrator
    em = EmergencyResponseOrchestrator()
    context = {
        "zone_id": "Z01",
        "zone_name": "Coke Oven Battery",
        "sensor_snapshot": {"S1": {"type": "LEL", "value": 25.0, "unit": "%LEL", "status": "critical"}},
        "permit_snapshot": [{"id": "PTW-001", "type": "Hot Work", "risk_level": "Critical"}],
        "personnel_in_zone": ["Rajesh Kumar", "Amit Singh"],
    }
    response = em.trigger("gas_leak", context)
    assert "id" in response, "Missing emergency ID"
    assert response["status"] == "active", "Should be active"
    assert len(response["alerts_dispatched"]) > 0, "Expected alerts"
    assert "incident_report" in response, "Expected incident report"
    print(f"  PASS: {response['id']} - {response['label']} - {len(response['alerts_dispatched'])} alerts dispatched")
    return em

def test_incident_patterns():
    print("Testing Incident Pattern Intelligence...")
    from orchestrator.incident_pattern_intelligence import IncidentPatternIntelligence
    ip = IncidentPatternIntelligence()
    patterns = ip.get_all_patterns()
    stats = ip.get_statistics()
    assert len(patterns) > 0, "Expected patterns"
    assert stats["total_incidents"] == 8, "Expected 8 incidents"
    print(f"  PASS: {len(patterns)} patterns, {stats['total_incidents']} incidents analyzed")
    return ip

def test_full_simulation_cycle():
    print("Testing Full Simulation Cycle...")
    from data.synthetic_data_generator import SyntheticDataGenerator
    from agents.compound_risk_engine import CompoundRiskDetectionEngine
    gen = SyntheticDataGenerator()
    engine = CompoundRiskDetectionEngine()
    for i in range(20):
        state = gen.step()
        result = engine.run(state)
        assert result["risk_score"] is not None, f"Risk score None at step {i}"
    print(f"  PASS: 20 simulation cycles completed successfully")
    return True

def test_compound_event():
    print("Testing Compound Event Scenario...")
    from data.synthetic_data_generator import SyntheticDataGenerator
    from agents.compound_risk_engine import CompoundRiskDetectionEngine
    gen = SyntheticDataGenerator()
    engine = CompoundRiskDetectionEngine()
    compound_found = False
    for i in range(100):
        state = gen.step()
        if state.get("compound_risks") and len(state["compound_risks"]) > 0:
            compound_found = True
            print(f"  Compound risk detected at step {i}: {state['compound_risks'][0]['recommendation'][:60]}...")
            break
    assert compound_found, "Expected at least one compound risk event within 100 steps"
    print(f"  PASS: Compound risk detection triggered within simulation")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("  ZeroHarm AI - Agent Component Tests")
    print("=" * 60)
    print()
    tests = [
        ("Data Generator", test_data_generator),
        ("Knowledge Graph", test_knowledge_graph),
        ("Compound Risk Engine", test_compound_risk_engine),
        ("RAG Pipeline", test_rag_pipeline),
        ("Emergency Orchestrator", test_emergency_orchestrator),
        ("Incident Patterns", test_incident_patterns),
        ("Full Simulation Cycle", test_full_simulation_cycle),
        ("Compound Event Simulation", test_compound_event),
    ]
    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
            print()
        except Exception as e:
            print(f"  FAIL: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    sys.exit(1 if failed > 0 else 0)
