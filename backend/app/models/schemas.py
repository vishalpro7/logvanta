from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    source: str = Field(..., min_length=1)
    raw_log: str = Field(..., min_length=1)


class FieldProfile(BaseModel):
    name: str
    inferred_type: str
    examples: List[str] = []
    confidence: float


class ProfileResult(BaseModel):
    detected_format: str
    fields: List[FieldProfile]
    confidence: float
    parser_hint: str


class NormalizedEvent(BaseModel):
    event_id: str
    source: str
    event_time: Optional[str] = None
    source_endpoint: Optional[str] = None
    destination_endpoint: Optional[str] = None
    action: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    raw: Dict[str, Any]
    ocsf_class: str = "Network Activity"
    mapping_confidence: float
    mapping_version: Optional[int] = None


class ValidationResult(BaseModel):
    valid: bool
    errors: List[str]
    warnings: List[str]


class ProcessResult(BaseModel):
    event_id: str
    profile: ProfileResult
    normalized: NormalizedEvent
    validation: ValidationResult
    traceability: Dict[str, Any]

class DriftResult(BaseModel):
    drift_detected: bool
    reason: str
    baseline_confidence: float
    current_confidence: float
    confidence_change: float
    missing_fields: List[str]
    new_fields: List[str]
    baseline_signature: List[str]
    current_signature: List[str]


class DriftRequest(BaseModel):
    source: str
    baseline_logs: List[str] = Field(..., min_length=1)
    current_log: str


class DriftResponse(BaseModel):
    source: str
    baseline: Dict[str, Any]
    current_profile: ProfileResult
    drift: DriftResult

class MappingVersionRequest(BaseModel):
    source: str
    mappings: List[Dict[str, Any]]
    confidence: float

class MappingVersionResponse(BaseModel):
    source: str
    version: int
    mappings: List[Dict[str, Any]]
    confidence: float
    status: str
    created_at: str
