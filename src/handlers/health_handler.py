"""
Health Check Handler — GET /health

Checks connectivity to all critical dependencies:
  - DynamoDB (Reports Table)
  - SQS (Ingestion Queue)
  - Gemini AI (API reachability)
  - EventBridge (Event Bus)

Returns overall status: healthy / degraded / unhealthy
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import boto3

from src.config import config
from src.services.gemini_service import gemini_service
from src.services.event_publisher import EventPublisher
from src.utils.logger import get_logger
from src.utils import response

logger = get_logger(__name__)


def handler(event: dict, context) -> dict:
    """
    Health check endpoint — no authentication required.
    Returns component-level health status.
    """
    import uuid
    request_id = context.aws_request_id if context else str(uuid.uuid4())
    
    start = time.time()
    components: dict[str, dict] = {}
    overall = "healthy"

    # --- Run all checks concurrently ---
    checks = {
        "dynamodb": _check_dynamodb,
        "sqs": _check_sqs,
        "gemini": _check_gemini,
        "eventbridge": _check_eventbridge,
    }
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn): name for name, fn in checks.items()}
        for future in as_completed(futures):
            components[futures[future]] = future.result()

    # --- Determine overall status ---
    statuses = [c.get("status") for c in components.values()]
    critical_components = ["dynamodb", "sqs"]

    for name in critical_components:
        if components[name].get("status") != "healthy":
            overall = "unhealthy"
            break

    if overall == "healthy" and any(s != "healthy" for s in statuses):
        overall = "degraded"

    duration_ms = int((time.time() - start) * 1000)

    body = {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "components": components,
        "version": "1.0.0",
        "traceId": request_id,
    }

    status_code = 200 if overall != "unhealthy" else 503
    return response.success(body, status_code=status_code, trace_id=request_id)


def _check_dynamodb() -> dict:
    """Verify DynamoDB table is accessible."""
    try:
        dynamodb = boto3.client("dynamodb", region_name=config.AWS_REGION)
        resp = dynamodb.describe_table(TableName=config.REPORTS_TABLE)
        status = resp["Table"]["TableStatus"]
        return {
            "status": "healthy" if status == "ACTIVE" else "degraded",
            "table": config.REPORTS_TABLE,
            "table_status": status,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def _check_sqs() -> dict:
    """Verify SQS queue is reachable."""
    if not config.SQS_QUEUE_URL:
        return {"status": "unhealthy", "error": "SQS_QUEUE_URL not configured"}

    try:
        sqs = boto3.client("sqs", region_name=config.AWS_REGION)
        resp = sqs.get_queue_attributes(
            QueueUrl=config.SQS_QUEUE_URL,
            AttributeNames=["ApproximateNumberOfMessages"],
        )
        msg_count = resp["Attributes"].get("ApproximateNumberOfMessages", "0")
        return {
            "status": "healthy",
            "queue_url": config.SQS_QUEUE_URL,
            "approximate_messages": int(msg_count),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def _check_gemini() -> dict:
    """Check Gemini API reachability (non-critical)."""
    if not config.GEMINI_API_KEY:
        return {"status": "degraded", "error": "GEMINI_API_KEY not configured"}
    return gemini_service.health_check()


def _check_eventbridge() -> dict:
    """Check EventBridge bus exists."""
    publisher = EventPublisher()
    return publisher.health_check()
