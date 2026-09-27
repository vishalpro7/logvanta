import json
import re
from typing import Any


def parse(raw: str, detected_format: str) -> dict[str, Any]:
    if detected_format == "json":
        return json.loads(raw)

    if detected_format == "key_value":
        result = {}
        for k, v in re.findall(r"([A-Za-z_][\w.-]*)=(\"[^\"]*\"|'[^']*'|\S+)", raw):
            result[k] = v.strip('"\'')
        return result

    if detected_format == "syslog":
        return {"message": raw}

    return {"message": raw}
