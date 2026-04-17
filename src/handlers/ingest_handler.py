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
from src.utils.logger import get_logger
from src.utils import response
from src.utils.validators import validate_ingest_payload

logger = get_logger(__name__)


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
    sqs_message = {
        "report_id": report_id,
        "reporter_source": body["reporter_source"],
        "reporter_id": body["reporter_id"],
        "raw_content": body.get("raw_content", ""),
        "media_urls": body.get("media_urls", []),
        "geo_location": body.get("geo_location"),
        "timestamp": body.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "source_external_id": body.get("source_external_id"),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }

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
