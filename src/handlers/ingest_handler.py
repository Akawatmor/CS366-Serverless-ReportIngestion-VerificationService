"""
Ingest Handler — Lambda behind POST /reports.

Fallback handler in case API Gateway → SQS direct integration is not used.
Validates the incoming payload and forwards it to the SQS ingestion queue.
Responds immediately with 202 Accepted (fire-and-forget pattern).
"""
from __future__ import annotations

import json
import uuid
import time
from datetime import datetime, timezone

import boto3

from src.config import config
from src.models.report import GeoLocation, Report
from src.utils.logger import get_logger
from src.utils import response
from src.utils.validators import validate_ingest_payload

logger = get_logger(__name__)


def _build_sensor_summary(sensor_data: dict) -> str:
    """Create readable fallback text for structured sensor alerts."""
    metric_name = str(sensor_data.get("metric_name") or "sensor metric")
    metric_value = sensor_data.get("metric_value")
    unit = str(sensor_data.get("unit") or "").strip()
    threshold = sensor_data.get("threshold")
    sensor_id = str(sensor_data.get("sensor_id") or "").strip()
    site_id = str(sensor_data.get("site_id") or "").strip()
    status = str(sensor_data.get("status") or "").strip()

    value_text = f"{metric_value} {unit}".strip() if metric_value is not None else "unknown"
    parts = [f"Sensor alert for {metric_name}: {value_text}"]
    if threshold is not None:
        parts.append(f"threshold {threshold}")
    if status:
        parts.append(f"status {status}")
    if sensor_id:
        parts.append(f"sensor {sensor_id}")
    if site_id:
        parts.append(f"site {site_id}")
    return ", ".join(parts)


def _build_placeholder_report(
    report_id: str,
    body: dict,
    raw_content: str,
    ingested_at: str,
    event_timestamp: str,
) -> Report:
    """Create the placeholder report persisted before async AI processing starts."""
    geo = body.get("geo_location") or {}
    geo_location = None
    if geo.get("lat") is not None and geo.get("lon") is not None:
        geo_location = GeoLocation(lat=float(geo["lat"]), lon=float(geo["lon"]))

    return Report(
        report_id=report_id,
        source_platform=body["reporter_source"],
        source_external_id=body.get("source_external_id"),
        reporter_id=body["reporter_id"],
        raw_content=raw_content,
        media_urls=body.get("media_urls", []),
        sensor_data=body.get("sensor_data"),
        geo_location=geo_location,
        event_timestamp=event_timestamp,
        ingested_at=ingested_at,
    )


def handler(event: dict, context) -> dict:
    """
    API Gateway Proxy integration handler for POST /reports.

    Flow:
      1. Parse and validate JSON body
      2. Generate report_id (UUID)
      3. Send message to SQS ingestion queue
      4. Return 202 Accepted with report_id
    """
    start = time.time()
    request_id = context.aws_request_id if context else str(uuid.uuid4())

    logger.info("Ingest request received", extra={
        "request_id": request_id,
        "data": {"path": "/reports", "method": "POST"},
    })

    # --- Parse body ---
    try:
        body = json.loads(event.get("body", "{}") or "{}")
    except (json.JSONDecodeError, TypeError):
        return response.bad_request("Invalid JSON body.", trace_id=request_id)

    # --- Check payload size ---
    raw_body = event.get("body", "")
    if len(raw_body.encode("utf-8")) > config.MAX_PAYLOAD_BYTES:
        return response.bad_request(
            f"Payload exceeds maximum size of {config.MAX_PAYLOAD_BYTES // 1024}KB.",
            trace_id=request_id,
        )

    # --- Validate ---
    errors = validate_ingest_payload(body)
    if errors:
        return response.bad_request("Validation failed.", detail="; ".join(errors), trace_id=request_id)

    # --- Generate report_id ---
    report_id = f"r-{uuid.uuid4().hex[:12]}"

    # --- Build SQS message ---
    sensor_data = body.get("sensor_data")
    raw_content = body.get("raw_content", "")
    if not raw_content and isinstance(sensor_data, dict) and sensor_data:
        raw_content = _build_sensor_summary(sensor_data)

    ingested_at = datetime.now(timezone.utc).isoformat()
    event_timestamp = body.get("timestamp", ingested_at)

    sqs_message = {
        "report_id": report_id,
        "reporter_source": body["reporter_source"],
        "reporter_id": body["reporter_id"],
        "raw_content": raw_content,
        "media_urls": body.get("media_urls", []),
        "sensor_data": sensor_data,
        "geo_location": body.get("geo_location"),
        "timestamp": event_timestamp,
        "source_external_id": body.get("source_external_id"),
        "ingested_at": ingested_at,
    }

    # --- Persist placeholder report before async analysis ---
    dynamodb = boto3.client("dynamodb", region_name=config.AWS_REGION)
    placeholder_report = _build_placeholder_report(
        report_id=report_id,
        body=body,
        raw_content=raw_content,
        ingested_at=ingested_at,
        event_timestamp=event_timestamp,
    )

    try:
        dynamodb.put_item(
            TableName=config.REPORTS_TABLE,
            Item=placeholder_report.to_dynamodb_item(),
            ConditionExpression="attribute_not_exists(report_id)",
        )
    except Exception as e:
        logger.error("Failed to persist queued report", extra={
            "request_id": request_id,
            "data": {"error": str(e), "report_id": report_id},
        })
        return response.internal_error("Failed to create report record.", trace_id=request_id)

    # --- Send to SQS ---
    try:
        sqs = boto3.client("sqs", region_name=config.AWS_REGION)
        sqs.send_message(
            QueueUrl=config.SQS_QUEUE_URL,
            MessageBody=json.dumps(sqs_message, ensure_ascii=False, default=str),
            MessageAttributes={
                "source": {
                    "DataType": "String",
                    "StringValue": body["reporter_source"],
                },
            },
        )
    except Exception as e:
        logger.error("Failed to enqueue report", extra={
            "request_id": request_id,
            "data": {"error": str(e), "report_id": report_id},
        })

        try:
            dynamodb.delete_item(
                TableName=config.REPORTS_TABLE,
                Key={"report_id": {"S": report_id}},
            )
        except Exception as cleanup_error:
            logger.error("Failed to delete queued placeholder report", extra={
                "request_id": request_id,
                "data": {
                    "error": str(cleanup_error),
                    "report_id": report_id,
                },
            })

        return response.internal_error("Failed to queue report for processing.", trace_id=request_id)

    duration_ms = int((time.time() - start) * 1000)
    logger.info("Report queued", extra={
        "request_id": request_id,
        "data": {"report_id": report_id, "duration_ms": duration_ms},
    })

    return response.accepted({
        "status": "QUEUED",
        "report_id": report_id,
        "message": "Report accepted and queued for processing.",
        "estimated_wait_time": "2s",
        "traceId": request_id,
    }, trace_id=request_id)
