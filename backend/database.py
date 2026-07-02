import json
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncGenerator

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

import constants as C

Base = declarative_base()


class PlantStateModel(Base):
    __tablename__ = "plant_states"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    time_step = Column(Integer)
    plant_name = Column(String(255))
    tenant_id = Column(String(100), default="plant_1")
    state_data = Column(Text)


class SensorReadingModel(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(String(100))
    type = Column(String(100))
    zone_id = Column(String(50))
    zone_name = Column(String(255))
    value = Column(Float)
    unit = Column(String(50))
    threshold = Column(Float)
    critical = Column(Float)
    status = Column(String(50))
    risk_score = Column(Float)
    tenant_id = Column(String(100), default="plant_1")
    timestamp = Column(DateTime, default=datetime.now)


class PermitModel(Base):
    __tablename__ = "permits"
    id = Column(String(100), primary_key=True)
    type = Column(String(100))
    zone_id = Column(String(50))
    zone_name = Column(String(255))
    description = Column(Text)
    status = Column(String(50))
    issued_at = Column(DateTime)
    expires_at = Column(DateTime)
    workers = Column(Text)
    risk_level = Column(String(50))
    conditions_check = Column(Boolean)
    tenant_id = Column(String(100), default="plant_1")
    timestamp = Column(DateTime, default=datetime.now)


class IncidentModel(Base):
    __tablename__ = "incidents"
    id = Column(String(100), primary_key=True)
    type = Column(String(100))
    status = Column(String(50))
    zone_id = Column(String(50))
    zone_name = Column(String(255))
    triggered_at = Column(DateTime)
    resolved_at = Column(DateTime, nullable=True)
    tenant_id = Column(String(100), default="plant_1")
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)


class ComplianceAuditModel(Base):
    __tablename__ = "compliance_audits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(100))
    overall_score = Column(Float)
    severity = Column(String(50))
    violations_count = Column(Integer)
    critical_findings_count = Column(Integer)
    tenant_id = Column(String(100), default="plant_1")
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)


class AlertModel(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(100))
    severity = Column(String(50))
    source = Column(String(100))
    message = Column(Text)
    zone_id = Column(String(50), nullable=True)
    zone_name = Column(String(255), nullable=True)
    tenant_id = Column(String(100), default="plant_1")
    timestamp = Column(DateTime, default=datetime.now)


class EmergencyEventModel(Base):
    __tablename__ = "emergency_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    emergency_id = Column(String(100))
    event_type = Column(String(100))
    event_data = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)


class ScenarioStateModel(Base):
    __tablename__ = "scenario_states"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(String(100))
    scenario_name = Column(String(255))
    state_data = Column(Text)
    is_active = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now)


_engine = None
_async_session_maker = None


async def init_db():
    global _engine, _async_session_maker
    database_url = C.DATABASE_URL
    _engine = create_async_engine(database_url, echo=False)
    _async_session_maker = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return _async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    global _async_session_maker
    if _async_session_maker is None:
        await init_db()
    async with _async_session_maker() as session:
        yield session


async def save_plant_state(state: Dict[str, Any]) -> None:
    global _async_session_maker
    if _async_session_maker is None:
        await init_db()
    async with _async_session_maker() as session:
        async with session.begin():
            model = PlantStateModel(
                timestamp=datetime.now(),
                time_step=state.get("time_step", 0),
                plant_name=state.get("plant_name", C.PLANT_NAME),
                state_data=json.dumps(state, default=str),
            )
            session.add(model)


async def save_sensor_reading(sensor: Dict[str, Any]) -> None:
    global _async_session_maker
    if _async_session_maker is None:
        await init_db()
    async with _async_session_maker() as session:
        async with session.begin():
            model = SensorReadingModel(
                sensor_id=sensor.get("id", ""),
                type=sensor.get("type", ""),
                zone_id=sensor.get("zone_id", ""),
                zone_name=sensor.get("zone_name", ""),
                value=sensor.get("value", 0.0),
                unit=sensor.get("unit", ""),
                threshold=sensor.get("threshold", 0.0),
                critical=sensor.get("critical", 0.0),
                status=sensor.get("status", ""),
                risk_score=sensor.get("risk_score", 0.0),
                timestamp=datetime.now(),
            )
            session.add(model)


async def save_permit(permit: Dict[str, Any]) -> None:
    global _async_session_maker
    if _async_session_maker is None:
        await init_db()
    async with _async_session_maker() as session:
        async with session.begin():
            issued = None
            expires = None
            try:
                issued = datetime.fromisoformat(permit["issued_at"]) if permit.get("issued_at") else None
            except (ValueError, TypeError):
                issued = None
            try:
                expires = datetime.fromisoformat(permit["expires_at"]) if permit.get("expires_at") else None
            except (ValueError, TypeError):
                expires = None
            model = PermitModel(
                id=permit.get("id", ""),
                type=permit.get("type", ""),
                zone_id=permit.get("zone_id", ""),
                zone_name=permit.get("zone_name", ""),
                description=permit.get("description", ""),
                status=permit.get("status", ""),
                issued_at=issued,
                expires_at=expires,
                workers=json.dumps(permit.get("workers", []), default=str),
                risk_level=permit.get("risk_level", ""),
                conditions_check=permit.get("conditions_check", False),
                timestamp=datetime.now(),
            )
            session.add(model)


