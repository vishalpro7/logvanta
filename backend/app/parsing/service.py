import json
import re
from typing import Any


SYSLOG_PATTERN = re.compile(
    r"^(?P<timestamp>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<message>.*)$"
)


def parse(raw: str, detected_format: str) -> dict[str, Any]:
    if detected_format == "json":
        return json.loads(raw)

    if detected_format == "key_value":
        result = {}

        for k, v in re.findall(
            r"([A-Za-z_][\w.-]*)=(\"[^\"]*\"|'[^']*'|\S+)",
            raw,
        ):
            result[k] = v.strip('"\'')
        
        return result

    if detected_format == "syslog":
        match = SYSLOG_PATTERN.match(raw.strip())

        if match:
            return {
                "timestamp": match.group("timestamp"),
                "message": match.group("message"),
            }

        return {
            "message": raw
        }

    return {
        "message": raw
    }