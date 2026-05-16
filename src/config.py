"""
Configuration loader — reads environment variables for the service.
All AWS resource names and external keys are configured here.
"""
import os
import re


class Config:
    """Central configuration loaded from environment variables."""

    DEFAULT_GEMINI_MODEL_CHAIN: tuple[str, ...] = (
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview",
        "gemma-4-26b-a4b-it",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemma-4-31b-it",
    )

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

    # S3 Media
    MEDIA_BUCKET: str = os.environ.get("MEDIA_BUCKET", "")

    # Gemini AI — multi-key rotation + model fallback
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")  # legacy single key
    GEMINI_API_KEYS: list = []  # populated in __init_keys()
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL_CHAIN[0])
    GEMINI_MODEL_FALLBACKS: list = []  # populated in __init_models()
    GEMINI_TIMEOUT: int = int(os.environ.get("GEMINI_TIMEOUT", "15"))

    @staticmethod
    def _is_configured_value(value: str) -> bool:
        """Return True when a config value is usable and not a placeholder."""
        normalized = value.strip()
        if not normalized:
            return False
        lowered = normalized.lower()
        return lowered not in {"-", "placeholder", "changeme", "replace_me"} and not lowered.startswith("your_")

    @classmethod
    def _split_config_list(cls, raw_value: str) -> list[str]:
        """Split comma-separated config values and remove placeholders."""
        return [
            item.strip()
            for item in raw_value.split(",")
            if cls._is_configured_value(item)
        ]

    @staticmethod
    def __init_keys() -> list:
        """Load Gemini API keys from environment.

        Supports (in priority order):
          1. GEMINI_API_KEYS — comma-separated string (used by Lambda env)
          2. GEMINI_API_KEY1..GEMINI_API_KEY9999 — individual vars (used by local .env)
          3. GEMINI_API_KEY — single key fallback (legacy)
        """
        # Method 1: Comma-separated (from Terraform → Lambda env)
        csv_keys = os.environ.get("GEMINI_API_KEYS", "")
        if csv_keys:
            return Config._split_config_list(csv_keys)

        # Method 2: Individual numbered keys (GEMINI_API_KEY1..GEMINI_API_KEY9999)
        key_vars = sorted(
            [(name, val) for name, val in os.environ.items()
             if re.match(r'^GEMINI_API_KEY\d+$', name) and Config._is_configured_value(val)],
            key=lambda x: int(re.search(r'\d+', x[0]).group()),
        )
        keys = [val for _, val in key_vars]

        # Method 3: Single key fallback
        if not keys:
            single = os.environ.get("GEMINI_API_KEY", "")
            if Config._is_configured_value(single):
                keys.append(single)
        return keys

    @staticmethod
    def __init_models() -> list:
        """Load model fallback chain from env or use defaults."""
        chain_env = os.environ.get("GEMINI_MODEL_FALLBACKS", "")
        if chain_env:
            chain = Config._split_config_list(chain_env)
            if chain:
                return chain

        numbered_models = sorted(
            [
                (name, val)
                for name, val in os.environ.items()
                if re.match(r'^GEMINI_MODEL\d+$', name) and Config._is_configured_value(val)
            ],
            key=lambda x: int(re.search(r'\d+', x[0]).group()),
        )
        if numbered_models:
            return [val for _, val in numbered_models]

        single_model = os.environ.get("GEMINI_MODEL", "")
        if Config._is_configured_value(single_model):
            return [single_model]

        return list(Config.DEFAULT_GEMINI_MODEL_CHAIN)

    # Trust Score Thresholds
    TRUST_AUTO_REJECT: int = int(os.environ.get("TRUST_AUTO_REJECT", "30"))
    TRUST_HIGH_PRIORITY: int = int(os.environ.get("TRUST_HIGH_PRIORITY", "80"))

    # Component Scoring — Source Platform (deterministic, used in compute_trust_score)
    SOURCE_SCORES: dict = {
        "IOT_SENSOR": 20,
        "OFFICIAL_APP": 18,
        "LINE": 12,
        "FACEBOOK": 12,
        "TWITTER": 8,
    }
    SOURCE_SCORE_DEFAULT: int = 0

    # Reporter History scoring (Component 3, computed in Python)
    HISTORY_BASE_SCORE: int = 10            # first-time reporter (no history)
    HISTORY_VERIFIED_BONUS: int = 5         # +5 bonus if ≥3 verified reports
    HISTORY_SPAM_PENALTY: int = 8           # -8 per spam record (min 0)
    HISTORY_RATE_LIMIT_WINDOW_MINUTES: int = 10
    HISTORY_RATE_LIMIT_THRESHOLD: int = 3   # ≥3 reports in window → force SPAM

    # Deduplication
    DEDUP_RADIUS_METERS: int = int(os.environ.get("DEDUP_RADIUS_METERS", "200"))
    DEDUP_TIME_WINDOW_MINUTES: int = int(os.environ.get("DEDUP_TIME_WINDOW_MINUTES", "15"))
    CONTENT_SIMILARITY_THRESHOLD: float = float(
        os.environ.get("CONTENT_SIMILARITY_THRESHOLD", "0.65")
    )

    # Upload
    UPLOAD_MAX_FILE_BYTES: int = int(os.environ.get("UPLOAD_MAX_FILE_BYTES", "20971520"))

    # Stats
    STATS_REPORT_SCAN_LIMIT: int = int(os.environ.get("STATS_REPORT_SCAN_LIMIT", "300"))
    STATS_CACHE_TTL_SECONDS: int = int(os.environ.get("STATS_CACHE_TTL_SECONDS", "60"))

    # Reverse geocoding
    REVERSE_GEOCODING_ENABLED: bool = os.environ.get(
        "REVERSE_GEOCODING_ENABLED", "true"
    ).lower() in ("1", "true", "yes", "y")
    GEOCODING_PROVIDER: str = os.environ.get("GEOCODING_PROVIDER", "nominatim")
    GEOCODING_TIMEOUT_SECONDS: int = int(os.environ.get("GEOCODING_TIMEOUT_SECONDS", "2"))
    GEOCODING_USER_AGENT: str = os.environ.get(
        "GEOCODING_USER_AGENT", "cs366-report-verify-service/1.0"
    )

    # API
    DEFAULT_PAGE_LIMIT: int = 5
    MAX_PAGE_LIMIT: int = 100
    MAX_PAYLOAD_BYTES: int = 256 * 1024  # 256 KB

    def __init__(self):
        self.GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
        self.GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "")
        self.GEMINI_API_KEYS = self.__init_keys()
        self.GEMINI_MODEL_FALLBACKS = self.__init_models()
        # Set primary key for backward compat
        if self.GEMINI_API_KEYS and not self._is_configured_value(self.GEMINI_API_KEY):
            self.GEMINI_API_KEY = self.GEMINI_API_KEYS[0]
        if self.GEMINI_MODEL_FALLBACKS and not self._is_configured_value(self.GEMINI_MODEL):
            self.GEMINI_MODEL = self.GEMINI_MODEL_FALLBACKS[0]


config = Config()
