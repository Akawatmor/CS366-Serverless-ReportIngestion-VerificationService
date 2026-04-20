"""
Unit tests for ingestion worker decision helpers.
"""

from src.handlers.ingestion_worker import _determine_priority, _determine_status
from src.models.enums import ValidationStatus


class TestIngestionPriority:
    """Priority queue decision tests."""

    def test_high_trust_is_priority(self):
        priority = _determine_priority(
            trust_score=95,
            raw_content="Minor details",
            ai_result={"keywords": [], "suggested_category": "OTHER"},
        )
        assert priority == 1

    def test_severity_keywords_raise_priority(self):
        priority = _determine_priority(
            trust_score=45,
            raw_content="มีคนติดอยู่ในตึก ช่วยด้วย",
            ai_result={"keywords": ["ไฟไหม้"], "suggested_category": "FIRE"},
        )
        assert priority == 1

    def test_normal_report_not_priority(self):
        priority = _determine_priority(
            trust_score=40,
            raw_content="Road has light traffic and minor issue",
            ai_result={"keywords": ["traffic"], "suggested_category": "OTHER"},
        )
        assert priority == 0


class TestIngestionStatus:
    """Status transition decision tests for worker auto-processing."""

    def test_duplicates_marked_duplicate(self):
        status = _determine_status(
            trust_score=80,
            ai_result={"is_spam_likely": False},
            duplicates=["r-1"],
            body={},
        )
        assert status == ValidationStatus.DUPLICATE.value

    def test_low_trust_marked_spam(self):
        status = _determine_status(
            trust_score=10,
            ai_result={"is_spam_likely": True},
            duplicates=[],
            body={},
        )
        assert status == ValidationStatus.SPAM.value
