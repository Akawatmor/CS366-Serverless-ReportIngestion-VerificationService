"""
Request validators — validate incoming payloads against the API contracts
defined in Service Proposal.
"""
from __future__ import annotations

import re
from typing import Any

from src.models.enums import (
    SourcePlatform,
    ValidationStatus,
)
from src.config import config


SUPPORTED_STATS_REGIONS = {"bkk", "central", "north", "northeast", "south"}


# ---------------------------------------------------------------------------
# Ingest (POST /reports) validation
# ---------------------------------------------------------------------------

def validate_ingest_payload(body: dict[str, Any]) -> list[str]:
    """
    Validate the raw report submission payload.
    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    # reporter_source — required, must be in enum
    source = body.get("reporter_source")
    if not source:
        errors.append("reporter_source is required.")
    elif source not in [e.value for e in SourcePlatform]:
        errors.append(
            f"reporter_source must be one of: {[e.value for e in SourcePlatform]}"
        )

    # reporter_id — required
    if not body.get("reporter_id"):
        errors.append("reporter_id is required.")

    # raw_content or media_urls — at least one
    has_content = bool(body.get("raw_content"))
    has_media = bool(body.get("media_urls")) and len(body.get("media_urls", [])) > 0
    sensor_data = body.get("sensor_data")
    has_sensor_data = isinstance(sensor_data, dict) and len(sensor_data) > 0
    if not has_content and not has_media and not has_sensor_data:
        errors.append("At least one of raw_content, media_urls, or sensor_data is required.")

    # geo_location — optional but validate shape if present
    geo = body.get("geo_location")
    if geo:
        geo_errors = _validate_geo(geo)
        errors.extend(geo_errors)

    # timestamp — optional but must be ISO8601 if present
    ts = body.get("timestamp")
    if ts and not _is_iso8601(ts):
        errors.append("timestamp must be ISO8601 format (e.g. 2026-02-18T14:30:00Z).")

    # media_urls — must be list of strings
    media = body.get("media_urls")
    if media is not None:
        if not isinstance(media, list):
            errors.append("media_urls must be an array of URL strings.")
        else:
            for i, url in enumerate(media):
                if not isinstance(url, str) or not url.startswith("http"):
                    errors.append(f"media_urls[{i}] is not a valid URL.")

    # sensor_data — optional structured sensor payload, useful for IOT sources
    if sensor_data is not None:
        errors.extend(_validate_sensor_data(sensor_data))

    return errors


# ---------------------------------------------------------------------------
# Verify (PATCH /reports/{report_id}) validation
# ---------------------------------------------------------------------------

ALLOWED_VERIFY_STATUSES = {
    ValidationStatus.VERIFIED.value,
    ValidationStatus.SPAM.value,
    ValidationStatus.DUPLICATE.value,
    ValidationStatus.REJECTED.value,
}

# Valid state transitions from current → new
VALID_TRANSITIONS: dict[str, set[str]] = {
    ValidationStatus.RECEIVED.value: {
        ValidationStatus.PENDING_REVIEW.value,
        ValidationStatus.SPAM.value,
        ValidationStatus.REJECTED.value,
        ValidationStatus.DUPLICATE.value,
    },
    ValidationStatus.PENDING_REVIEW.value: {
        ValidationStatus.VERIFIED.value,
        ValidationStatus.SPAM.value,
        ValidationStatus.REJECTED.value,
        ValidationStatus.DUPLICATE.value,
    },
}


def validate_verify_payload(body: dict[str, Any]) -> list[str]:
    """
    Validate the verification decision payload.
    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    status = body.get("validation_status")
    if not status:
        errors.append("validation_status is required.")
    elif status not in ALLOWED_VERIFY_STATUSES:
        errors.append(
            f"validation_status must be one of: {list(ALLOWED_VERIFY_STATUSES)}"
        )

    # If VERIFIED, reviewer_id is mandatory
    if status == ValidationStatus.VERIFIED.value:
        if not body.get("reviewer_id"):
            errors.append("reviewer_id is required when validation_status is VERIFIED.")

    # link_to_incident_id — optional, but must look like UUID if present
    link = body.get("link_to_incident_id")
    if link and not isinstance(link, str):
        errors.append("link_to_incident_id must be a string.")
    if link and status != ValidationStatus.VERIFIED.value:
        errors.append("link_to_incident_id is only allowed when validation_status is VERIFIED.")

    return errors


def validate_status_transition(current_status: str, new_status: str) -> str | None:
    """
    Check if the status transition is valid.
    Returns error message or None if valid.
    """
    allowed = VALID_TRANSITIONS.get(current_status)
    if allowed is None:
        return f"Report with status '{current_status}' cannot be updated."
    if new_status not in allowed:
        return (
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed: {list(allowed)}"
        )
    return None


