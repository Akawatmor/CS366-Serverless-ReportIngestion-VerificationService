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

    # Gemini AI — multi-key rotation + model fallback
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")  # legacy single key
    GEMINI_API_KEYS: list = []  # populated in __init_keys()
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    GEMINI_MODEL_FALLBACKS: list = []  # populated in __init_models()
    GEMINI_TIMEOUT: int = int(os.environ.get("GEMINI_TIMEOUT", "15"))

    @staticmethod
    def __init_keys() -> list:
        """Load all GEMINI_API_KEY* from env. Supports KEY1..KEY10."""
        keys = []
        for i in range(1, 11):
            k = os.environ.get(f"GEMINI_API_KEY{i}", "")
            if k:
                keys.append(k)
        # Fallback: single GEMINI_API_KEY
        if not keys:
            single = os.environ.get("GEMINI_API_KEY", "")
            if single:
                keys.append(single)
        return keys

    @staticmethod
    def __init_models() -> list:
        """Load model fallback chain from env or use defaults."""
        chain_env = os.environ.get("GEMINI_MODEL_FALLBACKS", "")
        if chain_env:
            return [m.strip() for m in chain_env.split(",") if m.strip()]
        # Default chain: flash-lite → flash → 3.1-flash-lite
        return ["gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-3.1-flash-lite"]

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

    def __init__(self):
        self.GEMINI_API_KEYS = self.__init_keys()
        self.GEMINI_MODEL_FALLBACKS = self.__init_models()
        # Set primary key for backward compat
        if self.GEMINI_API_KEYS and not self.GEMINI_API_KEY:
            self.GEMINI_API_KEY = self.GEMINI_API_KEYS[0]


config = Config()
