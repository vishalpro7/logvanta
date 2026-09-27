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
