"""
Deduplication Service — detects duplicate reports based on:
  1. source_external_id (Idempotency check)
  2. Geospatial proximity (within DEDUP_RADIUS_METERS)
  3. Time window (within DEDUP_TIME_WINDOW_MINUTES)
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DedupService:
    """Check incoming reports against existing data for duplicates."""

    def __init__(self, dynamodb_client=None):
        self.dynamodb = dynamodb_client or boto3.client("dynamodb", region_name=config.AWS_REGION)
        self.table_name = config.REPORTS_TABLE

    # ------------------------------------------------------------------
    # 1) Idempotency — same external ID means same report
    # ------------------------------------------------------------------

    def check_external_id(
        self,
        source_external_id: str | None,
        exclude_report_id: str | None = None,
    ) -> str | None:
        """
        If source_external_id already exists, return the existing report_id.
        Returns None if no duplicate found or if source_external_id is empty.
        """
        if not source_external_id:
            return None

        try:
            resp = self.dynamodb.query(
                TableName=self.table_name,
                IndexName="gsi_source_external_id",
                KeyConditionExpression="source_external_id = :sid",
                ExpressionAttributeValues={":sid": {"S": source_external_id}},
                Limit=1,
                ProjectionExpression="report_id",
            )
            items = resp.get("Items", [])
            if items:
                existing_id = items[0]["report_id"]["S"]
                if existing_id == exclude_report_id:
                    return None
                logger.info(
                    "Duplicate by external_id",
                    extra={"data": {
                        "source_external_id": source_external_id,
                        "existing_report_id": existing_id,
                    }},
                )
                return existing_id
        except Exception as e:
            logger.error(f"Error checking external_id: {e}", exc_info=True)

        return None

    # ------------------------------------------------------------------
    # 2) Geo + Time proximity
    # ------------------------------------------------------------------

    def find_nearby_reports(
        self,
        lat: float,
        lon: float,
        event_time: str | None = None,
        radius_meters: int | None = None,
        time_window_minutes: int | None = None,
        exclude_report_id: str | None = None,
    ) -> list[str]:
        """
        Find reports within radius_meters and time_window_minutes.
        Returns list of report_ids that are potential duplicates.

        Note: DynamoDB doesn't support geo queries natively. We use a
        simplified approach — scan PENDING_REVIEW items and compute
        Haversine distance in-memory. For production, consider
        ElastiCache/OpenSearch with geo indexing.
        """
        radius = radius_meters or config.DEDUP_RADIUS_METERS
        window = time_window_minutes or config.DEDUP_TIME_WINDOW_MINUTES
        duplicates: list[str] = []
        seen_ids: set[str] = set()

        try:
            # Query recent RECEIVED + PENDING_REVIEW reports
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window * 2)

            for status in ("RECEIVED", "PENDING_REVIEW"):
                resp = self.dynamodb.query(
                    TableName=self.table_name,
                    IndexName="gsi_status_ingested",
                    KeyConditionExpression=(
                        "validation_status = :status AND ingested_at > :cutoff"
                    ),
                    ExpressionAttributeValues={
                        ":status": {"S": status},
                        ":cutoff": {"S": cutoff_time.isoformat()},
                    },
                    ProjectionExpression="report_id, geo_location, ingested_at",
                    Limit=200,
                )

                for item in resp.get("Items", []):
                    report_id = item.get("report_id", {}).get("S")
                    if not report_id or report_id in seen_ids or report_id == exclude_report_id:
                        continue
                    if "geo_location" not in item:
                        continue

                    item_lat = float(item["geo_location"]["M"]["lat"]["N"])
                    item_lon = float(item["geo_location"]["M"]["lon"]["N"])

                    distance = _haversine_meters(lat, lon, item_lat, item_lon)
                    if distance <= radius:
                        # Check time window too
                        if event_time and "ingested_at" in item:
                            if _within_time_window(event_time, item["ingested_at"]["S"], window):
                                duplicates.append(report_id)
                                seen_ids.add(report_id)
                        else:
                            # No timestamp to compare — just use geo
                            duplicates.append(report_id)
                            seen_ids.add(report_id)

            if duplicates:
                logger.info(
                    "Found nearby duplicates",
                    extra={"data": {
                        "lat": lat, "lon": lon,
                        "count": len(duplicates),
                        "report_ids": duplicates[:5],
                    }},
                )

        except Exception as e:
            logger.error(f"Error in dedup geo query: {e}", exc_info=True)

        return duplicates

    # ------------------------------------------------------------------
    # 3) Content similarity
    # ------------------------------------------------------------------

    def find_content_similar_reports(
        self,
        raw_content: str,
        event_time: str | None = None,
        time_window_minutes: int | None = None,
        similarity_threshold: float | None = None,
        exclude_report_id: str | None = None,
    ) -> list[str]:
        """
        Find reports with similar text content within a recent time window.

        Uses Jaccard similarity over normalized token sets. For languages
        without whitespace tokenization, character bigrams are also used.
        """
        if not raw_content or len(raw_content.strip()) < 6:
            return []

        window = time_window_minutes or config.DEDUP_TIME_WINDOW_MINUTES
        threshold = similarity_threshold or config.CONTENT_SIMILARITY_THRESHOLD
        source_tokens = _normalize_tokens(raw_content)
        if not source_tokens:
            return []

        duplicates: list[str] = []
        seen_ids: set[str] = set()
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window * 2)

        try:
            for status in ("RECEIVED", "PENDING_REVIEW", "VERIFIED"):
                resp = self.dynamodb.query(
                    TableName=self.table_name,
                    IndexName="gsi_status_ingested",
                    KeyConditionExpression=(
                        "validation_status = :status AND ingested_at > :cutoff"
                    ),
                    ExpressionAttributeValues={
                        ":status": {"S": status},
                        ":cutoff": {"S": cutoff_time.isoformat()},
                    },
                    ProjectionExpression="report_id, raw_content, ingested_at",
                    Limit=200,
                )

                for item in resp.get("Items", []):
                    report_id = item.get("report_id", {}).get("S")
                    if (
                        not report_id
                        or report_id in seen_ids
                        or report_id == exclude_report_id
                    ):
                        continue

                    existing_text = item.get("raw_content", {}).get("S", "")
                    similarity = _jaccard_similarity(source_tokens, _normalize_tokens(existing_text))
                    if similarity < threshold:
                        continue

                    if event_time and "ingested_at" in item:
                        if not _within_time_window(event_time, item["ingested_at"]["S"], window):
                            continue

                    seen_ids.add(report_id)
                    duplicates.append(report_id)

            if duplicates:
                logger.info(
                    "Found content-similar reports",
                    extra={"data": {
                        "threshold": threshold,
                        "count": len(duplicates),
                        "report_ids": duplicates[:5],
                    }},
                )

        except Exception as e:
            logger.error(f"Error in content similarity query: {e}", exc_info=True)

        return duplicates


# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------

def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates in meters."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _within_time_window(time_a: str, time_b: str, window_minutes: int) -> bool:
    """Check if two ISO8601 timestamps are within window_minutes of each other."""
    try:
        t1 = datetime.fromisoformat(time_a.replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(time_b.replace("Z", "+00:00"))
        return abs((t1 - t2).total_seconds()) <= window_minutes * 60
    except Exception:
        return False


def _normalize_tokens(text: str) -> set[str]:
    """Normalize text into token set used by similarity checks."""
    lowered = text.lower()
    normalized = re.sub(r"[^\w\s]", " ", lowered, flags=re.UNICODE)
    words = [w for w in normalized.split() if len(w) >= 2]
    tokens = set(words)

    # Add character bigrams for languages that may not use spaces.
    compact = "".join(ch for ch in normalized if not ch.isspace())
    if len(compact) >= 4:
        tokens.update(compact[i:i + 2] for i in range(len(compact) - 1))

    return tokens


def _jaccard_similarity(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Compute Jaccard similarity in [0, 1]."""
    if not tokens_a or not tokens_b:
        return 0.0
    inter = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    if not union:
        return 0.0
    return len(inter) / len(union)
