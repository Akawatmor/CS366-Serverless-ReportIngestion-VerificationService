"""
Unit tests for src/services/gemini_service.py
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from src.services.gemini_service import GeminiService


class TestGeminiService:
    """Tests for Gemini AI trust scoring service."""

    def setup_method(self):
        self.service = GeminiService(api_key="test-key")

    def test_fallback_result_structure(self):
        """Fallback result should have all required fields."""
        result = GeminiService._fallback_result()
        assert result["trust_score"] == 50
        assert result["suggested_category"] == "OTHER"
        assert isinstance(result["keywords"], list)
        assert result["ai_analysis_failed"] is True

    @patch("src.services.gemini_service.genai", create=True)
    def test_analyze_report_success(self, mock_genai):
        """Successful Gemini analysis should return parsed JSON."""
        # Mock the Gemini response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "trust_score": 85,
            "suggested_category": "FIRE",
            "keywords": ["fire", "smoke", "urgent"],
            "reasoning": "Multiple indicators of fire detected",
            "is_spam_likely": False,
        })

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        self.service._client = mock_model

        result = self.service.analyze_report(
            content="Fire at Central World!",
            source="TWITTER",
            reporter_id="@user123",
            lat=13.7466,
            lon=100.5391,
            timestamp="2026-02-18T14:30:00Z",
        )

        assert result["trust_score"] == 85
        assert result["suggested_category"] == "FIRE"
        assert "fire" in result["keywords"]
        assert result["ai_analysis_failed"] is False

    def test_analyze_report_failure_returns_fallback(self):
        """When Gemini fails, should return fallback values."""
        # Force an error by setting invalid client
        self.service._client = MagicMock()
        self.service._client.generate_content.side_effect = Exception("API Error")

        result = self.service.analyze_report(content="Test content")

        assert result["trust_score"] == 50
        assert result["ai_analysis_failed"] is True

    def test_analyze_report_invalid_json_returns_fallback(self):
        """When Gemini returns non-JSON, should return fallback."""
        mock_response = MagicMock()
        mock_response.text = "This is not JSON"
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        self.service._client = mock_model

        result = self.service.analyze_report(content="Test content")

        assert result["trust_score"] == 50
        assert result["ai_analysis_failed"] is True

    def test_health_check_success(self):
        """Health check returns healthy when API responds."""
        mock_response = MagicMock()
        mock_response.text = "OK"
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        self.service._client = mock_model

        result = self.service.health_check()
        assert result["status"] == "healthy"

    def test_health_check_failure(self):
        """Health check returns unhealthy when API fails."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Connection error")
        self.service._client = mock_model

        result = self.service.health_check()
        assert result["status"] == "unhealthy"
