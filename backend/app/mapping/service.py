from typing import Any

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


def map_to_ocsf(parsed: dict[str, Any], source: str, event_id: str):
    normalized = {
        "event_id": event_id,
        "source": source,
        "raw": parsed,
        "ocsf_class": "Network Activity",
        "mapping_confidence": 0.0,
    }

    mapped = 0
    total = len(parsed) or 1
    for key, value in parsed.items():
        target = ALIASES.get(key.lower())
        if target:
            normalized[target] = value
            mapped += 1

    normalized["mapping_confidence"] = round(mapped / total, 2)
    return normalized