# ---------------------------------------------------------------------------
# Delete (DELETE /reports/{report_id}) validation
# ---------------------------------------------------------------------------

def validate_delete_payload(body: dict[str, Any]) -> list[str]:
    """Validate soft-delete request body."""
    errors: list[str] = []
    if not body.get("reason"):
        errors.append("reason is required for audit purposes.")
    if not body.get("deleted_by"):
        errors.append("deleted_by is required.")
    return errors


# ---------------------------------------------------------------------------
# Query params validation
# ---------------------------------------------------------------------------

def validate_list_params(params: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    """
    Parse and validate query parameters for GET /reports.
    Returns (parsed_params, errors).
    """
    errors: list[str] = []
    parsed: dict[str, Any] = {}

    # status filter
    status = params.get("status")
    if status:
        all_statuses = {e.value for e in ValidationStatus}
        if status not in all_statuses:
            errors.append(f"status must be one of: {list(all_statuses)}")
        else:
            parsed["status"] = status

    # min_trust_score
    score = params.get("min_trust_score")
    if score is not None:
        try:
            s = int(score)
            if not (0 <= s <= 100):
                errors.append("min_trust_score must be 0-100.")
            else:
                parsed["min_trust_score"] = s
        except ValueError:
            errors.append("min_trust_score must be an integer.")

    # limit
    limit = params.get("limit")
    if limit is not None:
        try:
            lim = int(limit)
            if lim < 1 or lim > config.MAX_PAGE_LIMIT:
                errors.append(f"limit must be between 1 and {config.MAX_PAGE_LIMIT}.")
            else:
                parsed["limit"] = lim
        except ValueError:
            errors.append("limit must be a positive integer.")
    else:
        parsed["limit"] = config.DEFAULT_PAGE_LIMIT

    # priority filter
    priority = (params.get("priority") or "all").lower().strip()
    allowed_priorities = {"all", "high", "normal"}
    if priority not in allowed_priorities:
        errors.append(f"priority must be one of: {sorted(allowed_priorities)}")
    else:
        parsed["priority"] = priority

    return parsed, errors


def validate_stats_params(params: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    """Parse and validate query parameters for GET /reports/stats."""
    errors: list[str] = []
    parsed: dict[str, Any] = {}

    timeframe = params.get("timeframe", "today")
    allowed_tf = {"today", "last_24h", "last_7d"}
    if timeframe not in allowed_tf:
        errors.append(f"timeframe must be one of: {list(allowed_tf)}")
    else:
        parsed["timeframe"] = timeframe

    region = params.get("region")
    if region:
        normalized = region.lower().strip()
        if normalized not in SUPPORTED_STATS_REGIONS:
            errors.append(f"region must be one of: {sorted(SUPPORTED_STATS_REGIONS)}")
        else:
            parsed["region"] = normalized

    return parsed, errors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_geo(geo: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(geo, dict):
        errors.append("geo_location must be an object with lat and lon.")
        return errors
    lat = geo.get("lat")
    lon = geo.get("lon")
    if lat is None or lon is None:
        errors.append("geo_location must contain both lat and lon.")
    else:
        try:
            lat_f = float(lat)
            lon_f = float(lon)
            if not (-90 <= lat_f <= 90):
                errors.append("geo_location.lat must be between -90 and 90.")
            if not (-180 <= lon_f <= 180):
                errors.append("geo_location.lon must be between -180 and 180.")
        except (ValueError, TypeError):
            errors.append("geo_location.lat and lon must be numeric.")
    return errors


def _validate_sensor_data(sensor_data: Any) -> list[str]:
    """Validate optional structured sensor metadata."""
    errors: list[str] = []
    if not isinstance(sensor_data, dict):
        errors.append("sensor_data must be an object.")
        return errors

    string_fields = {
        "sensor_id",
        "sensor_type",
        "site_id",
        "metric_name",
        "unit",
        "status",
    }
    numeric_fields = {"metric_value", "threshold"}

    for field_name in string_fields:
        value = sensor_data.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(f"sensor_data.{field_name} must be a string.")

    for field_name in numeric_fields:
        value = sensor_data.get(field_name)
        if value is None:
            continue
        try:
            float(value)
        except (TypeError, ValueError):
            errors.append(f"sensor_data.{field_name} must be numeric.")

    if sensor_data.get("observed_at") and not _is_iso8601(sensor_data["observed_at"]):
        errors.append("sensor_data.observed_at must be ISO8601 format.")

    if not sensor_data.get("metric_name"):
        errors.append("sensor_data.metric_name is required when sensor_data is provided.")
    if sensor_data.get("metric_value") is None:
        errors.append("sensor_data.metric_value is required when sensor_data is provided.")

    return errors


def _is_iso8601(value: str) -> bool:
    """Simple check for ISO8601 datetime string."""
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    return bool(re.match(pattern, value))
