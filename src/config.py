"""
Configuration loader — reads environment variables for the service.
All AWS resource names and external keys are configured here.
"""
import os


class Config:
    """Central configuration loaded from environment variables."""

    # AWS Region
    AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")

    # DynamoDB Tables
    REPORTS_TABLE: str = os.environ.get("REPORTS_TABLE", "report-verify-reports")
    AUDIT_TABLE: str = os.environ.get("AUDIT_TABLE", "report-verify-audit-logs")
    STATS_TABLE: str = os.environ.get("STATS_TABLE", "report-verify-stats")

    # SQS
    SQS_QUEUE_URL: str = os.environ.get("SQS_QUEUE_URL", "")
    SQS_DLQ_URL: str = os.environ.get("SQS_DLQ_URL", "")

    # EventBridge
    EVENT_BUS_NAME: str = os.environ.get("EVENT_BUS_NAME", "disaster-event-bus")
    EVENT_SOURCE: str = "service.report-verify"

    # Gemini AI
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_TIMEOUT: int = int(os.environ.get("GEMINI_TIMEOUT", "10"))

    # Trust Score Thresholds
    TRUST_AUTO_REJECT: int = int(os.environ.get("TRUST_AUTO_REJECT", "30"))
    TRUST_HIGH_PRIORITY: int = int(os.environ.get("TRUST_HIGH_PRIORITY", "80"))

    # Deduplication
    DEDUP_RADIUS_METERS: int = int(os.environ.get("DEDUP_RADIUS_METERS", "200"))
    DEDUP_TIME_WINDOW_MINUTES: int = int(os.environ.get("DEDUP_TIME_WINDOW_MINUTES", "15"))

    # API
    DEFAULT_PAGE_LIMIT: int = 5
    MAX_PAGE_LIMIT: int = 100
    MAX_PAYLOAD_BYTES: int = 256 * 1024  # 256 KB


config = Config()
