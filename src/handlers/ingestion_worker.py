"""
Ingestion Worker — SQS-triggered Lambda that processes raw reports.

Flow per message:
  1. Parse SQS record body
  2. Idempotency check (source_external_id)
  3. Call Gemini AI for trust scoring
  4. Deduplication check (geo + time)
  5. Determine initial status based on trust_score
  6. Write report to DynamoDB
  7. Update stats counters
  8. Publish ReportStatusChangedEvent if auto-rejected
  9. Write audit log
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import boto3

from src.config import config
from src.models.report import Report, GeoLocation
from src.models.enums import ValidationStatus, SEVERITY_KEYWORDS
from src.services.gemini_service import gemini_service
from src.services.dedup_service import DedupService
from src.services.audit_service import AuditService
from src.services.event_publisher import EventPublisher
from src.utils.logger import get_logger

logger = get_logger(__name__)


def handler(event: dict, context) -> dict:
    """
    SQS batch event handler.
    Processes each record independently — partial batch failure supported.
    """
    failed_ids: list[str] = []
    dynamodb = boto3.client("dynamodb", region_name=config.AWS_REGION)
    dedup_svc = DedupService(dynamodb_client=dynamodb)
    audit_svc = AuditService(dynamodb_client=dynamodb)
    event_pub = EventPublisher()

    records = event.get("Records", [])
    logger.info(f"Processing batch of {len(records)} records")

    for record in records:
        message_id = record.get("messageId", "unknown")
        try:
            body = json.loads(record["body"])
            _process_single_report(body, dynamodb, dedup_svc, audit_svc, event_pub)
        except Exception as e:
            logger.error(
                "Failed to process SQS record",
                extra={"data": {"messageId": message_id, "error": str(e)}},
            )
            failed_ids.append(message_id)

    # Return partial batch failure response
    if failed_ids:
        return {
            "batchItemFailures": [
                {"itemIdentifier": mid} for mid in failed_ids
            ]
        }
    return {"batchItemFailures": []}


def _process_single_report(
    body: dict[str, Any],
    dynamodb,
    dedup_svc: DedupService,
    audit_svc: AuditService,
    event_pub: EventPublisher,
) -> None:
    """Process one raw report from the SQS message body."""
    start = time.time()
    report_id = body["report_id"]

    logger.info("Processing report", extra={"data": {"report_id": report_id}})

    # --- 1. Idempotency check ---
    existing_id = dedup_svc.check_external_id(body.get("source_external_id"))
    if existing_id:
        logger.info(
            "Skipping duplicate (external_id match)",
            extra={"data": {"report_id": report_id, "existing": existing_id}},
        )
        return

    # --- 2. Call Gemini AI for trust scoring ---
    geo = body.get("geo_location") or {}

    # --- 2a. Fetch reporter history for enhanced SPAM detection ---
    reporter_history = _get_reporter_history(dynamodb, body.get("reporter_id", ""))

    ai_result = gemini_service.analyze_report(
        content=body.get("raw_content", ""),
        source=body.get("reporter_source", ""),
        reporter_id=body.get("reporter_id", ""),
        lat=geo.get("lat"),
        lon=geo.get("lon"),
        timestamp=body.get("timestamp", ""),
        media_urls=body.get("media_urls", []),
        reporter_history=reporter_history,
    )

    # --- 3. Deduplication (geo + time) ---
    potential_duplicates: list[str] = []
    if geo.get("lat") and geo.get("lon"):
        potential_duplicates = dedup_svc.find_nearby_reports(
            lat=float(geo["lat"]),
            lon=float(geo["lon"]),
            event_time=body.get("timestamp"),
        )

    # Add text similarity dedup even when geo is missing/noisy.
    similar_by_content = dedup_svc.find_content_similar_reports(
        raw_content=body.get("raw_content", ""),
        event_time=body.get("timestamp"),
    )
    potential_duplicates = list(dict.fromkeys(potential_duplicates + similar_by_content))

    # --- 4. Determine initial status ---
    trust_score = ai_result["trust_score"]
    initial_status = _determine_status(trust_score, ai_result, potential_duplicates, body)
    priority = _determine_priority(trust_score, body.get("raw_content", ""), ai_result)

    # --- 5. Build Report object ---
    geo_location = None
    if geo.get("lat") and geo.get("lon"):
        geo_location = GeoLocation(lat=float(geo["lat"]), lon=float(geo["lon"]))

    report = Report(
        report_id=report_id,
        source_platform=body.get("reporter_source", "OFFICIAL_APP"),
        source_external_id=body.get("source_external_id"),
        reporter_id=body.get("reporter_id", ""),
        raw_content=body.get("raw_content", ""),
        media_urls=body.get("media_urls", []),
        geo_location=geo_location,
        event_timestamp=body.get("timestamp"),
        ingested_at=body.get("ingested_at", datetime.now(timezone.utc).isoformat()),
        trust_score=trust_score,
        ai_analysis_tags=ai_result.get("keywords", []),
        ai_reasoning=ai_result.get("reasoning", ""),
        suggested_category=ai_result.get("suggested_category", "OTHER"),
        ai_analysis_failed=ai_result.get("ai_analysis_failed", False),
        priority=priority,
        validation_status=initial_status,
        potential_duplicates=potential_duplicates,
    )

    # --- 6. Write to DynamoDB ---
    dynamodb.put_item(
        TableName=config.REPORTS_TABLE,
        Item=report.to_dynamodb_item(),
    )

    # --- 7. Update stats counter ---
    _increment_stat(dynamodb, "total_received")
    if initial_status == ValidationStatus.SPAM.value:
        _increment_stat(dynamodb, "spam_rejected")
    elif initial_status == ValidationStatus.DUPLICATE.value:
        _increment_stat(dynamodb, "duplicates")
    elif initial_status == ValidationStatus.PENDING_REVIEW.value:
        _increment_stat(dynamodb, "pending_review")

    # --- 8. Publish status change event if auto-processed ---
    if initial_status != ValidationStatus.PENDING_REVIEW.value:
        event_pub.publish_status_changed(
            report_id=report_id,
            old_status=ValidationStatus.RECEIVED.value,
            new_status=initial_status,
            changed_by="SYSTEM_AI",
            reason=ai_result.get("reasoning", "Auto-processed by AI"),
        )

    # --- 9. Audit log ---
    audit_svc.log_ai_analysis(report_id, ai_result)
    if initial_status != ValidationStatus.RECEIVED.value:
        audit_svc.log_status_change(
            report_id=report_id,
            actor_id="SYSTEM_AI",
            old_status=ValidationStatus.RECEIVED.value,
            new_status=initial_status,
            notes=ai_result.get("reasoning", ""),
        )

    duration_ms = int((time.time() - start) * 1000)
    logger.info(
        "Report processed",
        extra={"data": {
            "report_id": report_id,
            "status": initial_status,
            "trust_score": trust_score,
            "duration_ms": duration_ms,
        }},
    )


def _determine_status(
    trust_score: int,
    ai_result: dict,
    duplicates: list[str],
    body: dict,
) -> str:
    """
    Decide initial validation_status based on business rules:
      - trust_score < TRUST_AUTO_REJECT (30%) → SPAM
      - Duplicates detected → DUPLICATE
      - Otherwise → PENDING_REVIEW
      - Severity keywords → still PENDING_REVIEW but flagged for priority
    """
    if ai_result.get("is_spam_likely") and trust_score < config.TRUST_AUTO_REJECT:
        return ValidationStatus.SPAM.value

    if trust_score < config.TRUST_AUTO_REJECT:
        return ValidationStatus.SPAM.value

    if duplicates:
        return ValidationStatus.DUPLICATE.value

    return ValidationStatus.PENDING_REVIEW.value


def _determine_priority(trust_score: int, raw_content: str, ai_result: dict) -> int:
    """Return 1 for high-priority reports, otherwise 0."""
    if trust_score >= config.TRUST_HIGH_PRIORITY:
        return 1

    tags = " ".join(ai_result.get("keywords", []))
    if _has_severity_keywords(raw_content) or _has_severity_keywords(tags):
        return 1

    category = (ai_result.get("suggested_category") or "").upper()
    if category in {"FIRE", "FLOOD", "EARTHQUAKE", "SOS"} and trust_score >= 60:
        return 1

    return 0


def _has_severity_keywords(content: str) -> bool:
    """Check if content contains any high-severity keywords."""
    content_lower = content.lower()
    return any(kw.lower() in content_lower for kw in SEVERITY_KEYWORDS)


def _increment_stat(dynamodb, stat_key: str) -> None:
    """Atomic increment of a stats counter in the StatsCounter table."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dynamodb.update_item(
            TableName=config.STATS_TABLE,
            Key={"stat_key": {"S": f"{today}#{stat_key}"}},
            UpdateExpression="ADD stat_value :inc",
            ExpressionAttributeValues={":inc": {"N": "1"}},
        )
    except Exception as e:
        logger.error(f"Failed to update stat counter: {e}")


