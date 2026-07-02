import pytest
from root_cause_analyzer import RootCauseAnalyzer
from digital_twin import DigitalTwinAggregator
from personnel_tracker import PersonnelTracker


@pytest.fixture
def rca():
    return RootCauseAnalyzer()


@pytest.fixture
def dt():
    return DigitalTwinAggregator()


@pytest.fixture
def pt():
    return PersonnelTracker()


# --- Root Cause Analyzer ---

def test_rca_returns_expected_structure(rca):
    result = rca.analyze(plant_state={"sensors": {}, "active_permits": []})
    assert "incident" in result
    assert "root_causes" in result
    assert "contributing_factors" in result
    assert "causal_chain" in result
    assert "recommendations" in result
    assert "regulatory_context" in result


def test_rca_detects_sensor_anomaly(rca):
    result = rca.analyze(incident_type="gas_leak", plant_state={
        "sensors": {
            "S01": {"zone_id": "Coke Oven Battery", "type": "LEL", "value": 45, "critical_threshold": 25, "status": "critical"},
        },
        "active_permits": [],
    })
    assert any(c["type"] == "sensor_anomaly" for c in result["causal_chain"])
    assert len(result["root_causes"]) > 0


def test_rca_no_data_returns_graceful(rca):
    result = rca.analyze(incident_type="nonexistent")
    assert result["incident"] is None


# --- Digital Twin ---

def test_digital_twin_returns_all_sections(dt):
    result = dt.build_dashboard()
    assert "kpi" in result
    assert "sensors" in result
    assert "permits" in result
    assert "zones" in result
    assert "alerts" in result
    assert "health_index" in result
    assert "status_summary" in result
    assert "trend_direction" in result


def test_digital_twin_empty_state(dt):
    result = dt.build_dashboard()
    assert result["kpi"]["sensor_health_score"] == 0
    assert result["kpi"]["overall_risk"] == 0
    assert result["sensors"]["total"] == 0


def test_digital_twin_with_real_plant_state(dt):
    result = dt.build_dashboard(
        plant_state={
            "sensors": {"S1": {"status": "normal"}, "S2": {"status": "warning"}},
            "active_permits": [{"risk_level": "high"}, {"risk_level": "low"}],
            "zone_risk_scores": {"Z01": 0.9, "Z02": 0.2},
        },
        risk_result={"risk_score": 0.65, "severity": "high"},
        health_index={"overall": 72, "label": "Good"},
        alerts=[{"severity": "critical"}, {"severity": "warning"}],
    )
    assert result["sensors"]["total"] == 2
    assert result["sensors"]["health_score"] == 75
    assert result["kpi"]["overall_risk"] == 0.65
    assert result["alerts"]["critical"] == 1
    assert result["alerts"]["total"] == 2
    assert result["health_index"]["overall"] == 72


def test_digital_twin_trend_insufficient_data(dt):
    assert dt._trend_direction([]) == "insufficient_data"
    assert dt._trend_direction([1, 2]) == "insufficient_data"


def test_digital_twin_trend_increasing(dt):
    assert dt._trend_direction([1, 2, 3, 4, 10]) == "increasing"


def test_digital_twin_trend_decreasing(dt):
    assert dt._trend_direction([10, 9, 8, 7, 1]) == "decreasing"


def test_digital_twin_trend_stable(dt):
    assert dt._trend_direction([5, 5, 5, 5, 5]) == "stable"


# --- Personnel Tracker ---

def test_personnel_tracker_initial_state(pt):
    locs = pt.get_all_locations()
    assert len(locs) == pt.get_personnel_count()
    for p in locs:
        assert "name" in p
        assert "zone_id" in p
        assert "mustered" in p


def test_personnel_tracker_mustering(pt):
    result = pt.trigger_mustering("Z01")
    assert result["total_personnel"] > 0
    assert "mustered" in result
    assert "missing" in result
    assert "mustered_pct" in result
    assert "in_danger_zone" in result


def test_personnel_tracker_mustering_marks_all(pt):
    result = pt.trigger_mustering("NONEXISTENT")
    assert result["missing"] == 0
    assert result["mustered"] == result["total_personnel"]


def test_personnel_tracker_zone_occupancy(pt):
    zones = pt.get_zone_occupancy()
    assert len(zones) > 0
    for z in zones:
        assert "zone_id" in z
        assert "count" in z
        assert "personnel" in z


def test_personnel_tracker_hazard_exposure(pt):
    report = pt.get_hazard_exposure_report()
    assert "workers_with_exposure" in report
    assert "details" in report


def test_personnel_tracker_update_location(pt):
    pt.update_location(pt.workers[0], "Z01")
    locs = pt.get_all_locations()
    target = next(p for p in locs if p["name"] == pt.workers[0])
    assert target["zone_id"] == "Z01"
