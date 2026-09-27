import re
from difflib import SequenceMatcher
from typing import Any


KNOWN_FIELD_MAPPINGS = {
    "src_ip": "source_endpoint",
    "source_ip": "source_endpoint",
    "source_address": "source_endpoint",

    "dst_ip": "destination_endpoint",
    "destination_ip": "destination_endpoint",
    "destination_address": "destination_endpoint",

    "action": "action",
    "decision": "action",

    "severity": "severity",
    "event_time": "event_time",
    "timestamp": "event_time",
}


def normalize_name(name: str) -> str:
    """
    Converts different naming styles into a comparable form.

    sourceAddress → sourceaddress
    source_address → sourceaddress
    src_ip → srcip
    """

    return re.sub(r"[^a-z0-9]", "", name.lower())


def is_ipv4(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    pattern = (
        r"^(25[0-5]|2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)$"
    )

    return bool(re.match(pattern, value))


def name_similarity(
    new_field: str,
    known_field: str,
) -> float:

    return SequenceMatcher(
        None,
        normalize_name(new_field),
        normalize_name(known_field),
    ).ratio()


def generate_candidates(
    parsed_fields: dict[str, Any],
) -> list[dict[str, Any]]:

    candidates = []

    for new_field, value in parsed_fields.items():

        best_match = None
        best_score = 0.0

        for known_field, target in KNOWN_FIELD_MAPPINGS.items():

            score = name_similarity(
                new_field,
                known_field,
            )

            if score > best_score:
                best_score = score
                best_match = {
                    "known_field": known_field,
                    "target": target,
                }

        # Value-type evidence
        type_bonus = 0.0

        if is_ipv4(value):
            if best_match and best_match["target"] in {
                "source_endpoint",
                "destination_endpoint",
            }:
                type_bonus = 0.20

        final_score = min(
            1.0,
            best_score + type_bonus,
        )

        if final_score >= 0.75:
            decision = "high_confidence"
        elif final_score >= 0.55:
            decision = "review_required"
        else:
            decision = "rejected"

        candidates.append({
            "new_field": new_field,
            "value": value,
            "candidate_mapping": (
                best_match["target"]
                if best_match
                else None
            ),
            "matched_known_field": (
                best_match["known_field"]
                if best_match
                else None
            ),
            "name_similarity": round(
                best_score,
                3,
            ),
            "type_bonus": type_bonus,
            "confidence": round(
                final_score,
                3,
            ),
            "decision": decision,
        })

    return candidates