async def save_incident(incident: Dict[str, Any]) -> None:
    global _async_session_maker
    if _async_session_maker is None:
        await init_db()
    async with _async_session_maker() as session:
        async with session.begin():
            triggered = None
            resolved = None
            try:
                triggered = datetime.fromisoformat(incident["triggered_at"]) if incident.get("triggered_at") else None
            except (ValueError, TypeError):
                triggered = None
            try:
                resolved = datetime.fromisoformat(incident["resolved_at"]) if incident.get("resolved_at") else None
            except (ValueError, TypeError):
                resolved = None
            model = IncidentModel(
                id=incident.get("id", ""),
                type=incident.get("type", ""),
                status=incident.get("status", ""),
                zone_id=incident.get("zone_id", ""),
                zone_name=incident.get("zone_name", ""),
                triggered_at=triggered,
                resolved_at=resolved,
                details=json.dumps(incident, default=str),
                timestamp=datetime.now(),
            )
            session.add(model)


async def save_compliance_audit(audit: Dict[str, Any]) -> None:
    global _async_session_maker
    if _async_session_maker is None:
        await init_db()
    async with _async_session_maker() as session:
        async with session.begin():
            model = ComplianceAuditModel(
                agent_id=audit.get("agent_id", ""),
                overall_score=audit.get(C.OVERALL_COMPLIANCE_SCORE_KEY, 0.0),
                severity=audit.get("severity", ""),
                violations_count=len(audit.get("violations", [])),
                critical_findings_count=len(audit.get("critical_findings", [])),
                details=json.dumps(audit, default=str),
                timestamp=datetime.now(),
            )
            session.add(model)


async def save_alert(alert: Dict[str, Any]) -> None:
    global _async_session_maker
    if _async_session_maker is None:
        await init_db()
    async with _async_session_maker() as session:
        async with session.begin():
            ts = None
            try:
                ts = datetime.fromisoformat(alert["timestamp"]) if alert.get("timestamp") else None
            except (ValueError, TypeError):
                ts = None
            model = AlertModel(
                alert_type=alert.get("type", ""),
                severity=alert.get("severity", ""),
                source=alert.get("source", ""),
                message=alert.get("message", ""),
                zone_id=alert.get("zone_id"),
                zone_name=alert.get("zone_name"),
                timestamp=ts or datetime.now(),
            )
            session.add(model)


async def save_emergency_event(event: Dict[str, Any]) -> None:
    global _async_session_maker
    if _async_session_maker is None:
        await init_db()
    async with _async_session_maker() as session:
        async with session.begin():
            model = EmergencyEventModel(
                emergency_id=event.get("id", ""),
                event_type=event.get("type", ""),
                event_data=json.dumps(event, default=str),
                timestamp=datetime.now(),
            )
            session.add(model)


async def save_scenario_state(scenario_id: str, scenario_name: str, state: Dict[str, Any], is_active: bool = False) -> None:
    global _async_session_maker
    if _async_session_maker is None:
        await init_db()
    async with _async_session_maker() as session:
        async with session.begin():
            from sqlalchemy import select, update
            if is_active:
                await session.execute(
                    update(ScenarioStateModel).where(ScenarioStateModel.is_active == True).values(is_active=False)
                )
            existing = await session.execute(
                select(ScenarioStateModel).where(
                    ScenarioStateModel.scenario_id == scenario_id,
                    ScenarioStateModel.is_active == True
                )
            )
            row = existing.scalar_one_or_none()
            if row:
                row.state_data = json.dumps(state, default=str)
                row.timestamp = datetime.now()
            else:
                session.add(ScenarioStateModel(
                    scenario_id=scenario_id,
                    scenario_name=scenario_name,
                    state_data=json.dumps(state, default=str),
                    is_active=is_active,
                    timestamp=datetime.now(),
                ))


async def get_active_scenario_state() -> Optional[Dict[str, Any]]:
    global _async_session_maker
    if _async_session_maker is None:
        return None
    async with _async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ScenarioStateModel).where(ScenarioStateModel.is_active == True).order_by(ScenarioStateModel.timestamp.desc()).limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return json.loads(row.state_data) if row.state_data else None


async def get_recent_plant_states(limit: int = 10) -> List[Dict[str, Any]]:
    global _async_session_maker
    if _async_session_maker is None:
        return []
    async with _async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(PlantStateModel).order_by(PlantStateModel.id.desc()).limit(limit)
        )
        rows = result.scalars().all()
        states = []
        for row in reversed(rows):
            try:
                states.append(json.loads(row.state_data))
            except (json.JSONDecodeError, TypeError):
                states.append({"time_step": row.time_step, "plant_name": row.plant_name})
        return states


async def get_incident_history(limit: int = 50) -> List[Dict[str, Any]]:
    global _async_session_maker
    if _async_session_maker is None:
        return []
    async with _async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(IncidentModel).order_by(IncidentModel.timestamp.desc()).limit(limit)
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "type": r.type,
                "status": r.status,
                "zone_id": r.zone_id,
                "zone_name": r.zone_name,
                "triggered_at": r.triggered_at.isoformat() if r.triggered_at else None,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                "details": json.loads(r.details) if r.details else {},
            }
            for r in rows
        ]


async def get_compliance_history(limit: int = 50) -> List[Dict[str, Any]]:
    global _async_session_maker
    if _async_session_maker is None:
        return []
    async with _async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ComplianceAuditModel).order_by(ComplianceAuditModel.timestamp.desc()).limit(limit)
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "agent_id": r.agent_id,
                "overall_score": r.overall_score,
                "severity": r.severity,
                "violations_count": r.violations_count,
                "critical_findings_count": r.critical_findings_count,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in rows
        ]
