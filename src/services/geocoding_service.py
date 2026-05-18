"""
Reverse geocoding service for turning lat/lon into human-readable addresses.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class _CacheEntry:
    value: str | None
    expires_at: float


class ReverseGeocodingService:
    """Resolve lat/lon to address text using a best-effort external provider."""

    def __init__(self):
        self._cache: dict[tuple[float, float], _CacheEntry] = {}
        self._cache_ttl_seconds = 24 * 60 * 60

    def reverse_geocode(self, lat: float, lon: float) -> str | None:
        """Return human-readable address text for coordinates."""
        cache_key = (round(lat, 4), round(lon, 4))
        now = time.time()

        cached = self._cache.get(cache_key)
        if cached and cached.expires_at > now:
            return cached.value

        if not config.REVERSE_GEOCODING_ENABLED:
            value = self._fallback_address(lat, lon)
            self._cache[cache_key] = _CacheEntry(value=value, expires_at=now + self._cache_ttl_seconds)
            return value

        provider = config.GEOCODING_PROVIDER.lower().strip()
        value: str | None

        try:
            if provider == "nominatim":
                value = self._reverse_with_nominatim(lat, lon)
            else:
                logger.warning(f"Unknown geocoding provider '{provider}', using fallback")
                value = None
        except Exception as e:
            logger.warning(f"Reverse geocoding failed: {e}")
            value = None

        if not value:
            value = self._fallback_address(lat, lon)

        self._cache[cache_key] = _CacheEntry(value=value, expires_at=now + self._cache_ttl_seconds)
        return value

    def _reverse_with_nominatim(self, lat: float, lon: float) -> str | None:
        query = urlencode({
            "lat": str(lat),
            "lon": str(lon),
            "format": "jsonv2",
            "zoom": "16",
            "addressdetails": "1",
        })
        url = f"https://nominatim.openstreetmap.org/reverse?{query}"
        req = Request(
            url,
            headers={
                "User-Agent": config.GEOCODING_USER_AGENT,
                "Accept": "application/json",
            },
            method="GET",
        )

        with urlopen(req, timeout=config.GEOCODING_TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        if not isinstance(payload, dict):
            return None

        address = payload.get("address") or {}
        display_name = payload.get("display_name", "")

        parts = [
            address.get("suburb"),
            address.get("city"),
            address.get("state"),
            address.get("country"),
        ]
        compact = ", ".join([p for p in parts if p])

        if compact:
            return compact
        if isinstance(display_name, str) and display_name:
            return display_name[:200]
        return None

    @staticmethod
    def _fallback_address(lat: float, lon: float) -> str:
        return f"lat={lat:.5f}, lon={lon:.5f}"


reverse_geocoding_service = ReverseGeocodingService()
