from collections import Counter
from typing import Any


def _profile_signature(profile: dict[str, Any]) -> tuple:
    """
    Creates a simple structural signature for a log profile.

    Example:
        src_ip, dst_ip, action

    becomes:

        ("src_ip", "dst_ip", "action")
    """
    fields = profile.get("fields", [])

    return tuple(
        sorted(field["name"] for field in fields)
    )


def build_baseline(profiles: list[dict[str, Any]]) -> dict:
    """
    Builds a baseline from previously observed profiles.
    """

    if not profiles:
        raise ValueError("At least one profile is required")

    signatures = [
        _profile_signature(profile)
        for profile in profiles
    ]

    signature_counts = Counter(signatures)

    baseline_signature, occurrences = signature_counts.most_common(1)[0]

    confidence_values = [
        float(profile.get("confidence", 0))
        for profile in profiles
    ]

    average_confidence = sum(confidence_values) / len(confidence_values)

    return {
        "signature": baseline_signature,
        "occurrences": occurrences,
        "average_confidence": round(average_confidence, 3),
        "sample_count": len(profiles),
    }


def compare_with_baseline(
    baseline: dict,
    current_profile: dict,
) -> dict:
    """
    Compares a new profile against the established baseline.
    """

    baseline_signature = tuple(baseline["signature"])
    current_signature = _profile_signature(current_profile)

    structure_match = baseline_signature == current_signature

    baseline_confidence = float(
        baseline.get("average_confidence", 0)
    )

    current_confidence = float(
        current_profile.get("confidence", 0)
    )

    confidence_change = round(
        current_confidence - baseline_confidence,
        3,
    )

    # Calculate how many expected fields disappeared
    baseline_fields = set(baseline_signature)
    current_fields = set(current_signature)

    missing_fields = sorted(
        baseline_fields - current_fields
    )

    new_fields = sorted(
        current_fields - baseline_fields
    )

    # Drift conditions
    structure_drift = not structure_match

    confidence_drift = (
        current_confidence < baseline_confidence - 0.20
    )

    drift_detected = structure_drift or confidence_drift

    if drift_detected:
        if structure_drift and confidence_drift:
            reason = "Structure changed and confidence decreased"
        elif structure_drift:
            reason = "Log structure changed"
        else:
            reason = "Parser confidence decreased"
    else:
        reason = "No significant drift detected"

    return {
        "drift_detected": drift_detected,
        "reason": reason,
        "baseline_confidence": baseline_confidence,
        "current_confidence": current_confidence,
        "confidence_change": confidence_change,
        "missing_fields": missing_fields,
        "new_fields": new_fields,
        "baseline_signature": list(baseline_signature),
        "current_signature": list(current_signature),
    }