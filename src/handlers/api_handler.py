"""
API Handler — single Lambda that routes all synchronous REST API requests.

Endpoints handled:
  - GET    /reports              → list pending reports
  - GET    /reports/stats        → dashboard statistics
  - GET    /reports/{report_id}  → report detail
  - PATCH  /reports/{report_id}  → verify/reject report
  - DELETE /reports/{report_id}  → soft-delete report
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html import escape as xml_escape
from typing import Any

import boto3

from src.config import config
from src.models.report import Report
from src.models.enums import ValidationStatus, VerificationAction
from src.services.audit_service import AuditService
from src.services.event_publisher import EventPublisher
from src.services.geocoding_service import reverse_geocoding_service
from src.utils.logger import get_logger
from src.utils import response
from src.utils.validators import (
    validate_verify_payload,
    validate_status_transition,
    validate_delete_payload,
    validate_list_params,
    validate_stats_params,
)

logger = get_logger(__name__)


REGION_BOUNDARIES: dict[str, dict[str, tuple[float, float] | str]] = {
    "bkk": {
        "label": "Bangkok",
        "lat": (13.45, 13.95),
        "lon": (100.30, 100.95),
    },
    "central": {
        "label": "Central",
        "lat": (13.00, 16.50),
        "lon": (99.00, 101.80),
    },
    "north": {
        "label": "North",
        "lat": (17.00, 20.50),
        "lon": (97.00, 101.50),
    },
    "northeast": {
        "label": "Northeast",
        "lat": (14.00, 18.50),
        "lon": (101.00, 105.80),
    },
    "south": {
        "label": "South",
        "lat": (6.00, 13.00),
        "lon": (98.00, 101.50),
    },
}

_STATS_CACHE: dict[str, dict[str, Any]] = {}

CHANGELOG_ENTRIES: list[dict[str, str]] = [
    {
        "id": "2026-04-20-deprecation-info",
        "title": "Added deprecation info endpoint and improved deprecation headers",
        "description": (
            "New GET /v1/deprecation-info returns all deprecated or sunset endpoints. "
            "Deprecation headers X-Deprecated-Version and X-Sunset-Date are now "
            "included in success responses when applicable."
        ),
        "version": "1.2.0",
        "published_at": "2026-04-20T08:00:00+00:00",
    },
    {
        "id": "2026-04-20-trace-cloudwatch",
        "title": "Added trace lookup guide and CloudWatch tracing support",
        "description": (
            "X-Trace-Id can now be used to search CloudWatch Logs across all Lambda "
            "functions for end-to-end request tracing."
        ),
        "version": "1.1.1",
        "published_at": "2026-04-20T07:00:00+00:00",
    },
    {
        "id": "2026-04-19-openapi-rss",
        "title": "Added OpenAPI specification and RSS changelog endpoint",
        "description": (
            "Published OpenAPI 3.0 spec for API consumers and added "
            "GET /v1/changelog.xml feed for machine-readable change tracking."
        ),
        "version": "1.1.0",
        "published_at": "2026-04-19T10:00:00+00:00",
    },
    {
        "id": "2026-04-08-observability",
        "title": "Improved response observability",
        "description": (
            "Added X-Trace-Id header and standardized error responses with "
            "traceId, errorCode, and timestamp fields."
        ),
        "version": "1.0.2",
        "published_at": "2026-04-08T09:00:00+00:00",
    },
    {
        "id": "2026-04-08-contract-versioning",
        "title": "Added schemaVersion to async events",
        "description": (
            "EventBridge payloads now include schemaVersion to support safer "
            "contract evolution for downstream consumers."
        ),
        "version": "1.0.1",
        "published_at": "2026-04-08T08:30:00+00:00",
    },
]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> dict:
    """
    API Gateway Proxy integration — route based on method + resource path.
    """
    start = time.time()
    request_id = context.aws_request_id if context else str(uuid.uuid4())

    method = event.get("httpMethod", "").upper()
    path = event.get("resource", event.get("path", ""))
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    logger.info("API request", extra={
        "request_id": request_id,
        "data": {"method": method, "path": path},
    })

    dynamodb = boto3.client("dynamodb", region_name=config.AWS_REGION)

    try:
        # Route matching
        if method == "GET" and path in ("/reports", "/v1/reports"):
            # Check if it's /reports/stats
            if query_params.get("_route") == "stats":
                result = _handle_get_stats(query_params, dynamodb, request_id)
            else:
                result = _handle_list_reports(query_params, dynamodb, request_id)

        elif method == "GET" and "/stats" in path:
            result = _handle_get_stats(query_params, dynamodb, request_id)

        elif method == "GET" and "/audit" in path:
            result = _handle_get_audit_logs(query_params, dynamodb, request_id)

        elif method == "GET" and "/events" in path:
            result = _handle_get_events(query_params, dynamodb, request_id)

        elif method == "GET" and "changelog.xml" in path:
            result = _handle_changelog_rss(event, request_id)

        elif method == "GET" and "deprecation-info" in path:
            result = _handle_deprecation_info(request_id)

        elif method == "GET" and "/trace/" in path:
            trace_target = path_params.get("trace_id") or path.rstrip("/").rsplit("/", 1)[-1]
            result = _handle_trace_lookup(trace_target, request_id)

        elif method == "POST" and "/upload-url" in path:
            body = _parse_body(event, request_id)
            if isinstance(body, dict) and "error" in body:
                result = body
            else:
                result = _handle_upload_url(body, request_id)

        elif method == "GET" and path_params.get("report_id"):
            result = _handle_get_detail(path_params["report_id"], dynamodb, request_id)

        elif method == "PATCH" and path_params.get("report_id"):
            body = _parse_body(event, request_id)
            if isinstance(body, dict) and "error" in body:
                result = body  # Return parse error
            else:
                result = _handle_verify(path_params["report_id"], body, dynamodb, request_id)

        elif method == "DELETE" and path_params.get("report_id"):
            body = _parse_body(event, request_id)
            if isinstance(body, dict) and "error" in body:
                result = body
            else:
                result = _handle_delete(path_params["report_id"], body, dynamodb, request_id)

        elif method == "POST" and "report-incident" in path:
            body = _parse_body(event, request_id)
            if isinstance(body, dict) and "error" in body:
                result = body
            else:
                result = _handle_incident_result(body, dynamodb, request_id)

        elif method == "OPTIONS":
            result = response.success({"message": "CORS preflight OK"}, trace_id=request_id)

        else:
            result = response.not_found(f"No route for {method} {path}", trace_id=request_id)

    except Exception as e:
        logger.error("Unhandled error in API handler", exc_info=True)
        result = response.internal_error(str(e), trace_id=request_id)

    duration_ms = int((time.time() - start) * 1000)
    logger.info("API response", extra={
        "request_id": request_id,
        "data": {
            "status_code": result.get("statusCode"),
            "duration_ms": duration_ms,
        },
    })
    return result


# ---------------------------------------------------------------------------
# GET /reports — List pending reports (API Contract #2)
# ---------------------------------------------------------------------------

def _handle_list_reports(query_params: dict, dynamodb, trace_id: str | None = None) -> dict:
    """Query reports by status with optional trust score filter."""
    parsed, errors = validate_list_params(query_params)
    if errors:
        return response.bad_request("Invalid query parameters.", "; ".join(errors), trace_id=trace_id)

    status = parsed.get("status", ValidationStatus.PENDING_REVIEW.value)
    limit = parsed.get("limit", config.DEFAULT_PAGE_LIMIT)
    min_score = parsed.get("min_trust_score")
    priority_filter = parsed.get("priority", "all")
    query_fetch_limit = min(max(limit * 4, limit), config.MAX_PAGE_LIMIT)

    try:
        expr_values: dict[str, Any] = {
            ":status": {"S": status},
        }
        filter_expr = None

        if min_score is not None:
            filter_expr = "trust_score >= :min_score"
            expr_values[":min_score"] = {"N": str(min_score)}

        query_kwargs: dict[str, Any] = {
            "TableName": config.REPORTS_TABLE,
            "IndexName": "gsi_status_ingested",
            "KeyConditionExpression": "validation_status = :status",
            "ExpressionAttributeValues": expr_values,
            "ScanIndexForward": False,  # newest first
            "Limit": query_fetch_limit,
        }
        if filter_expr is not None:
            query_kwargs["FilterExpression"] = filter_expr

        resp = dynamodb.query(**query_kwargs)

        items = resp.get("Items", [])
        reports_all = [Report.from_dynamodb_item(item) for item in items]

        if priority_filter == "high":
            reports_all = [r for r in reports_all if r.priority > 0]
        elif priority_filter == "normal":
            reports_all = [r for r in reports_all if r.priority <= 0]

        reports_all.sort(key=lambda r: (r.priority, r.ingested_at), reverse=True)
        reports = [r.to_api_summary() for r in reports_all[:limit]]

        return response.success({
            "data": reports,
            "total_count": len(reports_all),
        }, trace_id=trace_id)

    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        return response.internal_error("Failed to retrieve reports.", trace_id=trace_id)


# ---------------------------------------------------------------------------
# GET /reports/{report_id} — Report detail (API Contract #4)
# ---------------------------------------------------------------------------

def _handle_get_detail(report_id: str, dynamodb, trace_id: str | None = None) -> dict:
    """Get full report detail by ID."""
    try:
        resp = dynamodb.get_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": report_id}},
        )

        item = resp.get("Item")
        if not item:
            return response.not_found(f"Report '{report_id}' not found.", trace_id=trace_id)

        report = Report.from_dynamodb_item(item)

        # Don't show DELETED reports
        if report.validation_status == ValidationStatus.DELETED.value:
            return response.not_found(f"Report '{report_id}' not found.", trace_id=trace_id)

        return response.success(report.to_api_detail(), trace_id=trace_id)

    except Exception as e:
        logger.error(f"Error getting report detail: {e}", exc_info=True)
        return response.internal_error("Failed to retrieve report.", trace_id=trace_id)


# ---------------------------------------------------------------------------
# PATCH /reports/{report_id} — Verify/Reject (API Contract #3)
# ---------------------------------------------------------------------------

def _handle_verify(report_id: str, body: dict, dynamodb, trace_id: str | None = None) -> dict:
    """Process verification decision from Trust Officer."""
    errors = validate_verify_payload(body)
    if errors:
        return response.bad_request("Validation failed.", "; ".join(errors), trace_id=trace_id)

    new_status = body["validation_status"]

    # Fetch current report
    try:
        resp = dynamodb.get_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": report_id}},
        )
        item = resp.get("Item")
        if not item:
            return response.not_found(f"Report '{report_id}' not found.", trace_id=trace_id)

        current_status = item["validation_status"]["S"]
    except Exception as e:
        logger.error(f"Error fetching report for verify: {e}", exc_info=True)
        return response.internal_error("Failed to retrieve report.", trace_id=trace_id)

    # Validate transition
    transition_error = validate_status_transition(current_status, new_status)
    if transition_error:
        return response.conflict(transition_error, trace_id=trace_id)

    # Determine action
    link_incident_id = body.get("link_to_incident_id")
    if new_status == ValidationStatus.VERIFIED.value:
        if link_incident_id:
            action_taken = VerificationAction.MERGED_EXISTING_INCIDENT.value
        else:
            action_taken = VerificationAction.TRIGGER_NEW_INCIDENT.value
    else:
        action_taken = VerificationAction.NO_ACTION.value

    # Update with optimistic locking (ConditionExpression)
    now = datetime.now(timezone.utc).isoformat()
    update_expr = (
        "SET validation_status = :new_status, "
        "verified_by = :reviewer, "
        "verification_notes = :notes, "
        "updated_at = :now"
    )
    expr_values: dict[str, Any] = {
        ":new_status": {"S": new_status},
        ":reviewer": {"S": body.get("reviewer_id", "")},
        ":notes": {"S": body.get("reviewer_notes", "")},
        ":now": {"S": now},
        ":expected_status": {"S": current_status},
    }

    if link_incident_id:
        update_expr += ", linked_incident_id = :incident_id"
        expr_values[":incident_id"] = {"S": link_incident_id}

    try:
        dynamodb.update_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": report_id}},
            UpdateExpression=update_expr,
            ConditionExpression="validation_status = :expected_status",
            ExpressionAttributeValues=expr_values,
        )
    except dynamodb.exceptions.ConditionalCheckFailedException:
        return response.conflict(
            "Report has been modified by another user. Please refresh and try again.",
            trace_id=trace_id,
        )
    except Exception as e:
        logger.error(f"Error updating report status: {e}", exc_info=True)
        return response.internal_error("Failed to update report.", trace_id=trace_id)

    # --- Post-update async actions ---
    audit_svc = AuditService(dynamodb_client=dynamodb)
    event_pub = EventPublisher()

    # Audit log
    audit_svc.log_status_change(
        report_id=report_id,
        actor_id=body.get("reviewer_id", ""),
        old_status=current_status,
        new_status=new_status,
        notes=body.get("reviewer_notes", ""),
    )

    # Update stats
    if new_status == ValidationStatus.VERIFIED.value:
        _update_stat(dynamodb, "verified_incidents", 1)
        _update_stat(dynamodb, "pending_review", -1)
    elif new_status in (ValidationStatus.SPAM.value, ValidationStatus.REJECTED.value):
        _update_stat(dynamodb, "spam_rejected", 1)
        _update_stat(dynamodb, "pending_review", -1)

    # Publish events
    event_pub.publish_status_changed(
        report_id=report_id,
        old_status=current_status,
        new_status=new_status,
        changed_by=body.get("reviewer_id", ""),
        reason=body.get("reviewer_notes", ""),
    )

    # If VERIFIED → also publish ReportVerifiedEvent for Incident Service
    if new_status == ValidationStatus.VERIFIED.value:
        report = Report.from_dynamodb_item(item)
        severity_level = _calculate_severity_level(report)
        reporter_count = _calculate_reporter_count(dynamodb, report)
        address_text = _resolve_address_text(report)

        incident_data = {
            "type": report.suggested_category or "OTHER",
            "description": report.raw_content[:500],
            "severity_level": severity_level,
            "location": report.geo_location.to_dict() if report.geo_location else None,
            "reporter_count": reporter_count,
            "media_evidence": report.media_urls,
        }
        if address_text:
            incident_data["address_text"] = address_text

        event_pub.publish_report_verified(
            report_id=report_id,
            suggested_incident_data=incident_data,
            verified_by=body.get("reviewer_id", ""),
            verification_notes=body.get("reviewer_notes", ""),
            action=action_taken,
        )

    return response.success({
        "report_id": report_id,
        "validation_status": new_status,
        "action_taken": action_taken,
        "updated_at": now,
    }, trace_id=trace_id)


# ---------------------------------------------------------------------------
# DELETE /reports/{report_id} — Soft delete (API Contract #6)
# ---------------------------------------------------------------------------

def _handle_delete(report_id: str, body: dict, dynamodb, trace_id: str | None = None) -> dict:
    """Soft-delete (archive) a report."""
    errors = validate_delete_payload(body)
    if errors:
        return response.bad_request("Validation failed.", "; ".join(errors), trace_id=trace_id)

    # Check report exists
    try:
        resp = dynamodb.get_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": report_id}},
            ProjectionExpression="report_id, validation_status",
        )
        item = resp.get("Item")
        if not item:
            return response.not_found(f"Report '{report_id}' not found.", trace_id=trace_id)

        if item["validation_status"]["S"] == ValidationStatus.DELETED.value:
            return response.not_found(f"Report '{report_id}' not found.", trace_id=trace_id)

    except Exception as e:
        logger.error(f"Error checking report for delete: {e}", exc_info=True)
        return response.internal_error("Failed to check report.", trace_id=trace_id)

    # Soft delete — set status to DELETED
    now = datetime.now(timezone.utc).isoformat()
    try:
        dynamodb.update_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": report_id}},
            UpdateExpression=(
                "SET validation_status = :deleted, "
                "deleted_by = :who, "
                "deleted_reason = :reason, "
                "updated_at = :now"
            ),
            ExpressionAttributeValues={
                ":deleted": {"S": ValidationStatus.DELETED.value},
                ":who": {"S": body["deleted_by"]},
                ":reason": {"S": body["reason"]},
                ":now": {"S": now},
            },
        )
    except Exception as e:
        logger.error(f"Error soft-deleting report: {e}", exc_info=True)
        return response.internal_error("Failed to delete report.", trace_id=trace_id)

    # Audit log
    audit_svc = AuditService(dynamodb_client=dynamodb)
    audit_svc.log_soft_delete(
        report_id=report_id,
        deleted_by=body["deleted_by"],
        reason=body["reason"],
    )

    return response.success({
        "report_id": report_id,
        "status": "DELETED",
        "message": "Report has been archived and removed from public view.",
    }, trace_id=trace_id)


# ---------------------------------------------------------------------------
# POST /report-incident — Receive IncidentCreationResultEvent from Incident Service
# ---------------------------------------------------------------------------

def _handle_incident_result(body: dict, dynamodb, trace_id: str | None = None) -> dict:
    """
    Callback from Incident Tracking Service after it processes a ReportVerifiedEvent.

    Accepts both ``original_report_ref_id`` (preferred) and ``source_report_id``
    (fallback) to identify the originating report — whichever is present is used.

    On CREATED: auto-populate linked_incident_id on the report in DynamoDB and
                record full incident metadata in the audit log.
    On FAILED:  write an audit log entry so the failure is traceable.
    """
    logger.info(
        "report-incident callback received",
        extra={"request_id": trace_id, "data": {"body_keys": list(body.keys()), "body": body}},
    )

    # --- Unwrap event envelope format (eventType + data) if present ---
    # Supports both flat body and envelope: { eventType, data: { ... } }
    event_type = body.get("eventType", "")
    if event_type and isinstance(body.get("data"), dict):
        payload = body["data"]
        # Map eventType to status
        if event_type in ("INCIDENT_CREATED", "INCIDENT_UPDATED"):
            payload.setdefault("status", "CREATED")
        elif event_type in ("INCIDENT_FAILED", "INCIDENT_ERROR"):
            payload.setdefault("status", "FAILED")
    else:
        payload = body

    # --- Resolve report reference (own field takes priority, then friend's field) ---
    # Accept: original_report_ref_id (ours) > source_report_id > report_id (common alias)
    report_ref_id = (
        payload.get("original_report_ref_id")
        or payload.get("source_report_id")
        or payload.get("report_id")
        or ""
    ).strip()

    status = payload.get("status", "").strip()
    incident_id = payload.get("incident_id", "").strip()
    error_code = payload.get("error_code", "")
    error_message = payload.get("error_message", "")

    # Additional fields sent by the Incident Tracking Service on creation
    incident_type = payload.get("incident_type") or payload.get("indident_type") or ""
    incident_description = payload.get("incident_description", "")
    exact_location = payload.get("exact_location", "")
    exact_location_description = payload.get("exact_location_description", "")
    impact_level = payload.get("impact_level", "")
    priority = payload.get("priority", "")

    # Normalise status aliases: REPORTED / ACTIVE → CREATED
    if status in ("REPORTED", "ACTIVE", "OPEN"):
        status = "CREATED"

    if not report_ref_id:
        # This incident was not triggered by our service — gracefully ignore it
        logger.info(
            "report-incident callback ignored (no report ref_id)",
            extra={"request_id": trace_id, "data": {"event_type": event_type}},
        )
        return response.success({
            "acknowledged": True,
            "message": "Event acknowledged — no linked report, skipped.",
        }, trace_id=trace_id)
    if status not in ("CREATED", "FAILED"):
        return response.bad_request(
            "Validation failed.", "status must be CREATED or FAILED.", trace_id=trace_id
        )
    if status == "CREATED" and not incident_id:
        return response.bad_request(
            "Validation failed.", "incident_id is required when status is CREATED.", trace_id=trace_id
        )

    now = datetime.now(timezone.utc).isoformat()
    audit_svc = AuditService(dynamodb_client=dynamodb)

    if status == "CREATED":
        # Auto-populate linked_incident_id so GET /reports/{id} shows it immediately
        try:
            dynamodb.update_item(
                TableName=config.REPORTS_TABLE,
                Key={"report_id": {"S": report_ref_id}},
                UpdateExpression="SET linked_incident_id = :iid, updated_at = :now",
                ConditionExpression="attribute_exists(report_id)",
                ExpressionAttributeValues={
                    ":iid": {"S": incident_id},
                    ":now": {"S": now},
                },
            )
            logger.info(
                "Linked incident to report",
                extra={"request_id": trace_id, "data": {
                    "report_id": report_ref_id,
                    "incident_id": incident_id,
                }},
            )
        except dynamodb.exceptions.ConditionalCheckFailedException:
            return response.not_found(
                f"Report '{report_ref_id}' not found.", trace_id=trace_id
            )
        except Exception as e:
            logger.error(f"Error linking incident to report: {e}", exc_info=True)
            return response.internal_error("Failed to update report.", trace_id=trace_id)

        # Store full incident metadata in the audit log for traceability
        incident_log_data: dict = {"linked_incident_id": incident_id}
        if incident_type:
            incident_log_data["incident_type"] = incident_type
        if incident_description:
            incident_log_data["incident_description"] = incident_description
        if exact_location:
            incident_log_data["exact_location"] = exact_location
        if exact_location_description:
            incident_log_data["exact_location_description"] = exact_location_description
        if impact_level:
            incident_log_data["impact_level"] = impact_level
        if priority:
            incident_log_data["priority"] = str(priority)

        audit_svc._write_log(
            report_id=report_ref_id,
            actor_id="service.incident-tracking",
            action_type="INCIDENT_LINKED",
            previous_value={"linked_incident_id": None},
            new_value=incident_log_data,
        )

        return response.success({
            "report_id": report_ref_id,
            "linked_incident_id": incident_id,
            "message": "Report successfully linked to incident.",
        }, trace_id=trace_id)

    # status == "FAILED"
    audit_svc._write_log(
        report_id=report_ref_id,
        actor_id="service.incident-tracking",
        action_type="INCIDENT_LINK_FAILED",
        previous_value=None,
        new_value={
            "error_code": error_code,
            "error_message": error_message,
        },
    )
    logger.warning(
        "Incident creation failed for report",
        extra={"request_id": trace_id, "data": {
            "report_id": report_ref_id,
            "error_code": error_code,
            "error_message": error_message,
        }},
    )

    return response.success({
        "report_id": report_ref_id,
        "acknowledged": True,
        "message": "Failure notification recorded.",
    }, trace_id=trace_id)


# ---------------------------------------------------------------------------
# GET /reports/stats — Dashboard stats (API Contract #5)
# ---------------------------------------------------------------------------

def _handle_get_stats(query_params: dict, dynamodb, trace_id: str | None = None) -> dict:
    """Get aggregated dashboard statistics with timeframe + region filtering."""
    parsed, errors = validate_stats_params(query_params)
    if errors:
        return response.bad_request("Invalid parameters.", "; ".join(errors), trace_id=trace_id)

    timeframe = parsed.get("timeframe", "today")
    region = parsed.get("region")
    cache_key = f"{timeframe}|{region or 'all'}"

    now_ts = time.time()
    cached = _STATS_CACHE.get(cache_key)
    if cached and cached.get("expires_at", 0) > now_ts:
        return response.success(cached["payload"], trace_id=trace_id)

    try:
        report_items = _collect_reports_for_stats(
            dynamodb=dynamodb,
            timeframe=timeframe,
            region=region,
        )
        summary = _summarize_report_items(report_items)

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "timeframe": timeframe,
            "region": region,
            "supported_regions": sorted(REGION_BOUNDARIES.keys()),
            "summary": summary,
            "trending_keywords": _compute_trending_keywords(report_items),
            "heatmap_data": _compute_heatmap_data(report_items),
        }

        _STATS_CACHE[cache_key] = {
            "payload": payload,
            "expires_at": now_ts + config.STATS_CACHE_TTL_SECONDS,
        }

        return response.success(payload, trace_id=trace_id)

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return response.internal_error("Failed to compute statistics.", trace_id=trace_id)


# ---------------------------------------------------------------------------
# GET /reports/audit — Audit logs (safe table read)
# ---------------------------------------------------------------------------

def _handle_get_audit_logs(query_params: dict, dynamodb, trace_id: str | None = None) -> dict:
    """Retrieve audit logs, optionally filtered by report_id."""
    report_id = query_params.get("report_id")
    limit = min(int(query_params.get("limit", "20")), 100)

    try:
        if report_id:
            # Query by report using GSI
            resp = dynamodb.query(
                TableName=config.AUDIT_TABLE,
                IndexName="gsi_report_timestamp",
                KeyConditionExpression="report_ref_id = :rid",
                ExpressionAttributeValues={":rid": {"S": report_id}},
                ScanIndexForward=False,
                Limit=limit,
            )
        else:
            # Scan recent audit logs (limited)
            resp = dynamodb.scan(
                TableName=config.AUDIT_TABLE,
                Limit=limit,
            )

        items = resp.get("Items", [])
        logs = []
        for item in items:
            log_entry = {
                "log_id": item.get("log_id", {}).get("S", ""),
                "report_ref_id": item.get("report_ref_id", {}).get("S", ""),
                "actor_id": item.get("actor_id", {}).get("S", ""),
                "action_type": item.get("action_type", {}).get("S", ""),
                "timestamp": item.get("timestamp", {}).get("S", ""),
            }
            if "new_value" in item:
                try:
                    log_entry["new_value"] = json.loads(item["new_value"]["S"])
                except Exception:
                    log_entry["new_value"] = item["new_value"]["S"]
            if "previous_value" in item:
                try:
                    log_entry["previous_value"] = json.loads(item["previous_value"]["S"])
                except Exception:
                    log_entry["previous_value"] = item["previous_value"]["S"]
            logs.append(log_entry)

        return response.success({
            "data": logs,
            "total_count": len(logs),
        }, trace_id=trace_id)

    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}", exc_info=True)
        return response.internal_error("Failed to retrieve audit logs.", trace_id=trace_id)


# ---------------------------------------------------------------------------
# GET /reports/events — Recent EventBridge events (from CloudWatch Logs)
# ---------------------------------------------------------------------------

def _handle_get_events(query_params: dict, dynamodb, trace_id: str | None = None) -> dict:
    """Retrieve recent EventBridge events from CloudWatch Logs."""
    limit = min(int(query_params.get("limit", "20")), 50)
    event_type = query_params.get("type", "all")  # all, verified, status-changed

    try:
        logs_client = boto3.client("logs", region_name=config.AWS_REGION)
        events = []

        # Determine which log groups to query
        prefix = config.EVENT_BUS_NAME.rsplit("-disaster-event-bus", 1)[0]
        log_groups = []
        if event_type in ("all", "verified"):
            log_groups.append(f"/events/{prefix}/report-verified")
        if event_type in ("all", "status-changed"):
            log_groups.append(f"/events/{prefix}/status-changed")

        for log_group in log_groups:
            try:
                resp = logs_client.filter_log_events(
                    logGroupName=log_group,
                    limit=limit,
                    interleaved=True,
                )
                for ev in resp.get("events", []):
                    try:
                        msg = json.loads(ev.get("message", "{}"))
                        events.append({
                            "event_type": msg.get("detail-type", "Unknown"),
                            "source": msg.get("source", ""),
                            "timestamp": ev.get("timestamp"),
                            "detail": msg.get("detail", {}),
                        })
                    except (json.JSONDecodeError, TypeError):
                        events.append({
                            "event_type": "raw",
                            "message": ev.get("message", "")[:500],
                            "timestamp": ev.get("timestamp"),
                        })
            except Exception as e:
                logger.warning(f"Could not read log group {log_group}: {e}")

        # Sort by timestamp descending
        events.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        events = events[:limit]

        return response.success({
            "data": events,
            "total_count": len(events),
            "log_groups": log_groups,
        }, trace_id=trace_id)

    except Exception as e:
        logger.error(f"Error fetching events: {e}", exc_info=True)
        return response.internal_error("Failed to retrieve events.", trace_id=trace_id)


# ---------------------------------------------------------------------------
# POST /reports/upload-url — Generate presigned S3 URL for media upload
# ---------------------------------------------------------------------------

def _handle_upload_url(body: dict, trace_id: str | None = None) -> dict:
    """Generate a presigned S3 PUT URL for uploading media evidence."""
    filename = body.get("filename", "")
    content_type = body.get("content_type", "application/octet-stream")
    report_id = body.get("report_id", "")
    file_size = body.get("file_size_bytes")

    if not filename:
        return response.bad_request("filename is required.", trace_id=trace_id)

    if not config.MEDIA_BUCKET:
        return response.internal_error("Media storage not configured.", trace_id=trace_id)

    # Validate content type
    allowed_types = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "video/mp4", "video/quicktime", "video/x-msvideo",
        "application/pdf",
    ]
    if content_type not in allowed_types:
        return response.bad_request(
            f"Unsupported content_type. Allowed: {allowed_types}",
            trace_id=trace_id,
        )

    if file_size is not None:
        try:
            file_size_int = int(file_size)
        except (TypeError, ValueError):
            return response.bad_request("file_size_bytes must be an integer.", trace_id=trace_id)

        if file_size_int <= 0:
            return response.bad_request("file_size_bytes must be greater than 0.", trace_id=trace_id)

        if file_size_int > config.UPLOAD_MAX_FILE_BYTES:
            return response.bad_request(
                f"file_size_bytes exceeds max limit of {config.UPLOAD_MAX_FILE_BYTES} bytes.",
                trace_id=trace_id,
            )

    # Build S3 key: media/{report_id_or_temp}/{uuid}_{filename}
    prefix = report_id if report_id else "temp"
    safe_filename = filename.replace(" ", "_").replace("/", "_")
    media_id = f"m-{uuid.uuid4().hex[:12]}"
    s3_key = f"media/{prefix}/{media_id}_{safe_filename}"

    try:
        s3_client = boto3.client("s3", region_name=config.AWS_REGION)

        # Generate presigned PUT URL (expires in 15 minutes)
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": config.MEDIA_BUCKET,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=900,  # 15 minutes
        )

        # The final URL for referencing this media
        media_url = f"https://{config.MEDIA_BUCKET}.s3.{config.AWS_REGION}.amazonaws.com/{s3_key}"

        return response.success({
            "upload_url": presigned_url,
            "media_id": media_id,
            "media_url": media_url,
            "s3_key": s3_key,
            "expires_in": 900,
            "method": "PUT",
            "content_type": content_type,
            "max_file_size_bytes": config.UPLOAD_MAX_FILE_BYTES,
            "instructions": (
                "1. PUT the file body to upload_url with Content-Type header. "
                "2. Include media_url in POST /reports media_urls array."
            ),
        }, trace_id=trace_id)

    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}", exc_info=True)
        return response.internal_error("Failed to generate upload URL.", trace_id=trace_id)


# ---------------------------------------------------------------------------
# Trending Keywords computation
# ---------------------------------------------------------------------------

def _collect_reports_for_stats(dynamodb, timeframe: str, region: str | None) -> list[dict]:
    """Collect report items for stats/trending/heatmap calculations."""
    cutoff_iso = _timeframe_cutoff(timeframe).isoformat()
    statuses = [
        ValidationStatus.RECEIVED.value,
        ValidationStatus.PENDING_REVIEW.value,
        ValidationStatus.VERIFIED.value,
        ValidationStatus.SPAM.value,
        ValidationStatus.REJECTED.value,
        ValidationStatus.DUPLICATE.value,
    ]

    projection = (
        "report_id, validation_status, ai_analysis_tags, suggested_category, "
        "geo_location, ingested_at"
    )
    report_items: list[dict] = []

    for status in statuses:
        resp = dynamodb.query(
            TableName=config.REPORTS_TABLE,
            IndexName="gsi_status_ingested",
            KeyConditionExpression="validation_status = :status AND ingested_at >= :cutoff",
            ExpressionAttributeValues={
                ":status": {"S": status},
                ":cutoff": {"S": cutoff_iso},
            },
            ProjectionExpression=projection,
            ScanIndexForward=False,
            Limit=config.STATS_REPORT_SCAN_LIMIT,
        )

        for item in resp.get("Items", []):
            if region:
                geo = _parse_geo_from_item(item)
                if not geo or not _coordinates_in_region(geo[0], geo[1], region):
                    continue
            report_items.append(item)

    return report_items


def _timeframe_cutoff(timeframe: str) -> datetime:
    now = datetime.now(timezone.utc)
    if timeframe == "last_24h":
        return now - timedelta(hours=24)
    if timeframe == "last_7d":
        return now - timedelta(days=7)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _summarize_report_items(report_items: list[dict]) -> dict[str, int]:
    pending_review = 0
    verified_incidents = 0
    spam_rejected = 0

    for item in report_items:
        status = item.get("validation_status", {}).get("S", "")
        if status == ValidationStatus.PENDING_REVIEW.value:
            pending_review += 1
        elif status == ValidationStatus.VERIFIED.value:
            verified_incidents += 1
        elif status in (ValidationStatus.SPAM.value, ValidationStatus.REJECTED.value):
            spam_rejected += 1

    return {
        "total_received_today": len(report_items),
        "pending_review": pending_review,
        "verified_incidents": verified_incidents,
        "spam_rejected": spam_rejected,
    }


def _compute_trending_keywords(report_items: list[dict]) -> list[dict]:
    """Compute trending keywords from report ai_analysis_tags."""
    keyword_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}

    for item in report_items:
        tags = [t["S"] for t in item.get("ai_analysis_tags", {}).get("L", [])]
        for tag in tags:
            tag_lower = tag.lower().strip()
            if tag_lower and len(tag_lower) > 1:
                keyword_counts[tag_lower] = keyword_counts.get(tag_lower, 0) + 1

        cat = item.get("suggested_category", {}).get("S", "")
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    trending = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return [
        {"keyword": kw, "count": count, "category": _guess_category(kw, category_counts)}
        for kw, count in trending
    ]


def _compute_heatmap_data(report_items: list[dict]) -> list[dict]:
    """Aggregate report coordinates into simple geo buckets for dashboard heatmaps."""
    heatmap: dict[tuple[float, float], int] = {}

    for item in report_items:
        geo = _parse_geo_from_item(item)
        if not geo:
            continue

        lat, lon = geo
        # Bucket to ~1.1km cells for lightweight rendering.
        bucket_key = (round(lat, 2), round(lon, 2))
        heatmap[bucket_key] = heatmap.get(bucket_key, 0) + 1

    points = []
    for (lat, lon), count in heatmap.items():
        region = _resolve_region_for_point(lat, lon)
        points.append({
            "lat": lat,
            "lon": lon,
            "count": count,
            "region": region,
        })

    points.sort(key=lambda p: p["count"], reverse=True)
    return points[:50]


def _parse_geo_from_item(item: dict) -> tuple[float, float] | None:
    """Read lat/lon from a DynamoDB report item."""
    try:
        geo_m = item.get("geo_location", {}).get("M")
        if not geo_m:
            return None
        lat = float(geo_m["lat"]["N"])
        lon = float(geo_m["lon"]["N"])
        return lat, lon
    except Exception:
        return None


def _coordinates_in_region(lat: float, lon: float, region: str) -> bool:
    bounds = REGION_BOUNDARIES.get(region)
    if not bounds:
        return False

    lat_min, lat_max = bounds["lat"]
    lon_min, lon_max = bounds["lon"]
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def _resolve_region_for_point(lat: float, lon: float) -> str | None:
    for region_key in sorted(REGION_BOUNDARIES.keys()):
        if _coordinates_in_region(lat, lon, region_key):
            return region_key
    return None


def _guess_category(keyword: str, category_counts: dict[str, int]) -> str:
    """Guess the disaster category for a keyword based on common patterns."""
    kw = keyword.lower()
    category_map = {
        "fire": "FIRE", "smoke": "FIRE", "ไฟ": "FIRE", "ไฟไหม้": "FIRE",
        "flood": "FLOOD", "water": "FLOOD", "น้ำท่วม": "FLOOD", "น้ำ": "FLOOD",
        "earthquake": "EARTHQUAKE", "quake": "EARTHQUAKE", "แผ่นดินไหว": "EARTHQUAKE",
        "accident": "ACCIDENT", "crash": "ACCIDENT", "อุบัติเหตุ": "ACCIDENT",
    }
    return category_map.get(kw, max(category_counts, key=category_counts.get) if category_counts else "OTHER")


def _calculate_severity_level(report: Report) -> int:
    """Derive severity level (1-5) from category/tags/content signals."""
    category = (report.suggested_category or "").upper()
    tags_text = " ".join(report.ai_analysis_tags).lower()
    content_text = (report.raw_content or "").lower()
    combined = f"{tags_text} {content_text}"

    level = 1
    if category in {"FIRE", "FLOOD", "EARTHQUAKE", "SOS", "DAMAGE"}:
        level = max(level, 3)
    elif category == "ACCIDENT":
        level = max(level, 2)

    emergency_keywords = [
        "mass casualty", "many injured", "multiple dead", "ระเบิด", "ถล่มทั้งอาคาร",
    ]
    critical_keywords = [
        "trapped", "can't breathe", "help", "ติดอยู่", "หายใจไม่ออก", "ช่วยด้วย",
        "severe burn", "collapsed", "major fire",
    ]
    high_keywords = [
        "fire", "flood", "earthquake", "evacuation", "ไฟไหม้", "น้ำท่วม", "แผ่นดินไหว",
        "rescue", "injured", "อพยพ", "บาดเจ็บ",
    ]

    if any(k in combined for k in high_keywords):
        level = max(level, 3)
    if any(k in combined for k in critical_keywords):
        level = max(level, 4)
    if any(k in combined for k in emergency_keywords):
        level = max(level, 5)

    if report.trust_score >= 90 and level < 3:
        level = 3

    return max(1, min(level, 5))


def _calculate_reporter_count(dynamodb, report: Report) -> int:
    """Count unique reporters from current report and its potential duplicates."""
    reporter_ids: set[str] = set()
    if report.reporter_id:
        reporter_ids.add(report.reporter_id)

    duplicate_ids = report.potential_duplicates[:50]
    if not duplicate_ids:
        return max(1, len(reporter_ids))

    try:
        keys = [{"report_id": {"S": rid}} for rid in duplicate_ids]
        resp = dynamodb.batch_get_item(
            RequestItems={
                config.REPORTS_TABLE: {
                    "Keys": keys,
                    "ProjectionExpression": "report_id, reporter_id",
                },
            }
        )
        for item in resp.get("Responses", {}).get(config.REPORTS_TABLE, []):
            reporter_id = item.get("reporter_id", {}).get("S")
            if reporter_id:
                reporter_ids.add(reporter_id)
    except Exception as e:
        logger.warning(f"Could not calculate reporter_count from duplicates: {e}")

    return max(1, len(reporter_ids))


def _resolve_address_text(report: Report) -> str | None:
    """Resolve user-friendly address text from report coordinates."""
    if not report.geo_location:
        return None

    lat = report.geo_location.lat
    lon = report.geo_location.lon

    address = reverse_geocoding_service.reverse_geocode(lat, lon)
    region_key = _resolve_region_for_point(lat, lon)
    if region_key:
        region_label = str(REGION_BOUNDARIES[region_key]["label"])
        if address and region_label.lower() not in address.lower():
            return f"{address} ({region_label})"
        if address:
            return address
        return f"{region_label} (lat={lat:.5f}, lon={lon:.5f})"

    return address


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_api_base_url(event: dict) -> str:
    """Resolve API base URL from API Gateway event metadata."""
    headers = event.get("headers") or {}
    host = headers.get("Host") or headers.get("host")
    request_ctx = event.get("requestContext") or {}
    stage = request_ctx.get("stage")

    if host and stage:
        return f"https://{host}/{stage}/v1"
    return ""


def _format_rss_pub_date(timestamp_iso: str) -> str:
    """Convert ISO timestamp to RFC-2822 date for RSS pubDate."""
    try:
        return format_datetime(datetime.fromisoformat(timestamp_iso))
    except Exception:
        return format_datetime(datetime.now(timezone.utc))


def _build_changelog_rss_xml(api_base_url: str) -> str:
    """Build RSS 2.0 XML from static changelog entries."""
    feed_self_link = f"{api_base_url}/changelog.xml" if api_base_url else ""
    docs_link = f"{api_base_url}/openapi.json" if api_base_url else ""
    channel_pub_date = _format_rss_pub_date(datetime.now(timezone.utc).isoformat())

    item_xml_parts: list[str] = []
    for entry in CHANGELOG_ENTRIES:
        entry_link = (
            f"{api_base_url}/changelog.xml#{xml_escape(entry['id'])}"
            if api_base_url else f"#{xml_escape(entry['id'])}"
        )
        item_xml_parts.append(
            "\n".join([
                "    <item>",
                f"      <title>{xml_escape(entry['title'])}</title>",
                f"      <description>{xml_escape(entry['description'])}</description>",
                f"      <link>{entry_link}</link>",
                f"      <guid isPermaLink=\"false\">{xml_escape(entry['id'])}</guid>",
                f"      <pubDate>{_format_rss_pub_date(entry['published_at'])}</pubDate>",
                f"      <category>version:{xml_escape(entry['version'])}</category>",
                "    </item>",
            ])
        )

    return "\n".join([
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\">",
        "  <channel>",
        "    <title>Report Verify Service Changelog</title>",
        "    <description>Release and contract changes for API consumers</description>",
        f"    <link>{xml_escape(api_base_url) if api_base_url else ''}</link>",
        f"    <lastBuildDate>{channel_pub_date}</lastBuildDate>",
        "    <ttl>60</ttl>",
        f"    <docs>{xml_escape(docs_link)}</docs>",
        f"    <atom:link href=\"{xml_escape(feed_self_link)}\" rel=\"self\" type=\"application/rss+xml\" xmlns:atom=\"http://www.w3.org/2005/Atom\"/>",
        *item_xml_parts,
        "  </channel>",
        "</rss>",
    ])


def _handle_changelog_rss(event: dict, trace_id: str | None = None) -> dict:
    """Return changelog feed as RSS XML."""
    api_base_url = _resolve_api_base_url(event)
    xml_body = _build_changelog_rss_xml(api_base_url)
    return response.xml(xml_body, trace_id=trace_id)


# ---------------------------------------------------------------------------
# Deprecation Notes
# ---------------------------------------------------------------------------

# Registry of deprecated endpoints with sunset dates.
DEPRECATION_REGISTRY: list[dict[str, str]] = [
    {
        "endpoint": "GET /v0/reports (example)",
        "deprecated_since": "2026-04-01",
        "sunset_date": "2026-07-01",
        "migration_guide": "Use GET /v1/reports instead. See docs/VERSIONING_POLICY.md for details.",
        "status": "deprecated",
    },
]


def _handle_deprecation_info(trace_id: str | None = None) -> dict:
    """Return deprecation info for all endpoints, including active and upcoming sunsets."""
    active = [d for d in DEPRECATION_REGISTRY if d.get("status") == "deprecated"]
    sunset = [d for d in DEPRECATION_REGISTRY if d.get("status") == "sunset"]

    return response.success({
        "deprecation_policy_url": "docs/VERSIONING_POLICY.md",
        "changelog_url": "/v1/changelog.xml",
        "active_deprecations": active,
        "sunset_endpoints": sunset,
        "note": (
            "Deprecated endpoints return X-Deprecated-Version: true and "
            "X-Sunset-Date headers. Monitor these headers in your integration."
        ),
    }, trace_id=trace_id)


# ---------------------------------------------------------------------------
# Trace Lookup — search CloudWatch Logs by traceId
# ---------------------------------------------------------------------------

def _handle_trace_lookup(target_trace_id: str, trace_id: str | None = None) -> dict:
    """Search CloudWatch Logs for a given traceId across all Lambda log groups."""
    if not target_trace_id or len(target_trace_id) < 8:
        return response.bad_request("Invalid trace ID.", trace_id=trace_id)

    logs_client = boto3.client("logs", region_name=config.AWS_REGION)

    # Lambda function log groups to search
    prefix = config.REPORTS_TABLE.replace("-reports", "")
    log_groups = [
        f"/aws/lambda/{prefix}-api-handler",
        f"/aws/lambda/{prefix}-ingest-handler",
        f"/aws/lambda/{prefix}-ingestion-worker",
        f"/aws/lambda/{prefix}-health-handler",
    ]

    trace_results: list[dict] = []

    # CloudWatch filter patterns treat '-' as NOT operator.
    # Use only the first hex segment of UUID (8 chars, no hyphen) as filter term.
    cw_filter = target_trace_id.split("-")[0]

    for lg in log_groups:
        try:
            kwargs: dict = {
                "logGroupName": lg,
                "filterPattern": cw_filter,
                "limit": 50,
                "interleaved": True,
            }
            while len(trace_results) < 100:
                resp = logs_client.filter_log_events(**kwargs)
                for ev in resp.get("events", []):
                    trace_results.append({
                        "log_group": lg,
                        "timestamp": ev.get("timestamp"),
                        "message": (ev.get("message", ""))[:500],
                    })
                next_token = resp.get("nextToken")
                if not next_token:
                    break
                kwargs["nextToken"] = next_token
        except logs_client.exceptions.ResourceNotFoundException:
            continue
        except Exception as e:
            logger.warning(f"Trace search failed for {lg}: {e}")
            continue

    trace_results.sort(key=lambda x: x.get("timestamp", 0))

    return response.success({
        "target_trace_id": target_trace_id,
        "total_log_entries": len(trace_results),
        "log_groups_searched": log_groups,
        "results": trace_results[:50],
        "cloudwatch_insights_query": (
            f'fields @timestamp, @message | filter @message like "{target_trace_id}" '
            "| sort @timestamp asc | limit 100"
        ),
        "how_to_trace": {
            "step_1": "Copy the X-Trace-Id from any API response header or traceId from JSON body",
            "step_2": "Use GET /v1/reports/trace/{traceId} to search logs automatically",
            "step_3": "Or go to AWS CloudWatch → Logs Insights and run the query above",
            "step_4": "Select all Lambda log groups for this service to get the full request flow",
        },
    }, trace_id=trace_id)

def _parse_body(event: dict, trace_id: str | None = None) -> dict:
    """Parse JSON body from API Gateway event."""
    try:
        return json.loads(event.get("body", "{}") or "{}")
    except (json.JSONDecodeError, TypeError):
        return response.bad_request("Invalid JSON body.", trace_id=trace_id)


def _update_stat(dynamodb, stat_key: str, increment: int) -> None:
    """Atomic increment/decrement of a stats counter."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dynamodb.update_item(
            TableName=config.STATS_TABLE,
            Key={"stat_key": {"S": f"{today}#{stat_key}"}},
            UpdateExpression="ADD stat_value :inc",
            ExpressionAttributeValues={":inc": {"N": str(increment)}},
        )
    except Exception as e:
        logger.error(f"Failed to update stat '{stat_key}': {e}")
