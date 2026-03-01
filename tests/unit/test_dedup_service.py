"""
Unit tests for src/services/dedup_service.py
"""
import pytest
from src.services.dedup_service import _haversine_meters, _within_time_window


class TestHaversine:
    """Tests for distance calculation."""

    def test_same_point(self):
        dist = _haversine_meters(13.7466, 100.5391, 13.7466, 100.5391)
        assert dist == 0.0

    def test_nearby_points_within_200m(self):
        """Two points ~100m apart in Bangkok."""
        dist = _haversine_meters(13.7466, 100.5391, 13.7475, 100.5391)
        assert dist < 200

    def test_far_points(self):
        """Bangkok to Chiang Mai ~585km."""
        dist = _haversine_meters(13.7563, 100.5018, 18.7883, 98.9853)
        assert dist > 500_000  # > 500km

    def test_equator_crossing(self):
        dist = _haversine_meters(0.001, 0.0, -0.001, 0.0)
        assert dist > 0
        assert dist < 500  # ~222m


class TestTimeWindow:
    """Tests for time window checking."""

    def test_within_window(self):
        assert _within_time_window(
            "2026-02-18T14:30:00Z",
            "2026-02-18T14:35:00Z",
            15,
        ) is True

    def test_outside_window(self):
        assert _within_time_window(
            "2026-02-18T14:00:00Z",
            "2026-02-18T15:00:00Z",
            15,
        ) is False

    def test_exact_boundary(self):
        assert _within_time_window(
            "2026-02-18T14:00:00Z",
            "2026-02-18T14:15:00Z",
            15,
        ) is True

    def test_invalid_format(self):
        assert _within_time_window("invalid", "also-invalid", 15) is False

    def test_timezone_aware(self):
        assert _within_time_window(
            "2026-02-18T14:30:00+07:00",
            "2026-02-18T07:35:00+00:00",
            15,
        ) is True
