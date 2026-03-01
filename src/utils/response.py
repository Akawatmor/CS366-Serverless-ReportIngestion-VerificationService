"""
Standardised API response builder — ensures every Lambda response
follows the same shape expected by API Gateway (proxy integration).
"""
import json
from typing import Any


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Api-Key",
}


def success(body: Any, status_code: int = 200) -> dict:
    """Return a successful API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def accepted(body: Any) -> dict:
    """202 Accepted — used for async ingestion."""
    return success(body, status_code=202)


def error(status_code: int, message: str, detail: str | None = None) -> dict:
    """Return an error API Gateway response."""
    body: dict[str, Any] = {
        "error": True,
        "message": message,
    }
    if detail:
        body["detail"] = detail
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def bad_request(message: str = "Bad Request", detail: str | None = None) -> dict:
    return error(400, message, detail)


def unauthorized(message: str = "Unauthorized") -> dict:
    return error(401, message)


def forbidden(message: str = "Forbidden") -> dict:
    return error(403, message)


def not_found(message: str = "Not Found") -> dict:
    return error(404, message)


def conflict(message: str = "Conflict") -> dict:
    return error(409, message)


def too_many_requests(message: str = "Too Many Requests") -> dict:
    return error(429, message)


def internal_error(message: str = "Internal Server Error") -> dict:
    return error(500, message)
