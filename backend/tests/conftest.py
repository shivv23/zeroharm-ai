import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data.synthetic_data_generator import SyntheticDataGenerator
from agents.compound_risk_engine import CompoundRiskDetectionEngine
from orchestrator.emergency_response import EmergencyResponseOrchestrator
from orchestrator.incident_pattern_intelligence import IncidentPatternIntelligence
from knowledge_graph.kg_builder import IndustrialKnowledgeGraph
from config_loader import get_zones


@pytest.fixture
def generator():
    return SyntheticDataGenerator()


@pytest.fixture
def risk_engine():
    return CompoundRiskDetectionEngine()


@pytest.fixture
def emergency_orchestrator():
    return EmergencyResponseOrchestrator()


@pytest.fixture
def plant_state(generator):
    return generator.step()


@pytest.fixture
def kg_builder():
    return IndustrialKnowledgeGraph()


@pytest.fixture
def zones():
    return get_zones()
