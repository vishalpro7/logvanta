import json
import re
from collections import Counter
from typing import Any


def _infer_type(value: Any) -> str:
    s = str(value)
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", s):
        return "ip"
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return "number"
    if s.lower() in {"true", "false"}:
        return "boolean"
    if re.search(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}", s):
        return "datetime"
    return "string"


def _profile_json(raw: str):
    data = json.loads(raw)
    if isinstance(data, dict):
        fields = []
        for k, v in data.items():
            fields.append({"name": k, "inferred_type": _infer_type(v), "examples": [str(v)], "confidence": 0.95})
        return fields, 0.98, "json_key_value"
    raise ValueError("JSON log must contain an object")


def _profile_key_value(raw: str):
    pairs = re.findall(r"([A-Za-z_][\w.-]*)=(\"[^\"]*\"|'[^']*'|\S+)", raw)
    if not pairs:
        return None
    fields = []
    for k, v in pairs:
        v = v.strip('"\'')
        fields.append({"name": k, "inferred_type": _infer_type(v), "examples": [v], "confidence": 0.88})
    return fields, 0.86, "key_value"


def _profile_syslog(raw: str):
    if re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}", raw):
        return [
            {"name": "timestamp", "inferred_type": "datetime", "examples": [], "confidence": 0.82},
            {"name": "message", "inferred_type": "string", "examples": [raw], "confidence": 0.72},
        ], 0.82, "syslog"
    return None


def profile_log(raw: str):
    stripped = raw.strip()
    try:
        fields, conf, hint = _profile_json(stripped)
        return "json", fields, conf, hint
    except Exception:
        pass

    kv = _profile_key_value(stripped)
    if kv:
        fields, conf, hint = kv
        return "key_value", fields, conf, hint

    syslog = _profile_syslog(stripped)
    if syslog:
        fields, conf, hint = syslog
        return "syslog", fields, conf, hint

    # Last-resort unknown profile: preserve the sample and force review.
    return "unknown", [
        {"name": "message", "inferred_type": "string", "examples": [stripped], "confidence": 0.35}
    ], 0.35, "human_review"
