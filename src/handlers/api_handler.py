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
from datetime import datetime, timezone
from typing import Any

import boto3

from src.config import config
from src.models.report import Report
from src.models.enums import ValidationStatus, VerificationAction
from src.services.audit_service import AuditService
from src.services.event_publisher import EventPublisher
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
                result = _handle_get_stats(query_params, dynamodb)
            else:
                result = _handle_list_reports(query_params, dynamodb)

        elif method == "GET" and "/stats" in path:
            result = _handle_get_stats(query_params, dynamodb)

        elif method == "GET" and path_params.get("report_id"):
            result = _handle_get_detail(path_params["report_id"], dynamodb)

        elif method == "PATCH" and path_params.get("report_id"):
            body = _parse_body(event)
            if isinstance(body, dict) and "error" in body:
                result = body  # Return parse error
            else:
                result = _handle_verify(path_params["report_id"], body, dynamodb)

        elif method == "DELETE" and path_params.get("report_id"):
            body = _parse_body(event)
            if isinstance(body, dict) and "error" in body:
                result = body
            else:
                result = _handle_delete(path_params["report_id"], body, dynamodb)

        elif method == "OPTIONS":
            result = response.success({"message": "CORS preflight OK"})

        else:
            result = response.not_found(f"No route for {method} {path}")

    except Exception as e:
        logger.error("Unhandled error in API handler", exc_info=True)
        result = response.internal_error(str(e))

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

def _handle_list_reports(query_params: dict, dynamodb) -> dict:
    """Query reports by status with optional trust score filter."""
    parsed, errors = validate_list_params(query_params)
    if errors:
        return response.bad_request("Invalid query parameters.", "; ".join(errors))

    status = parsed.get("status", ValidationStatus.PENDING_REVIEW.value)
    limit = parsed.get("limit", config.DEFAULT_PAGE_LIMIT)
    min_score = parsed.get("min_trust_score")

    try:
        expr_values: dict[str, Any] = {
            ":status": {"S": status},
        }
        filter_expr = None

        if min_score is not None:
            filter_expr = "trust_score >= :min_score"
            expr_values[":min_score"] = {"N": str(min_score)}

        resp = dynamodb.query(
            TableName=config.REPORTS_TABLE,
            IndexName="gsi_status_ingested",
            KeyConditionExpression="validation_status = :status",
            ExpressionAttributeValues=expr_values,
            FilterExpression=filter_expr,
            ScanIndexForward=False,  # newest first
            Limit=limit,
        )

        items = resp.get("Items", [])
        reports = [Report.from_dynamodb_item(item).to_api_summary() for item in items]

        return response.success({
            "data": reports,
            "total_count": resp.get("Count", 0),
        })

    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        return response.internal_error("Failed to retrieve reports.")


# ---------------------------------------------------------------------------
# GET /reports/{report_id} — Report detail (API Contract #4)
# ---------------------------------------------------------------------------

def _handle_get_detail(report_id: str, dynamodb) -> dict:
    """Get full report detail by ID."""
    try:
        resp = dynamodb.get_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": report_id}},
        )

        item = resp.get("Item")
        if not item:
            return response.not_found(f"Report '{report_id}' not found.")

        report = Report.from_dynamodb_item(item)

        # Don't show DELETED reports
        if report.validation_status == ValidationStatus.DELETED.value:
            return response.not_found(f"Report '{report_id}' not found.")

        return response.success(report.to_api_detail())

    except Exception as e:
        logger.error(f"Error getting report detail: {e}", exc_info=True)
        return response.internal_error("Failed to retrieve report.")


# ---------------------------------------------------------------------------
# PATCH /reports/{report_id} — Verify/Reject (API Contract #3)
# ---------------------------------------------------------------------------

