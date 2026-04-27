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

    # --- 2a. Fetch reporter history for Gemini context and Python scoring ---
    reporter_history_str, reporter_history_stats = _get_reporter_history(
        dynamodb, body.get("reporter_id", "")
    )

    # --- 2b. Rate-limit check: ≥ RATE_LIMIT_THRESHOLD reports in window → force SPAM ---
    if reporter_history_stats["recent_count"] >= config.HISTORY_RATE_LIMIT_THRESHOLD:
        logger.warning(
            "Rate-limit detected — forcing SPAM status",
            extra={"data": {
                "report_id": report_id,
                "recent_count": reporter_history_stats["recent_count"],
            }},
        )
        ai_result = {
            "content_score": 0,
            "content_score_reasoning": "Rate-limited: too many reports in short window.",
            "suggested_category": "OTHER",
            "keywords": [],
            "spam_signals": ["rate_limited"],
            "is_spam_likely": True,
            "ai_analysis_failed": False,
            "vision_used": False,
        }
    else:
        ai_result = gemini_service.analyze_report(
            content=body.get("raw_content", ""),
            source=body.get("reporter_source", ""),
            reporter_id=body.get("reporter_id", ""),
            lat=geo.get("lat"),
            lon=geo.get("lon"),
            timestamp=body.get("timestamp", ""),
            media_urls=body.get("media_urls", []),
            reporter_history=reporter_history_str,
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
    trust_score = compute_trust_score(ai_result, body, reporter_history_stats)
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
        ai_reasoning=ai_result.get("content_score_reasoning", ""),
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
            reason=ai_result.get("content_score_reasoning", "Auto-processed by AI"),
        )

    # --- 9. Audit log ---
    audit_svc.log_ai_analysis(report_id, ai_result)
    if initial_status != ValidationStatus.RECEIVED.value:
        audit_svc.log_status_change(
            report_id=report_id,
            actor_id="SYSTEM_AI",
            old_status=ValidationStatus.RECEIVED.value,
            new_status=initial_status,
            notes=ai_result.get("content_score_reasoning", ""),
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


def compute_trust_score(
    ai_result: dict,
    body: dict,
    reporter_history_stats: dict,
) -> int:
    """
    Assemble final trust score from deterministic components.

    Components (total 100):
      Component 1 — Content quality   : 0-30  (from Gemini)
      Component 2 — Source platform   : 0-20  (fixed table)
      Component 3 — Reporter history  : 0-20  (Python rules)
      Component 4 — Media evidence    : 0-20  (partially from Gemini vision)
      Component 5 — Geographic data   : 0-10  (presence of lat/lon)
    """
    score = 0

    # Component 1 — Content quality (Gemini)
    score += max(0, min(30, ai_result.get("content_score", 15)))

    # Component 2 — Source platform (deterministic)
    source = (body.get("reporter_source") or "").upper()
    score += config.SOURCE_SCORES.get(source, config.SOURCE_SCORE_DEFAULT)

    # Component 3 — Reporter history (Python rules)
    score += _reporter_history_score(reporter_history_stats)

    # Component 4 — Media evidence
    media_urls = body.get("media_urls") or []
    if ai_result.get("vision_used"):
        # Vision prompt already examined the image
        image_score = ai_result.get("image_score", 0)
        score += image_score
    elif media_urls:
        # Media present but not analysed visually — partial credit
        score += 8

    # Component 5 — Geographic data
    geo = body.get("geo_location") or {}
    if geo.get("lat") and geo.get("lon"):
        score += 10

    return max(0, min(100, score))


def _reporter_history_score(stats: dict) -> int:
    """
    Compute Component 3 (0-20) from structured reporter history stats.

    stats keys expected:
      total       (int)  — total prior reports
      verified    (int)  — reports with VERIFIED status
      spam        (int)  — reports with SPAM status
      recent_count (int) — reports in the last RATE_LIMIT_WINDOW_MINUTES
    """
    total = stats.get("total", 0)

    if total == 0:
        # First-time reporter
        return config.HISTORY_BASE_SCORE

    score = config.HISTORY_BASE_SCORE
    # Bonus for established verified reporters
    if stats.get("verified", 0) >= 3:
        score += config.HISTORY_VERIFIED_BONUS
    # Penalty per spam record
    spam_count = stats.get("spam", 0)
    score -= spam_count * config.HISTORY_SPAM_PENALTY

    return max(0, min(20, score))


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


def _get_reporter_history(dynamodb, reporter_id: str) -> tuple[str, dict]:
    """
    Fetch past reports for reporter_id.

    Returns:
        (history_str, stats_dict) where:
          history_str  — human-readable summary for Gemini prompt
          stats_dict   — structured dict for compute_trust_score():
                          total, verified, spam, recent_count
    """
    _empty_stats = {"total": 0, "verified": 0, "spam": 0, "recent_count": 0}

    if not reporter_id:
        return "No reporter_id provided.", _empty_stats

    try:
        resp = dynamodb.query(
            TableName=config.REPORTS_TABLE,
            IndexName="gsi_reporter",
            KeyConditionExpression="reporter_id = :rid",
            ExpressionAttributeValues={":rid": {"S": reporter_id}},
            ProjectionExpression="report_id, validation_status, trust_score, ingested_at",
            ScanIndexForward=False,
            Limit=20,
        )

        items = resp.get("Items", [])
        if not items:
            return "First-time reporter \u2014 no previous reports found.", _empty_stats

        from datetime import timedelta
        now = datetime.now(timezone.utc)
        rate_limit_cutoff = now - timedelta(minutes=config.HISTORY_RATE_LIMIT_WINDOW_MINUTES)

        total = len(items)
        status_counts: dict[str, int] = {}
        scores: list[int] = []
        recent_count = 0

        for item in items:
            status = item.get("validation_status", {}).get("S", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

            score_val = item.get("trust_score", {}).get("N")
            if score_val:
                scores.append(int(score_val))

            ingested_at_str = item.get("ingested_at", {}).get("S", "")
            if ingested_at_str:
                try:
                    ingested_at = datetime.fromisoformat(
                        ingested_at_str.replace("Z", "+00:00")
                    )
                    if ingested_at >= rate_limit_cutoff:
                        recent_count += 1
                except ValueError:
                    pass

        avg_score = sum(scores) // len(scores) if scores else 0
        status_summary = ", ".join(f"{s}: {c}" for s, c in status_counts.items())

        history_str = (
            f"Reporter has {total} prior report(s) (showing up to 20). "
            f"Status breakdown: {status_summary}. "
            f"Average trust score: {avg_score}/100."
        )

        stats_dict = {
            "total": total,
            "verified": status_counts.get("VERIFIED", 0),
            "spam": status_counts.get("SPAM", 0),
            "recent_count": recent_count,
        }

        return history_str, stats_dict

    except Exception as e:
        logger.warning(f"Could not fetch reporter history: {e}")
        return "Reporter history unavailable.", _empty_stats