def _get_reporter_history(dynamodb, reporter_id: str) -> str:
    """
    Fetch past reports from the same reporter_id to provide historical
    context for SPAM detection. Returns a human-readable summary string.
    """
    if not reporter_id:
        return "No reporter_id provided."

    try:
        resp = dynamodb.query(
            TableName=config.REPORTS_TABLE,
            IndexName="gsi_reporter",
            KeyConditionExpression="reporter_id = :rid",
            ExpressionAttributeValues={":rid": {"S": reporter_id}},
            ProjectionExpression="report_id, validation_status, trust_score, ingested_at",
            ScanIndexForward=False,
            Limit=10,
        )

        items = resp.get("Items", [])
        if not items:
            return "First-time reporter — no previous reports found."

        total = len(items)
        status_counts: dict[str, int] = {}
        scores: list[int] = []

        for item in items:
            status = item.get("validation_status", {}).get("S", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
            score = item.get("trust_score", {}).get("N")
            if score:
                scores.append(int(score))

        avg_score = sum(scores) // len(scores) if scores else 0
        status_summary = ", ".join(f"{s}: {c}" for s, c in status_counts.items())

        return (
            f"Reporter has {total} prior report(s) (showing up to 10). "
            f"Status breakdown: {status_summary}. "
            f"Average trust score: {avg_score}/100."
        )
    except Exception as e:
        logger.warning(f"Could not fetch reporter history: {e}")
        return "Reporter history unavailable."
