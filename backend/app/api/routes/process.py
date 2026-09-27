from fastapi import APIRouter, HTTPException

from app.models.schemas import IngestRequest, ProcessResult, ProfileResult, NormalizedEvent, ValidationResult
from app.ingestion.service import ingest
from app.profiling.service import profile_log
from app.parsing.service import parse
from app.mapping.service import map_to_ocsf
from app.validation.service import validate
from app.traceability.service import build_trace

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
