import pytest
from chat_assistant import ChatAssistant
from cost_of_safety import compute_cost_of_safety
import config_loader


@pytest.fixture
def chat():
    return ChatAssistant()


@pytest.mark.asyncio
async def test_chat_risk_intent(chat):
    result = await chat.answer("what is the risk level in the blast furnace area", plant_state={"zone_risk_scores": {"Z02": 0.85}})
    assert result["intent"] == "risk"
    assert "Z02" in result["answer"]


@pytest.mark.asyncio
async def test_chat_alerts_intent(chat):
    result = await chat.answer("show me critical alerts", alerts=[{"severity": "critical"}, {"severity": "warning"}])
    assert result["intent"] == "alerts"
    assert result["data"]["critical"] == 1
    assert result["data"]["total"] == 2


@pytest.mark.asyncio
async def test_chat_permits_intent(chat):
    result = await chat.answer("how many permits are active?",
                               plant_state={"active_permits": [{"id": "P1"}, {"id": "P2"}]})
    assert result["intent"] == "permits"
    assert "2" in result["answer"]


@pytest.mark.asyncio
async def test_chat_compliance_intent(chat):
    result = await chat.answer("what is our compliance score",
                               compliance_result={"overall_compliance_score": 87})
    assert result["intent"] == "compliance"
    assert "87" in result["answer"]


@pytest.mark.asyncio
async def test_chat_health_intent(chat):
    result = await chat.answer("how is plant health",
                               health_index={"label": "Good", "overall": 72})
    assert result["intent"] == "health"
    assert "Good" in result["answer"]


@pytest.mark.asyncio
async def test_chat_general_fallback(chat):
    result = await chat.answer("hello world")
    assert result["intent"] == "general"


@pytest.mark.asyncio
async def test_chat_forecast_intent(chat):
    result = await chat.answer("what does the forecast show", risk_trend=[1, 2, 3])
    assert result["intent"] == "forecast"
    assert 3 == result["data"]["readings"]


def test_cost_of_safety_with_alerts():
    result = compute_cost_of_safety(
        alerts=[{"severity": "critical"}, {"severity": "warning"}],
        active_permits=[{"risk_level": "high"}, {"risk_level": "low"}]
    )
    assert result["total_incidents"] >= 0
    assert result["ongoing_risk_cost"] == 10000 + 5000


def test_cost_of_safety_returns_expected_keys():
    result = compute_cost_of_safety()
    assert "total_cost" in result
    assert "total_fines" in result
    assert "total_incident_cost" in result
    assert "ongoing_risk_cost" in result
    assert "severity_breakdown" in result
    assert "zone_costs" in result
    assert "yearly_costs" in result
    assert "total_incidents" in result
    assert "cost_per_incident_avg" in result
    assert "prevention_savings_estimate" in result


def test_cost_of_safety_incident_data_loaded():
    result = compute_cost_of_safety()
    assert result["total_incidents"] > 0
    assert isinstance(result["severity_breakdown"], dict)
    assert isinstance(result["zone_costs"], dict)
