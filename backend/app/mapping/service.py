from typing import Any

from app.adaptation.registry import mapping_registry
from sqlalchemy.orm import Session


ALIASES = {
    "src": "source_endpoint",
    "src_ip": "source_endpoint",
    "source_ip": "source_endpoint",
    "source": "source_endpoint",

    "dst": "destination_endpoint",
    "dst_ip": "destination_endpoint",
    "dest_ip": "destination_endpoint",
    "destination_ip": "destination_endpoint",
    "destination": "destination_endpoint",

    "action": "action",
    "act": "action",

    "severity": "severity",
    "level": "severity",

    "time": "event_time",
    "timestamp": "event_time",
    "ts": "event_time",

    "message": "message",
    "msg": "message",
}


def _get_active_aliases(
    db: Session,
    source: str,
) -> tuple[dict[str, str], int | None]:

    active_version = mapping_registry.get_active_version(
    db,
    source,
)

    if not active_version:
        return ALIASES, None

    learned_aliases = {}

    for mapping in active_version.get("mappings", []):

        field = (
            mapping.get("field")
            or mapping.get("new_field")
        )

        target = (
            mapping.get("target")
            or mapping.get("candidate_mapping")
        )

        if field and target:
            learned_aliases[
                str(field).lower()
            ] = str(target)

    aliases = {
        **ALIASES,
        **learned_aliases,
    }

    return aliases, active_version["version"]


def map_to_ocsf(
    db: Session,
    parsed: dict[str, Any],
    source: str,
    event_id: str,
):

    aliases, mapping_version = _get_active_aliases(
    db,
    source,
)

    normalized = {
        "event_id": event_id,
        "source": source,
        "raw": parsed,
        "ocsf_class": "Network Activity",
        "mapping_confidence": 0.0,
    }

    if mapping_version is not None:
        normalized["mapping_version"] = mapping_version

    mapped = 0
    total = len(parsed) or 1

    for key, value in parsed.items():

        target = aliases.get(key.lower())

        if target:
            normalized[target] = value
            mapped += 1

    normalized["mapping_confidence"] = round(
        mapped / total,
        2,
    )

    return normalized