def _handle_verify(report_id: str, body: dict, dynamodb) -> dict:
    """Process verification decision from Trust Officer."""
    errors = validate_verify_payload(body)
    if errors:
        return response.bad_request("Validation failed.", "; ".join(errors))

    new_status = body["validation_status"]

    # Fetch current report
    try:
        resp = dynamodb.get_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": report_id}},
        )
        item = resp.get("Item")
        if not item:
            return response.not_found(f"Report '{report_id}' not found.")

        current_status = item["validation_status"]["S"]
    except Exception as e:
        logger.error(f"Error fetching report for verify: {e}", exc_info=True)
        return response.internal_error("Failed to retrieve report.")

    # Validate transition
    transition_error = validate_status_transition(current_status, new_status)
    if transition_error:
        return response.conflict(transition_error)

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
            "Report has been modified by another user. Please refresh and try again."
        )
    except Exception as e:
        logger.error(f"Error updating report status: {e}", exc_info=True)
        return response.internal_error("Failed to update report.")

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
        incident_data = {
            "type": report.suggested_category or "OTHER",
            "description": report.raw_content[:500],
            "severity_level": 3,  # TODO: compute from AI tags
            "location": report.geo_location.to_dict() if report.geo_location else None,
            "reporter_count": 1,
            "media_evidence": report.media_urls,
        }
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
    })


# ---------------------------------------------------------------------------
# DELETE /reports/{report_id} — Soft delete (API Contract #6)
# ---------------------------------------------------------------------------

def _handle_delete(report_id: str, body: dict, dynamodb) -> dict:
    """Soft-delete (archive) a report."""
    errors = validate_delete_payload(body)
    if errors:
        return response.bad_request("Validation failed.", "; ".join(errors))

    # Check report exists
    try:
        resp = dynamodb.get_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": report_id}},
            ProjectionExpression="report_id, validation_status",
        )
        item = resp.get("Item")
        if not item:
            return response.not_found(f"Report '{report_id}' not found.")

        if item["validation_status"]["S"] == ValidationStatus.DELETED.value:
            return response.not_found(f"Report '{report_id}' not found.")

    except Exception as e:
        logger.error(f"Error checking report for delete: {e}", exc_info=True)
        return response.internal_error("Failed to check report.")

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
        return response.internal_error("Failed to delete report.")

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
    })


# ---------------------------------------------------------------------------
# GET /reports/stats — Dashboard stats (API Contract #5)
# ---------------------------------------------------------------------------

def _handle_get_stats(query_params: dict, dynamodb) -> dict:
    """Get aggregated dashboard statistics from the StatsCounter table."""
    parsed, errors = validate_stats_params(query_params)
    if errors:
        return response.bad_request("Invalid parameters.", "; ".join(errors))

    timeframe = parsed.get("timeframe", "today")

    try:
        # Determine date prefix for stats lookup
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        stat_keys = [
            f"{today}#total_received",
            f"{today}#pending_review",
            f"{today}#verified_incidents",
            f"{today}#spam_rejected",
            f"{today}#duplicates",
        ]

        # Batch get stats
        keys = [{"stat_key": {"S": k}} for k in stat_keys]
        resp = dynamodb.batch_get_item(
            RequestItems={
                config.STATS_TABLE: {
                    "Keys": keys,
                    "ProjectionExpression": "stat_key, stat_value",
                },
            },
        )

        stats_map: dict[str, int] = {}
        for item in resp.get("Responses", {}).get(config.STATS_TABLE, []):
            key = item["stat_key"]["S"].split("#", 1)[-1]
            stats_map[key] = int(item.get("stat_value", {}).get("N", 0))

        return response.success({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_received_today": stats_map.get("total_received", 0),
                "pending_review": stats_map.get("pending_review", 0),
                "verified_incidents": stats_map.get("verified_incidents", 0),
                "spam_rejected": stats_map.get("spam_rejected", 0),
            },
            "trending_keywords": [],  # TODO: implement keyword tracking
            "heatmap_data": [],       # TODO: implement from geo_location aggregation
        })

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return response.internal_error("Failed to compute statistics.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_body(event: dict) -> dict:
    """Parse JSON body from API Gateway event."""
    try:
        return json.loads(event.get("body", "{}") or "{}")
    except (json.JSONDecodeError, TypeError):
        return response.bad_request("Invalid JSON body.")


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
