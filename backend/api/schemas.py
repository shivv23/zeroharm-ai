from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PermitComplianceRequest(BaseModel):
    permit_type: str = Field(default="Hot Work", max_length=100)
    zone_hazard_class: str = Field(default="High", max_length=50)
    sensor_readings: Dict[str, float] = Field(default_factory=dict)


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=3, ge=1, le=50)


class EmergencyTriggerRequest(BaseModel):
    type: str = Field(default="gas_leak", max_length=100)
    context: Dict[str, Any] = Field(default_factory=dict)


class EmergencyResolveRequest(BaseModel):
    notes: Optional[str] = Field(default="", max_length=1000)


class WhatIfApplyRequest(BaseModel):
    scenario_id: str = Field(..., min_length=1, max_length=100)


class WhatIfCustomRequest(BaseModel):
    changes: Dict[str, Any] = Field(default_factory=dict)
    permits_to_add: List[Dict[str, Any]] = Field(default_factory=list)
    name: str = Field(default="Custom Scenario", max_length=200)
