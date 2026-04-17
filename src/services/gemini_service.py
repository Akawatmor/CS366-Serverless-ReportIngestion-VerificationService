"""
Gemini AI Service — calls Google Gemini API for Trust Scoring.

Features:
  - Multi API key rotation: cycles through GEMINI_API_KEY1..10
    When a key gets 429 (rate limited), automatically rotates to the next key.
  - Model fallback chain: tries gemini-2.5-flash-lite first, then
    gemini-2.0-flash, then gemini-3.1-flash-lite.
  - Graceful degradation: if all keys/models fail, returns fallback values.
  - Vision support: can analyze images from S3 URLs.
"""
from __future__ import annotations

import base64
import json
import time
from typing import Any
from urllib.parse import urlparse

import boto3

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Prompt template for Gemini (text-only)
ANALYSIS_PROMPT = """You are a disaster report verification AI. Analyze the following raw disaster report and provide a trust assessment.

**Report Content:**
{content}

**Reporter Source:** {source}
**Reporter ID:** {reporter_id}
**Location (lat, lon):** {lat}, {lon}
**Reported Time:** {timestamp}

**Attached Media URLs:** {media_urls}

**Reporter History:**
{reporter_history}

**Instructions:**
1. Evaluate the credibility of this report on a scale of 0-100 (trust_score).
   - Consider the reporter's past history: repeated spam submissions lower trust; a track record of verified reports increases trust.
   - If media evidence URLs are attached, acknowledge their presence (higher trust if photos/video are included).
2. Suggest a disaster category from: FIRE, FLOOD, EARTHQUAKE, ACCIDENT, SOS, DAMAGE, OTHER.
3. Extract important keywords (Thai or English).
4. Provide a brief reasoning for your trust score, including how reporter history and media affected your decision.
5. Detect if this looks like spam, fake news, or a duplicate pattern. Consider repeat offenders.

**Respond ONLY with valid JSON in this exact format:**
{{
  "trust_score": <int 0-100>,
  "suggested_category": "<string>",
  "keywords": ["<string>", ...],
  "reasoning": "<string>",
  "is_spam_likely": <boolean>
}}"""

# Prompt template for Gemini Vision (with images)
VISION_ANALYSIS_PROMPT = """You are a disaster report verification AI with image analysis capability. Analyze the following disaster report including the attached image(s).

**Report Content:**
{content}

**Reporter Source:** {source}
**Reporter ID:** {reporter_id}
**Location (lat, lon):** {lat}, {lon}
**Reported Time:** {timestamp}

**Reporter History:**
{reporter_history}

**Instructions:**
1. Carefully examine the attached image(s) for signs of:
   - Real disaster damage (fire, flood, structural damage, etc.)
   - Manipulation or editing artifacts
   - Stock photos or internet-sourced images
   - Consistency with the text description
2. Evaluate the credibility of this report on a scale of 0-100 (trust_score).
   - Images showing real damage: +20-30 points
   - Images that look fake/manipulated: -30-50 points
   - Images inconsistent with description: -20 points
3. Suggest a disaster category from: FIRE, FLOOD, EARTHQUAKE, ACCIDENT, SOS, DAMAGE, OTHER.
4. Extract important keywords (Thai or English).
5. Describe what you see in the image(s) and how it affects your trust assessment.
6. Detect if this looks like spam, fake news, or a duplicate pattern.

**Respond ONLY with valid JSON in this exact format:**
{{
  "trust_score": <int 0-100>,
  "suggested_category": "<string>",
  "keywords": ["<string>", ...],
  "reasoning": "<string>",
  "image_analysis": "<description of what you see in the image(s)>",
  "image_authenticity": "<real|likely_fake|uncertain>",
  "is_spam_likely": <boolean>
}}"""


