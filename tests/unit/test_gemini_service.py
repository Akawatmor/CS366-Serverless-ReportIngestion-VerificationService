"""
Unit tests for src/services/gemini_service.py

Tests the GeminiService class with multi-key rotation and model fallback.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from src.services.gemini_service import GeminiService


class TestGeminiService:
    """Tests for Gemini AI trust scoring service."""

    def setup_method(self):
        """Create a fresh GeminiService with test keys configured via env."""
        with patch.dict("os.environ", {
            "GEMINI_API_KEY1": "test-key-1",
            "GEMINI_API_KEY2": "test-key-2",
        }):
            from src.config import Config
            test_config = Config()
            with patch("src.services.gemini_service.config", test_config):
                self.service = GeminiService()

    def test_fallback_result_structure(self):
        """Fallback result should have all required fields."""
        result = GeminiService._fallback_result()
        assert result["content_score"] == 15
        assert result["suggested_category"] == "OTHER"
        assert isinstance(result["keywords"], list)
        assert result["ai_analysis_failed"] is True
        assert result["is_spam_likely"] is False
        assert "content_score_reasoning" in result

    @patch("src.services.gemini_service.genai", create=True)
    def test_analyze_report_success(self, mock_genai):
        """Successful Gemini analysis should return parsed JSON."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "content_score": 25,
            "content_score_reasoning": "Street name and timeline present",
            "suggested_category": "FIRE",
            "keywords": ["fire", "smoke", "urgent"],
            "spam_signals": [],
            "is_spam_likely": False,
        })

        self.service._call_gemini = MagicMock(return_value=mock_response.text)

        result = self.service.analyze_report(
            content="Fire at Central World!",
            source="TWITTER",
            reporter_id="@user123",
            lat=13.7466,
            lon=100.5391,
            timestamp="2026-02-18T14:30:00Z",
        )

        assert result["content_score"] == 25
        assert result["suggested_category"] == "FIRE"
        assert "fire" in result["keywords"]
        assert result["ai_analysis_failed"] is False

    def test_analyze_report_failure_returns_fallback(self):
        """When Gemini fails, should return fallback values."""
        self.service._call_gemini = MagicMock(
            side_effect=RuntimeError("All keys exhausted")
        )

        result = self.service.analyze_report(content="Test content")

        assert result["content_score"] == 15
        assert result["ai_analysis_failed"] is True

    def test_analyze_report_invalid_json_returns_fallback(self):
        """When Gemini returns non-JSON, should return fallback."""
        self.service._call_gemini = MagicMock(return_value="This is not JSON")

        result = self.service.analyze_report(content="Test content")

        assert result["content_score"] == 15
        assert result["ai_analysis_failed"] is True

    @patch("urllib.request.urlopen")
    def test_health_check_success(self, mock_urlopen):
        """Health check returns healthy when API responds."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"models": []}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.service.health_check()
        assert result["status"] == "healthy"
        assert "model" in result
        assert "available_keys" in result

    @patch("urllib.request.urlopen", side_effect=Exception("Connection error"))
    def test_health_check_failure(self, _mock_urlopen):
        """Health check returns unhealthy when API fails."""
        result = self.service.health_check()
        assert result["status"] == "unhealthy"

    def test_rotate_key(self):
        """Key rotation should cycle through available keys."""
        self.service._api_keys = ["key1", "key2", "key3"]
        self.service._current_key_idx = 0
        self.service._blocked_keys = set()

        result = self.service._rotate_key()
        assert result is True
        assert self.service._current_key_idx == 1

    def test_rotate_key_all_exhausted(self):
        """When all keys are blocked, rotation should fail."""
        self.service._api_keys = ["key1", "key2"]
        self.service._current_key_idx = 0
        self.service._blocked_keys = set()

        self.service._rotate_key()
        result = self.service._rotate_key()
        assert result is False

    def test_advance_model(self):
        """Model fallback should advance to next model."""
        self.service._model_chain = ["model-A", "model-B", "model-C"]
        self.service._current_model_idx = 0
        self.service._blocked_keys = {0, 1}

        result = self.service._advance_model()
        assert result is True
        assert self.service._current_model_idx == 1
        assert self.service._blocked_keys == set()

    def test_advance_model_all_exhausted(self):
        """When all models used, advance should fail."""
        self.service._model_chain = ["model-A"]
        self.service._current_model_idx = 0

        result = self.service._advance_model()
        assert result is False

    def test_is_rate_limited(self):
        """Should detect 429 rate limit errors."""
        assert self.service._is_rate_limited(Exception("429 RESOURCE_EXHAUSTED"))
        assert self.service._is_rate_limited(Exception("rate limit exceeded"))
        assert not self.service._is_rate_limited(Exception("500 Internal Server Error"))

    def test_is_model_not_found(self):
        """Should detect model-not-found errors."""
        assert self.service._is_model_not_found(Exception("404 model not found"))
        assert self.service._is_model_not_found(Exception("models/gemini-X is not found"))
        assert not self.service._is_model_not_found(Exception("network timeout"))

    def test_no_keys_returns_fallback(self):
        """With no API keys, analyze_report returns fallback."""
        self.service._api_keys = []
        with patch("src.services.gemini_service.config") as mock_config:
            mock_config.GEMINI_API_KEY = ""
            result = self.service.analyze_report(content="test")
        assert result["ai_analysis_failed"] is True
        assert result["content_score"] == 15
