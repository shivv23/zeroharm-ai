from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=4, max_length=200)
    role: str = Field(default="viewer", pattern=r"^(admin|safety_officer|operator|viewer)$")
    tenant_id: str = Field(default="plant_1", max_length=100)
    name: Optional[str] = Field(default=None, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    username: str
    role: str
    tenant_id: str
    name: str


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


class SensorChange(BaseModel):
    value: Optional[float] = None
    status: Optional[str] = None
    risk_score: Optional[float] = Field(default=None, ge=0, le=1)


class PermitChange(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = Field(default=None, max_length=100)
    zone_id: Optional[str] = Field(default=None, max_length=20)
    zone_name: Optional[str] = Field(default=None, max_length=100)
    risk_level: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=20)
    workers: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None


class WhatIfCustomRequest(BaseModel):
    changes: Dict[str, SensorChange] = Field(default_factory=dict)
    permits_to_add: List[PermitChange] = Field(default_factory=list)
    name: str = Field(default="Custom Scenario", max_length=200)

    @field_validator("changes")
    @classmethod
    def validate_changes_keys(cls, v):
        for key in v:
            if not isinstance(key, str) or len(key) > 100:
                raise ValueError(f"Invalid sensor key: {key}")
        return v


class CreateInvestigationRequest(BaseModel):
    incident_data: Dict[str, Any] = Field(default_factory=dict)


class AddFindingRequest(BaseModel):
    finding: Dict[str, Any]


class CreateCapaRequest(BaseModel):
    finding: Dict[str, Any]
    action_type: str = Field(default="corrective", max_length=50)
    description: str = Field(default="", max_length=2000)
    owner: str = Field(default="", max_length=200)
    deadline: str = Field(default="", max_length=50)


class UpdateCapaStatusRequest(BaseModel):
    status: str = Field(..., max_length=50)


class VisionDetectRequest(BaseModel):
    image_bytes: Optional[str] = None
    base64: Optional[str] = None


class VisionDetectResponse(BaseModel):
    detections: List[Dict[str, Any]] = []
    ppe_counts: Optional[Dict[str, int]] = None
    zone_violations: Optional[List[Dict[str, Any]]] = None
    processed_at: str = ""


class VisionRTSPStartRequest(BaseModel):
    rtsp_url: str = Field(..., min_length=1, max_length=500)


class VisionRTSPStopRequest(BaseModel):
    rtsp_url: str = Field(..., min_length=1, max_length=500)


class VisionStatusResponse(BaseModel):
    enabled: bool = False
    model_loaded: bool = False
    ultralytics_available: bool = False
    opencv_available: bool = False
    active_streams: List[str] = []
    model_path: str = ""


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class ObservationSubmitRequest(BaseModel):
    observation_type: str = Field(..., min_length=1, max_length=50)
    zone_id: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=1000)
    severity: str = "medium"
    submitted_by: str = "Anonymous"
    location_detail: str = ""


class ObservationReviewRequest(BaseModel):
    obs_id: str = Field(..., min_length=1)
    reviewer: str = Field(..., min_length=1)
    resolution: str = Field(..., min_length=1)
    status: str = "closed"


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=4)


class ResetPasswordRequest(BaseModel):
    username: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=4)


class AuditLogQuery(BaseModel):
    action: Optional[str] = None
    resource: Optional[str] = None
    username: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class BulkExportRequest(BaseModel):
    resources: list[str] = Field(default_factory=lambda: ["sensors", "permits", "alerts", "incidents"])
    format: str = Field(default="csv", pattern=r"^(csv|json)$")
