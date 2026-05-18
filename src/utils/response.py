"""
Standardised API response builder — ensures every Lambda response
follows the same shape expected by API Gateway (proxy integration).

Features:
  - X-Trace-Id header for request tracing across services
  - Structured error responses with traceId, errorCode, timestamp
  - Deprecation headers for API versioning (X-Deprecated-Version, X-Sunset-Date)
"""
import json
from datetime import datetime, timezone
from typing import Any


def _build_headers(trace_id: str | None = None, deprecated: bool = False, sunset_date: str | None = None) -> dict:
    """Build response headers with optional tracing and deprecation info."""
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Api-Key, X-Trace-Id",
        "Access-Control-Expose-Headers": "X-Trace-Id, X-Deprecated-Version, X-Sunset-Date",
    }
    if trace_id:
        headers["X-Trace-Id"] = trace_id
    if deprecated:
        headers["X-Deprecated-Version"] = "true"
    if sunset_date:
        headers["X-Sunset-Date"] = sunset_date
    return headers


# Keep for backward compatibility
CORS_HEADERS = _build_headers()


def success(
    body: Any,
    status_code: int = 200,
    trace_id: str | None = None,
    deprecated: bool = False,
    sunset_date: str | None = None,
) -> dict:
    """Return a successful API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": _build_headers(trace_id, deprecated=deprecated, sunset_date=sunset_date),
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def raw(
    body: str,
    status_code: int = 200,
    content_type: str = "text/plain; charset=utf-8",
    trace_id: str | None = None,
) -> dict:
    """Return a raw (non-JSON) API Gateway response."""
    headers = _build_headers(trace_id)
    headers["Content-Type"] = content_type
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": body,
    }


def xml(body: str, status_code: int = 200, trace_id: str | None = None) -> dict:
    """Return an XML API Gateway response."""
    return raw(
        body=body,
        status_code=status_code,
        content_type="application/rss+xml; charset=utf-8",
        trace_id=trace_id,
    )


def accepted(
    body: Any,
    trace_id: str | None = None,
    deprecated: bool = False,
    sunset_date: str | None = None,
) -> dict:
    """202 Accepted — used for async ingestion."""
    return success(body, status_code=202, trace_id=trace_id, deprecated=deprecated, sunset_date=sunset_date)


def error(
    status_code: int,
    message: str,
    detail: str | None = None,
    trace_id: str | None = None,
    error_code: str | None = None,
) -> dict:
    """Return an error API Gateway response with tracing info."""
    body: dict[str, Any] = {
        "error": True,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if trace_id:
        body["traceId"] = trace_id
    if error_code:
        body["errorCode"] = error_code
    if detail:
        body["detail"] = detail
    return {
        "statusCode": status_code,
        "headers": _build_headers(trace_id),
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def bad_request(message: str = "Bad Request", detail: str | None = None, trace_id: str | None = None) -> dict:
    return error(400, message, detail, trace_id=trace_id, error_code="E400")


def unauthorized(message: str = "Unauthorized", trace_id: str | None = None) -> dict:
    return error(401, message, trace_id=trace_id, error_code="E401")


def forbidden(message: str = "Forbidden", trace_id: str | None = None) -> dict:
    return error(403, message, trace_id=trace_id, error_code="E403")


def not_found(message: str = "Not Found", trace_id: str | None = None) -> dict:
    return error(404, message, trace_id=trace_id, error_code="E404")


def conflict(message: str = "Conflict", trace_id: str | None = None) -> dict:
    return error(409, message, trace_id=trace_id, error_code="E409")


def too_many_requests(message: str = "Too Many Requests", trace_id: str | None = None) -> dict:
    return error(429, message, trace_id=trace_id, error_code="E429")


def internal_error(message: str = "Internal Server Error", trace_id: str | None = None) -> dict:
    return error(500, message, trace_id=trace_id, error_code="E500")
