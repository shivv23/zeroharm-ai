"""Tests for ZeroHarm AI agent components."""

import copy
import pytest
from orchestrator.incident_pattern_intelligence import IncidentPatternIntelligence


class TestSyntheticDataGenerator:
    def test_generates_sensors(self, generator):
        state = generator.step()
        sensors = state.get("sensors", {})
        assert len(sensors) > 0, "Should generate at least one sensor"

    def test_generates_permits(self, generator):
        state = generator.step()
        permits = state.get("active_permits", [])
        assert isinstance(permits, list), "Permits should be a list"


class TestKnowledgeGraph:
    def test_has_nodes(self, kg_builder, zones):
        for z in zones[:3]:
            kg_builder.add_zone(z["id"], z["name"], z.get("hazard_class", "High"), z.get("x", 0), z.get("y", 0))
        assert kg_builder.graph.number_of_nodes() > 0, "Graph should have nodes"

    def test_risk_paths_exist(self, kg_builder, zones):
        for z in zones[:3]:
            kg_builder.add_zone(z["id"], z["name"], z.get("hazard_class", "High"), z.get("x", 0), z.get("y", 0))
        findings = kg_builder.query_compound_risk_paths("Z01", ["Confined Space Entry"], {"O2": 18.2})
        assert isinstance(findings, list), "Risk findings should be a list"


class TestCompoundRiskEngine:
    def test_returns_risk_score(self, risk_engine, plant_state):
        result = risk_engine.run(copy.deepcopy(plant_state))
        assert "risk_score" in result, "Result should contain risk_score"
        assert isinstance(result["risk_score"], (int, float)), "risk_score should be numeric"
        assert 0.0 <= result["risk_score"] <= 1.0, "risk_score should be between 0 and 1"

    def test_returns_severity(self, risk_engine, plant_state):
        result = risk_engine.run(copy.deepcopy(plant_state))
        assert "severity" in result, "Result should contain severity"
        assert result["severity"] in ("normal", "warning", "high", "critical"), f"Unexpected severity: {result['severity']}"


class TestEmergencyOrchestrator:
    def test_triggers_gas_leak(self, emergency_orchestrator):
        result = emergency_orchestrator.trigger("gas_leak", {"zone_id": "Z01", "description": "Test gas leak"})
        assert result.get("status") == "active", "Emergency should be active"
        assert "id" in result, "Should generate emergency ID"
        assert len(emergency_orchestrator.active_emergencies) > 0, "Should have active emergencies"


class TestIncidentPatternIntelligence:
    def test_discovers_patterns(self):
        ip = IncidentPatternIntelligence()
        assert len(ip.patterns) > 0, "Should discover patterns from incident records"

    def test_returns_recommendations(self):
        ip = IncidentPatternIntelligence()
        recs = ip.get_prevention_recommendations("Z01", "Hot Work")
        assert isinstance(recs, list), "Recommendations should be a list"


class TestSimulationCycle:
    def test_full_cycle(self, generator, risk_engine):
        for _ in range(20):
            state = generator.step()
            risk_engine.run(copy.deepcopy(state))
        assert True, "20 simulation cycles completed without error"
