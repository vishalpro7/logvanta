import hashlib
import json


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_trace(event_id: str, source: str, raw_log: str, normalized: dict) -> dict:
    return {
        "event_id": event_id,
        "source": source,
        "raw_sha256": sha256_text(raw_log),
        "raw_preserved": True,
        "normalized_fields": {
            k: {"value": v, "source": k}
            for k, v in normalized.items()
            if k not in {"raw", "event_id", "source", "ocsf_class", "mapping_confidence"}
        },
    }
