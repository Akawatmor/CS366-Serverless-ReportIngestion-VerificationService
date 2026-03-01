"""
Gemini AI Service — calls Google Gemini API for Trust Scoring.

Replaces Amazon Comprehend from the original proposal.
Sends raw_content + reporter metadata as a structured prompt and
expects a JSON response with trust_score, suggested_category, and keywords.
"""
from __future__ import annotations

import json
import time
from typing import Any

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Prompt template for Gemini
ANALYSIS_PROMPT = """You are a disaster report verification AI. Analyze the following raw disaster report and provide a trust assessment.

**Report Content:**
{content}

**Reporter Source:** {source}
**Reporter ID:** {reporter_id}
**Location (lat, lon):** {lat}, {lon}
**Reported Time:** {timestamp}

**Instructions:**
1. Evaluate the credibility of this report on a scale of 0-100 (trust_score).
2. Suggest a disaster category from: FIRE, FLOOD, EARTHQUAKE, ACCIDENT, SOS, DAMAGE, OTHER.
3. Extract important keywords (Thai or English).
4. Provide a brief reasoning for your trust score.
5. Detect if this looks like spam, fake news, or a duplicate pattern.

**Respond ONLY with valid JSON in this exact format:**
{{
  "trust_score": <int 0-100>,
  "suggested_category": "<string>",
  "keywords": ["<string>", ...],
  "reasoning": "<string>",
  "is_spam_likely": <boolean>
}}"""


class GeminiService:
    """Client for Google Gemini API — handles trust scoring analysis."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self._client = None

    def _get_client(self):
        """Lazy-init the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(config.GEMINI_MODEL)
                logger.info("Gemini client initialized", extra={"data": {"model": config.GEMINI_MODEL}})
            except Exception as e:
                logger.error("Failed to initialize Gemini client", exc_info=True)
                raise
        return self._client

    def analyze_report(
        self,
        content: str,
        source: str = "",
        reporter_id: str = "",
        lat: float | None = None,
        lon: float | None = None,
        timestamp: str = "",
    ) -> dict[str, Any]:
        """
        Send report content to Gemini for trust scoring analysis.

        Returns dict with keys:
            trust_score (int), suggested_category (str),
            keywords (list[str]), reasoning (str), is_spam_likely (bool)

        On failure, returns fallback values with ai_analysis_failed=True.
        """
        start_time = time.time()

        try:
            prompt = ANALYSIS_PROMPT.format(
                content=content or "(no text content)",
                source=source,
                reporter_id=reporter_id,
                lat=lat or "N/A",
                lon=lon or "N/A",
                timestamp=timestamp or "N/A",
            )

            client = self._get_client()
            response = client.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 512,
                    "response_mime_type": "application/json",
                },
            )

            # Parse the JSON response
            result = json.loads(response.text)
            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Gemini analysis completed",
                extra={"data": {
                    "trust_score": result.get("trust_score"),
                    "category": result.get("suggested_category"),
                    "duration_ms": duration_ms,
                }},
            )

            return {
                "trust_score": int(result.get("trust_score", 50)),
                "suggested_category": result.get("suggested_category", "OTHER"),
                "keywords": result.get("keywords", []),
                "reasoning": result.get("reasoning", ""),
                "is_spam_likely": result.get("is_spam_likely", False),
                "ai_analysis_failed": False,
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Gemini analysis failed — using fallback values",
                extra={"data": {"error": str(e), "duration_ms": duration_ms}},
            )
            return self._fallback_result()

    @staticmethod
    def _fallback_result() -> dict[str, Any]:
        """Default result when AI is unavailable — trust_score = 50 (neutral)."""
        return {
            "trust_score": 50,
            "suggested_category": "OTHER",
            "keywords": [],
            "reasoning": "AI analysis unavailable — manual review required.",
            "is_spam_likely": False,
            "ai_analysis_failed": True,
        }

    def health_check(self) -> dict[str, Any]:
        """Lightweight connectivity check for /health endpoint."""
        try:
            client = self._get_client()
            # Minimal prompt to verify API reachability
            response = client.generate_content(
                "Reply with exactly: OK",
                generation_config={"max_output_tokens": 10},
            )
            return {"status": "healthy", "model": config.GEMINI_MODEL}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Module-level singleton
gemini_service = GeminiService()
