from typing import Any

from sqlalchemy.orm import Session
from app.adaptation.registry import mapping_registry
from app.adaptation.service import generate_candidates
from app.drift.service import build_baseline, compare_with_baseline
from app.parsing.service import parse
from app.profiling.service import profile_log


def _profile(raw_log: str) -> dict[str, Any]:
    detected_format, fields, confidence, parser_hint = profile_log(raw_log)

    return {
        "detected_format": detected_format,
        "fields": fields,
        "confidence": confidence,
        "parser_hint": parser_hint,
    }


def run_adaptation_workflow(
    db: Session,
    source: str,
    baseline_logs: list[str],
    current_log: str,
) -> dict[str, Any]:
    """
    Detect format drift and create a candidate mapping version
    when drift is detected.

    Candidate mappings are NEVER activated automatically.
    """

    baseline_profiles = [
        _profile(raw)
        for raw in baseline_logs
    ]

    baseline = build_baseline(baseline_profiles)

    current_profile = _profile(current_log)

    drift = compare_with_baseline(
        baseline,
        current_profile,
    )

    result = {
        "source": source,
        "status": "no_drift",
        "baseline": baseline,
        "current_profile": current_profile,
        "drift": drift,
        "candidate_version": None,
        "candidate_mappings": [],
    }

    if not drift["drift_detected"]:
        return result

    parsed = parse(
        current_log,
        current_profile["detected_format"],
    )

    candidates = generate_candidates(parsed)

    mapping_candidates = []
    confidence_values = []

    for candidate in candidates:

        target = candidate.get("candidate_mapping")
        decision = candidate.get("decision")

        if target and decision != "rejected":

            mapping_candidates.append({
                "field": candidate["new_field"],
                "target": target,
                "confidence": candidate["confidence"],
                "matched_known_field": candidate["matched_known_field"],
                "name_similarity": candidate["name_similarity"],
                "type_bonus": candidate["type_bonus"],
                "decision": decision,
            })

            confidence_values.append(
                float(candidate["confidence"])
            )

    candidate_confidence = (
        round(
            sum(confidence_values)
            / len(confidence_values),
            3,
        )
        if confidence_values
        else 0.0
    )

    version = mapping_registry.create_version(
    db=db,
    source=source,
    mappings=mapping_candidates,
    confidence=candidate_confidence,
    status="candidate",
)

    result.update({
        "status": "candidate_created",
        "candidate_version": version,
        "candidate_mappings": mapping_candidates,
    })

    return result