class GeminiService:
    """
    Client for Google Gemini API — handles trust scoring analysis.

    Supports:
      - Multi-key rotation on 429 errors
      - Model fallback chain (flash-lite → flash → 3.1-flash-lite)
      - Vision analysis for images from S3
    """

    # Supported image types for vision analysis
    SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    MAX_IMAGE_SIZE = 4 * 1024 * 1024  # 4MB limit per image
    MAX_IMAGES_PER_REQUEST = 3  # Limit images to avoid token limits

    def __init__(self):
        self._api_keys: list[str] = list(config.GEMINI_API_KEYS)
        self._model_chain: list[str] = list(config.GEMINI_MODEL_FALLBACKS)
        self._current_key_idx: int = 0
        self._current_model_idx: int = 0
        self._clients: dict[str, Any] = {}  # cache: (key_idx, model) -> client
        self._blocked_keys: set[int] = set()  # key indices that got 429
        self._s3_client = None

    @property
    def _current_key(self) -> str:
        if not self._api_keys:
            return config.GEMINI_API_KEY or ""
        return self._api_keys[self._current_key_idx % len(self._api_keys)]

    @property
    def _current_model(self) -> str:
        if not self._model_chain:
            return config.GEMINI_MODEL
        return self._model_chain[self._current_model_idx % len(self._model_chain)]

    def _get_s3_client(self):
        """Lazy-load S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=config.AWS_REGION)
        return self._s3_client

    def _get_client(self, api_key: str, model_name: str):
        """Get or create a Gemini GenerativeModel for the given key+model."""
        cache_key = f"{api_key[:8]}_{model_name}"
        if cache_key not in self._clients:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._clients[cache_key] = genai.GenerativeModel(model_name)
            logger.info("Gemini client initialized", extra={"data": {
                "model": model_name,
                "key_prefix": api_key[:8] + "...",
            }})
        return self._clients[cache_key]

    def _rotate_key(self) -> bool:
        """Rotate to next available API key. Returns False if all keys exhausted."""
        self._blocked_keys.add(self._current_key_idx)
        if len(self._blocked_keys) >= len(self._api_keys):
            # All keys blocked for current model — try next model
            return False
        # Find next non-blocked key
        for _ in range(len(self._api_keys)):
            self._current_key_idx = (self._current_key_idx + 1) % len(self._api_keys)
            if self._current_key_idx not in self._blocked_keys:
                logger.info("Rotated to next API key", extra={"data": {
                    "key_idx": self._current_key_idx,
                    "key_prefix": self._current_key[:8] + "...",
                }})
                return True
        return False

    def _advance_model(self) -> bool:
        """Move to next model in fallback chain. Returns False if all exhausted."""
        self._current_model_idx += 1
        if self._current_model_idx >= len(self._model_chain):
            return False
        # Reset blocked keys — new model gets fresh tries with all keys
        self._blocked_keys.clear()
        self._current_key_idx = 0
        logger.info("Falling back to next model", extra={"data": {
            "model": self._current_model,
            "model_idx": self._current_model_idx,
        }})
        return True

    def _download_image_from_s3(self, media_url: str) -> dict[str, Any] | None:
        """
        Download image from S3 URL and return base64 encoded data.
        Returns None if download fails or image is not supported.
        """
        try:
            # Parse S3 URL: https://{bucket}.s3.{region}.amazonaws.com/{key}
            parsed = urlparse(media_url)
            
            if "s3" not in parsed.netloc and "amazonaws.com" not in parsed.netloc:
                logger.warning(f"Not an S3 URL, skipping: {media_url[:50]}")
                return None

            # Extract bucket and key from URL
            # Format: {bucket}.s3.{region}.amazonaws.com/{key}
            host_parts = parsed.netloc.split(".")
            if len(host_parts) < 4:
                logger.warning(f"Invalid S3 URL format: {media_url[:50]}")
                return None
            
            bucket = host_parts[0]
            key = parsed.path.lstrip("/")

            # Download from S3
            s3 = self._get_s3_client()
            response = s3.get_object(Bucket=bucket, Key=key)
            
            content_type = response.get("ContentType", "application/octet-stream")
            content_length = response.get("ContentLength", 0)

            # Validate content type
            if content_type not in self.SUPPORTED_IMAGE_TYPES:
                logger.warning(f"Unsupported image type {content_type}: {media_url[:50]}")
                return None

            # Check size limit
            if content_length > self.MAX_IMAGE_SIZE:
                logger.warning(f"Image too large ({content_length} bytes): {media_url[:50]}")
                return None

            # Read and encode image
            image_data = response["Body"].read()
            base64_data = base64.b64encode(image_data).decode("utf-8")

            logger.info("Image downloaded from S3", extra={"data": {
                "bucket": bucket,
                "key": key[:50],
                "content_type": content_type,
                "size_bytes": content_length,
            }})

            return {
                "mime_type": content_type,
                "data": base64_data,
            }

        except Exception as e:
            logger.warning(f"Failed to download image from S3: {e}", extra={"data": {
                "url": media_url[:100],
                "error": str(e)[:100],
            }})
            return None

    def _prepare_image_parts(self, media_urls: list[str]) -> list[dict[str, Any]]:
        """
        Download images from S3 and prepare them for Gemini Vision.
        Returns list of image parts for multimodal input.
        """
        image_parts = []
        
        for url in media_urls[:self.MAX_IMAGES_PER_REQUEST]:
            image_data = self._download_image_from_s3(url)
            if image_data:
                image_parts.append({
                    "inline_data": image_data
                })

        return image_parts

    def _is_rate_limited(self, error: Exception) -> bool:
        """Check if error is a 429 rate limit or resource exhausted."""
        err_str = str(error).lower()
        return any(indicator in err_str for indicator in [
            "429", "resource_exhausted", "rate limit",
            "quota", "too many requests", "resourceexhausted",
        ])

    def _is_model_not_found(self, error: Exception) -> bool:
        """Check if the model is not available/found."""
        err_str = str(error).lower()
        return any(indicator in err_str for indicator in [
            "404", "not found", "not_found", "model not found",
            "is not found", "models/",
        ])

    def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini API with retry across keys and model fallback.
        Returns the response text or raises if all attempts fail.
        """
        # Reset state for this call
        self._blocked_keys.clear()
        self._current_model_idx = 0
        self._current_key_idx = 0

        last_error = None

        while self._current_model_idx < len(self._model_chain):
            model_name = self._current_model

            while True:
                api_key = self._current_key
                try:
                    client = self._get_client(api_key, model_name)
                    response = client.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.1,
                            "max_output_tokens": 512,
                            "response_mime_type": "application/json",
                        },
                        request_options={
                            "timeout": config.GEMINI_TIMEOUT,
                        },
                    )
                    # Success — log which key/model worked
                    logger.info("Gemini call succeeded", extra={"data": {
                        "model": model_name,
                        "key_idx": self._current_key_idx,
                    }})
                    return response.text

                except Exception as e:
                    last_error = e
                    logger.warning(f"Gemini call failed", extra={"data": {
                        "model": model_name,
                        "key_idx": self._current_key_idx,
                        "key_prefix": api_key[:8] + "...",
                        "error": str(e)[:200],
                    }})

                    if self._is_model_not_found(e):
                        # Model doesn't exist — skip to next model
                        logger.warning(f"Model {model_name} not available, advancing")
                        break

                    if self._is_rate_limited(e):
                        # 429 — rotate to next key
                        if not self._rotate_key():
                            # All keys exhausted for this model
                            break
                        continue
                    else:
                        # Other error — try next key anyway
                        if not self._rotate_key():
                            break
                        continue

            # Advance to next model in fallback chain
            if not self._advance_model():
                break

        raise RuntimeError(
            f"All Gemini API keys and models exhausted. "
            f"Last error: {last_error}"
        )

    def _call_gemini_with_images(self, prompt: str, image_parts: list[dict[str, Any]]) -> str:
        """
        Call Gemini Vision API with images for multimodal analysis.
        Returns the response text or raises if all attempts fail.
        """
        # Reset state for this call
        self._blocked_keys.clear()
        self._current_model_idx = 0
        self._current_key_idx = 0

        last_error = None

        # Build multimodal content: images first, then text prompt
        content_parts = image_parts + [prompt]

        while self._current_model_idx < len(self._model_chain):
            model_name = self._current_model

            while True:
                api_key = self._current_key
                try:
                    client = self._get_client(api_key, model_name)
                    response = client.generate_content(
                        content_parts,
                        generation_config={
                            "temperature": 0.1,
                            "max_output_tokens": 1024,  # More tokens for image analysis
                            "response_mime_type": "application/json",
                        },
                        request_options={
                            "timeout": config.GEMINI_TIMEOUT + 15,  # Extra time for vision
                        },
                    )
                    # Success — log which key/model worked
                    logger.info("Gemini Vision call succeeded", extra={"data": {
                        "model": model_name,
                        "key_idx": self._current_key_idx,
                        "image_count": len(image_parts),
                    }})
                    return response.text

                except Exception as e:
                    last_error = e
                    logger.warning(f"Gemini Vision call failed", extra={"data": {
                        "model": model_name,
                        "key_idx": self._current_key_idx,
                        "key_prefix": api_key[:8] + "...",
                        "error": str(e)[:200],
                    }})

                    if self._is_model_not_found(e):
                        # Model doesn't exist — skip to next model
                        logger.warning(f"Model {model_name} not available for Vision, advancing")
                        break

                    if self._is_rate_limited(e):
                        # 429 — rotate to next key
                        if not self._rotate_key():
                            break
                        continue
                    else:
                        # Other error — try next key anyway
                        if not self._rotate_key():
                            break
                        continue

            # Advance to next model in fallback chain
            if not self._advance_model():
                break

        raise RuntimeError(
            f"All Gemini Vision API keys and models exhausted. "
            f"Last error: {last_error}"
        )

    def analyze_report(
        self,
        content: str,
        source: str = "",
        reporter_id: str = "",
        lat: float | None = None,
        lon: float | None = None,
        timestamp: str = "",
        media_urls: list[str] | None = None,
        reporter_history: str = "",
    ) -> dict[str, Any]:
        """
        Send report content to Gemini for trust scoring analysis.
        If media_urls contain S3 images, uses Vision API for image analysis.

        Returns dict with keys:
            trust_score (int), suggested_category (str),
            keywords (list[str]), reasoning (str), is_spam_likely (bool)
            Optional: image_analysis, image_authenticity (when Vision used)

        On failure, returns fallback values with ai_analysis_failed=True.
        """
        if not self._api_keys and not config.GEMINI_API_KEY:
            logger.warning("No Gemini API keys configured — using fallback")
            return self._fallback_result()

        start_time = time.time()

        # Format reporter history
        history_str = reporter_history or "No prior reports from this reporter."

        # Try to download images from S3 for Vision analysis
        image_parts = []
        if media_urls:
            image_parts = self._prepare_image_parts(media_urls)

        use_vision = len(image_parts) > 0

        try:
            if use_vision:
                # Use Vision API with images
                logger.info(f"Using Gemini Vision with {len(image_parts)} image(s)")
                
                prompt = VISION_ANALYSIS_PROMPT.format(
                    content=content or "(no text content)",
                    source=source,
                    reporter_id=reporter_id,
                    lat=lat or "N/A",
                    lon=lon or "N/A",
                    timestamp=timestamp or "N/A",
                    reporter_history=history_str,
                )

                response_text = self._call_gemini_with_images(prompt, image_parts)
            else:
                # Use text-only API
                media_str = "None"
                if media_urls:
                    # Still include URLs in prompt even if we couldn't download
                    media_str = "\n".join(f"  - {url}" for url in media_urls[:10])

                prompt = ANALYSIS_PROMPT.format(
                    content=content or "(no text content)",
                    source=source,
                    reporter_id=reporter_id,
                    lat=lat or "N/A",
                    lon=lon or "N/A",
                    timestamp=timestamp or "N/A",
                    media_urls=media_str,
                    reporter_history=history_str,
                )

                response_text = self._call_gemini(prompt)

            result = json.loads(response_text)
            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Gemini analysis completed",
                extra={"data": {
                    "trust_score": result.get("trust_score"),
                    "category": result.get("suggested_category"),
                    "duration_ms": duration_ms,
                    "model_used": self._current_model,
                    "vision_used": use_vision,
                    "image_count": len(image_parts),
                }},
            )

            # Build response with optional Vision fields
            response = {
                "trust_score": int(result.get("trust_score", 50)),
                "suggested_category": result.get("suggested_category", "OTHER"),
                "keywords": result.get("keywords", []),
                "reasoning": result.get("reasoning", ""),
                "is_spam_likely": result.get("is_spam_likely", False),
                "ai_analysis_failed": False,
                "vision_used": use_vision,
            }

            # Include Vision-specific fields if present
            if use_vision:
                response["image_analysis"] = result.get("image_analysis", "")
                response["image_authenticity"] = result.get("image_authenticity", "uncertain")

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Gemini analysis failed — using fallback values",
                extra={"data": {"error": str(e)[:200], "duration_ms": duration_ms}},
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
        if not self._api_keys and not config.GEMINI_API_KEY:
            return {"status": "degraded", "error": "No API keys configured"}

        try:
            api_key = self._current_key
            model_name = self._model_chain[0] if self._model_chain else config.GEMINI_MODEL
            client = self._get_client(api_key, model_name)
            response = client.generate_content(
                "Reply with exactly: OK",
                generation_config={"max_output_tokens": 10},
                request_options={
                    "timeout": config.GEMINI_TIMEOUT,
                },
            )
            return {
                "status": "healthy",
                "model": model_name,
                "available_keys": len(self._api_keys),
                "model_chain": self._model_chain,
            }
        except Exception as e:
            if self._is_rate_limited(e) or self._is_model_not_found(e):
                return {
                    "status": "degraded",
                    "error": str(e)[:100],
                    "available_keys": len(self._api_keys),
                    "model_chain": self._model_chain,
                }
            return {"status": "unhealthy", "error": str(e)[:100]}


# Module-level singleton
gemini_service = GeminiService()
