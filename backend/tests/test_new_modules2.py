import pytest
from alert_triage import AlertTriageEngine
from equipment_health import EquipmentHealthMonitor
from safety_observations import SafetyObservationSystem
from environmental_monitor import EnvironmentalMonitor


@pytest.fixture
def triage():
    return AlertTriageEngine()


@pytest.fixture
def eqmon():
    return EquipmentHealthMonitor()


@pytest.fixture
def obs():
    sys = SafetyObservationSystem()
    sys._observations = []
    sys._save()
    return sys


@pytest.fixture
def env():
    return EnvironmentalMonitor()


# --- Alert Triage ---

def test_alert_triage_returns_structure(triage):
    result = triage.triage({"id": "A1", "severity": "critical", "zone": "Z01"})
    assert "id" in result
    assert "urgency" in result
    assert "suggested_actions" in result
    assert "requires_immediate_attention" in result
    assert result["urgency"] in ("critical", "high", "elevated", "normal")


def test_alert_triage_critical_urgency(triage):
    result = triage.triage({"id": "A2", "severity": "critical", "zone": "Z01"})
    assert result["urgency"] == "critical"
    assert result["requires_immediate_attention"] is True


def test_alert_triage_normal_no_actions(triage):
    result = triage.triage({"id": "A3", "severity": "info", "zone": "Z08"})
    assert result["urgency"] == "normal"


def test_alert_triage_cache(triage):
    r1 = triage.triage({"id": "A4", "severity": "critical", "zone": "Z02"})
    r2 = triage.triage({"id": "A4", "severity": "critical", "zone": "Z02"})
    assert r1 is r2


def test_alert_triage_stats(triage):
    stats = triage.get_stats([
        {"severity": "critical"}, {"severity": "high"}, {"severity": "warning"}
    ])
    assert stats["total"] == 3
    assert stats["critical"] == 1
    assert stats["high"] == 1


# --- Equipment Health ---

def test_equipment_health_returns_list(eqmon):
    result = eqmon.assess_equipment()
    assert isinstance(result, list)
    assert len(result) > 0


def test_equipment_health_structure(eqmon):
    result = eqmon.assess_equipment({"sensors": {}, "active_permits": []})
    for eq in result:
        assert "id" in eq
        assert "name" in eq
        assert "health_score" in eq
        assert "failure_risk" in eq
        assert "remaining_useful_life_days" in eq
        assert "maintenance_priority" in eq
        assert "recommended_action" in eq


def test_equipment_health_scores_in_range(eqmon):
    result = eqmon.assess_equipment()
    for eq in result:
        assert 0 <= eq["health_score"] <= 100
        assert 0 <= eq["failure_risk"] <= 1
        assert eq["remaining_useful_life_days"] >= 1


def test_equipment_health_summary(eqmon):
    result = eqmon.assess_equipment()
    summary = eqmon.get_summary(result)
    assert "total" in summary
    assert "healthy" in summary
    assert "warning" in summary
    assert "critical" in summary
    assert "average_health" in summary
    assert summary["total"] == len(result)


def test_equipment_health_with_sensor_data(eqmon):
    result = eqmon.assess_equipment({
        "sensors": {"S1": {"zone_id": "Z01", "type": "Temperature", "value": 85, "status": "critical", "critical_threshold": 80}},
        "active_permits": [{"zone_id": "Z01", "risk_level": "high"}],
    })
    z01_eq = [e for e in result if e["zone_id"] == "Z01"]
    if z01_eq:
        assert z01_eq[0]["health_score"] < 100


# --- Safety Observations ---

def test_observation_submit(obs):
    result = obs.submit("unsafe_condition", "Z01", "Oil spill on walkway", "medium")
    assert result["id"].startswith("OBS-")
    assert result["type"] == "unsafe_condition"
    assert result["status"] == "open"
    assert result["severity"] == "medium"


def test_observation_review(obs):
    sub = obs.submit("near_miss", "Z02", "Falling object near crane", "high")
    result = obs.review(sub["id"], "Safety Officer", "Barricaded area, retrained crew", "closed")
    assert result["status"] == "closed"
    assert result["reviewed_by"] == "Safety Officer"


def test_observation_get_open(obs):
    obs.submit("unsafe_act", "Z03", "Worker without harness", "critical")
    obs.submit("housekeeping", "Z04", "Cluttered aisle", "low")
    open_obs = obs.get_open()
    assert len(open_obs) == 2


def test_observation_get_by_zone(obs):
    obs.submit("electrical_hazard", "Z05", "Exposed wiring", "high")
    zone_obs = obs.get_by_zone("Z05")
    assert len(zone_obs) == 1
    assert zone_obs[0]["zone_id"] == "Z05"


def test_observation_trends(obs):
    obs.submit("unsafe_condition", "Z01", "Test 1", "low")
    obs.submit("unsafe_condition", "Z01", "Test 2", "critical")
    trends = obs.get_trends()
    assert trends["total"] == 2
    assert trends["by_type"]["unsafe_condition"] == 2
    assert trends["open_count"] == 2


# --- Environmental ---

def test_environmental_returns_metrics(env):
    result = env.get_summary(sensors={"S1": {"type": "CO", "value": 10, "status": "normal"}})
    assert "total_metrics" in result
    assert result["total_metrics"] > 0
    assert "overall_status" in result
    assert "metrics" in result


def test_environmental_metric_structure(env):
    result = env.get_summary()
    for key, m in result["metrics"].items():
        assert "value" in m
        assert "unit" in m
        assert "status" in m
        assert m["status"] in ("normal", "warning", "critical")


def test_environmental_history(env):
    env.update_from_sensors({})
    history = env.get_history("co2", 10)
    assert len(history) <= 10
    if history:
        assert "timestamp" in history[0]
        assert "value" in history[0]


def test_environmental_compliance(env):
    result = env.get_compliance()
    assert "standards" in result
    for std in result["standards"]:
        assert "standard" in std
        assert "compliant" in std
        assert "total_applicable" in std


def test_environmental_from_sensors(env):
    result = env.get_summary(sensors={"S1": {"type": "CO", "value": 30}})
    assert result["total_metrics"] > 0
