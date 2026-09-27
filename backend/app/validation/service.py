import re


def validate(event: dict) -> dict:
    errors = []
    warnings = []

    for field in ["event_id", "source", "ocsf_class"]:
        if not event.get(field):
            errors.append(f"Missing required field: {field}")

    for field in ["source_endpoint", "destination_endpoint"]:
        value = event.get(field)
        if value and not re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", str(value)):
            warnings.append(f"{field} is not a recognized IPv4 address: {value}")

    confidence = float(event.get("mapping_confidence", 0))
    if confidence < 0.60:
        warnings.append("Low mapping confidence; human review recommended")

    return {"valid": not errors, "errors": errors, "warnings": warnings}
