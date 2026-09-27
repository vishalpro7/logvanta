from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    IngestRequest,
    ProcessResult,
    ProfileResult,
    NormalizedEvent,
    ValidationResult,
    DriftRequest,
    DriftResponse,
    MappingVersionRequest,
    MappingVersionResponse,
)
from app.drift.service import build_baseline, compare_with_baseline
from app.ingestion.service import ingest
from app.profiling.service import profile_log
from app.parsing.service import parse
from app.mapping.service import map_to_ocsf
from app.validation.service import validate
from app.traceability.service import build_trace
from app.adaptation.service import generate_candidates
from app.adaptation.registry import mapping_registry

router = APIRouter(prefix="/api/v1", tags=["LOGVANTA Pipeline"])


@router.post("/process", response_model=ProcessResult)
def process_log(request: IngestRequest):
    record = ingest(request.source, request.raw_log)

    detected_format, fields, confidence, parser_hint = profile_log(request.raw_log)
    try:
        parsed = parse(request.raw_log, detected_format)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Parsing failed: {exc}")

    normalized = map_to_ocsf(parsed, request.source, record["event_id"])
    validation = validate(normalized)
    trace = build_trace(record["event_id"], request.source, request.raw_log, normalized)

    return {
        "event_id": record["event_id"],
        "profile": {
            "detected_format": detected_format,
            "fields": fields,
            "confidence": confidence,
            "parser_hint": parser_hint,
        },
        "normalized": normalized,
        "validation": validation,
        "traceability": trace,
    }

@router.post("/drift/check", response_model=DriftResponse)
def check_drift(request: DriftRequest):

    baseline_profiles = []

    for raw_log in request.baseline_logs:
        detected_format, fields, confidence, parser_hint = profile_log(
            raw_log
        )

        baseline_profiles.append({
            "detected_format": detected_format,
            "fields": fields,
            "confidence": confidence,
            "parser_hint": parser_hint,
        })

    baseline = build_baseline(baseline_profiles)

    detected_format, fields, confidence, parser_hint = profile_log(
        request.current_log
    )

    current_profile = {
        "detected_format": detected_format,
        "fields": fields,
        "confidence": confidence,
        "parser_hint": parser_hint,
    }

    drift = compare_with_baseline(
        baseline,
        current_profile,
    )

    return {
        "source": request.source,
        "baseline": baseline,
        "current_profile": current_profile,
        "drift": drift,
    }

@router.post("/adaptation/analyze")
def analyze_new_format(payload: dict):

    parsed_fields = payload.get("parsed_fields", {})

    candidates = generate_candidates(
        parsed_fields
    )

    return {
        "status": "analysis_complete",
        "candidate_mappings": candidates,
    }

@router.post(
    "/adaptation/version",
    response_model=MappingVersionResponse
)
def create_mapping_version(request: MappingVersionRequest):

    version = mapping_registry.create_version(
        source=request.source,
        mappings=request.mappings,
        confidence=request.confidence,
    )

    return version

@router.get(
    "/adaptation/{source}/versions"
)
def get_mapping_versions(source: str):

    return {
        "source": source,
        "versions": mapping_registry.get_versions(source),
    }

@router.post(
    "/adaptation/{source}/activate/{version}"
)
def activate_mapping_version(
    source: str,
    version: int,
):

    try:
        activated = mapping_registry.activate_version(
            source,
            version,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return activated
