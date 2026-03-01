"""
Unit tests for src/utils/validators.py
"""
import pytest
from src.utils.validators import (
    validate_ingest_payload,
    validate_verify_payload,
    validate_status_transition,
    validate_delete_payload,
    validate_list_params,
    validate_stats_params,
)


# ============================================================
# Ingest Payload Validation
# ============================================================

class TestValidateIngestPayload:
    """Tests for POST /reports validation."""

    def test_valid_payload(self, sample_ingest_payload):
        errors = validate_ingest_payload(sample_ingest_payload)
        assert errors == []

    def test_missing_reporter_source(self, sample_ingest_payload):
        del sample_ingest_payload["reporter_source"]
        errors = validate_ingest_payload(sample_ingest_payload)
        assert any("reporter_source" in e for e in errors)

    def test_invalid_reporter_source(self, sample_ingest_payload):
        sample_ingest_payload["reporter_source"] = "INVALID_PLATFORM"
        errors = validate_ingest_payload(sample_ingest_payload)
        assert any("reporter_source" in e for e in errors)

    def test_missing_reporter_id(self, sample_ingest_payload):
        del sample_ingest_payload["reporter_id"]
        errors = validate_ingest_payload(sample_ingest_payload)
        assert any("reporter_id" in e for e in errors)

    def test_missing_content_and_media(self):
        payload = {
            "reporter_source": "TWITTER",
            "reporter_id": "@test",
        }
        errors = validate_ingest_payload(payload)
        assert any("raw_content" in e or "media_urls" in e for e in errors)

    def test_content_only_is_valid(self):
        payload = {
            "reporter_source": "TWITTER",
            "reporter_id": "@test",
            "raw_content": "Fire!",
        }
        errors = validate_ingest_payload(payload)
        assert errors == []

    def test_media_only_is_valid(self):
        payload = {
            "reporter_source": "TWITTER",
            "reporter_id": "@test",
            "media_urls": ["https://img.host/photo.jpg"],
        }
        errors = validate_ingest_payload(payload)
        assert errors == []

    def test_invalid_geo_location(self, sample_ingest_payload):
        sample_ingest_payload["geo_location"] = {"lat": 999, "lon": 100}
        errors = validate_ingest_payload(sample_ingest_payload)
        assert any("lat" in e for e in errors)

    def test_invalid_timestamp(self, sample_ingest_payload):
        sample_ingest_payload["timestamp"] = "not-a-date"
        errors = validate_ingest_payload(sample_ingest_payload)
        assert any("timestamp" in e or "ISO8601" in e for e in errors)

    def test_valid_all_sources(self, sample_ingest_payload):
        for source in ["TWITTER", "FACEBOOK", "LINE", "OFFICIAL_APP", "IOT_SENSOR"]:
            sample_ingest_payload["reporter_source"] = source
            errors = validate_ingest_payload(sample_ingest_payload)
            assert errors == [], f"Source {source} should be valid"

    def test_invalid_media_url(self, sample_ingest_payload):
        sample_ingest_payload["media_urls"] = ["not-a-url"]
        errors = validate_ingest_payload(sample_ingest_payload)
        assert any("media_urls" in e for e in errors)


# ============================================================
# Verify Payload Validation
# ============================================================

class TestValidateVerifyPayload:
    """Tests for PATCH /reports/{id} validation."""

    def test_valid_verified(self, sample_verify_payload):
        errors = validate_verify_payload(sample_verify_payload)
        assert errors == []

    def test_missing_validation_status(self):
        errors = validate_verify_payload({})
        assert any("validation_status" in e for e in errors)

    def test_invalid_validation_status(self):
        errors = validate_verify_payload({"validation_status": "INVALID"})
        assert any("validation_status" in e for e in errors)

    def test_verified_without_reviewer_id(self):
        errors = validate_verify_payload({"validation_status": "VERIFIED"})
        assert any("reviewer_id" in e for e in errors)

    def test_spam_without_reviewer_id_is_ok(self):
        errors = validate_verify_payload({"validation_status": "SPAM"})
        assert errors == []

    def test_rejected_is_valid(self):
        errors = validate_verify_payload({"validation_status": "REJECTED"})
        assert errors == []

    def test_duplicate_is_valid(self):
        errors = validate_verify_payload({"validation_status": "DUPLICATE"})
        assert errors == []


# ============================================================
# Status Transition Validation
# ============================================================

class TestValidateStatusTransition:
    """Tests for state machine transitions."""

    def test_pending_to_verified(self):
        assert validate_status_transition("PENDING_REVIEW", "VERIFIED") is None

    def test_pending_to_spam(self):
        assert validate_status_transition("PENDING_REVIEW", "SPAM") is None

    def test_pending_to_rejected(self):
        assert validate_status_transition("PENDING_REVIEW", "REJECTED") is None

    def test_pending_to_duplicate(self):
        assert validate_status_transition("PENDING_REVIEW", "DUPLICATE") is None

    def test_received_to_pending(self):
        assert validate_status_transition("RECEIVED", "PENDING_REVIEW") is None

    def test_verified_cannot_change(self):
        error = validate_status_transition("VERIFIED", "SPAM")
        assert error is not None
        assert "cannot be updated" in error.lower() or "cannot transition" in error.lower()

    def test_spam_cannot_change(self):
        error = validate_status_transition("SPAM", "VERIFIED")
        assert error is not None

    def test_pending_cannot_go_to_received(self):
        error = validate_status_transition("PENDING_REVIEW", "RECEIVED")
        assert error is not None


# ============================================================
# Delete Payload Validation
# ============================================================

class TestValidateDeletePayload:
    """Tests for DELETE /reports/{id} validation."""

    def test_valid_delete(self, sample_delete_payload):
        errors = validate_delete_payload(sample_delete_payload)
        assert errors == []

    def test_missing_reason(self):
        errors = validate_delete_payload({"deleted_by": "admin"})
        assert any("reason" in e for e in errors)

    def test_missing_deleted_by(self):
        errors = validate_delete_payload({"reason": "test"})
        assert any("deleted_by" in e for e in errors)


# ============================================================
# Query Params Validation
# ============================================================

class TestValidateListParams:
    """Tests for GET /reports query parameters."""

    def test_defaults(self):
        parsed, errors = validate_list_params({})
        assert errors == []
        assert parsed["limit"] == 5

    def test_valid_params(self):
        parsed, errors = validate_list_params({
            "status": "PENDING_REVIEW",
            "min_trust_score": "50",
            "limit": "20",
        })
        assert errors == []
        assert parsed["status"] == "PENDING_REVIEW"
        assert parsed["min_trust_score"] == 50
        assert parsed["limit"] == 20

    def test_invalid_status(self):
        _, errors = validate_list_params({"status": "INVALID"})
        assert len(errors) > 0

    def test_limit_too_high(self):
        _, errors = validate_list_params({"limit": "999"})
        assert any("limit" in e for e in errors)

    def test_invalid_trust_score(self):
        _, errors = validate_list_params({"min_trust_score": "abc"})
        assert len(errors) > 0


class TestValidateStatsParams:
    """Tests for GET /reports/stats query parameters."""

    def test_default_timeframe(self):
        parsed, errors = validate_stats_params({})
        assert errors == []
        assert parsed["timeframe"] == "today"

    def test_valid_timeframes(self):
        for tf in ["today", "last_24h", "last_7d"]:
            parsed, errors = validate_stats_params({"timeframe": tf})
            assert errors == []

    def test_invalid_timeframe(self):
        _, errors = validate_stats_params({"timeframe": "last_year"})
        assert len(errors) > 0
