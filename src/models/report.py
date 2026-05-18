"""
Report model — dataclass that maps to DynamoDB Reports Table items.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from src.models.enums import ValidationStatus, SourcePlatform


def _generate_report_id() -> str:
    return f"r-{uuid.uuid4().hex[:12]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sensor_data_to_dynamodb_map(sensor_data: dict) -> dict:
    result: dict = {}
    for key, value in sensor_data.items():
        if value is None:
            continue
        if isinstance(value, bool):
            result[key] = {"BOOL": value}
        elif isinstance(value, (int, float)):
            result[key] = {"N": str(value)}
        else:
            result[key] = {"S": str(value)}
    return result


def _sensor_data_from_dynamodb_map(sensor_data_map: dict) -> dict:
    result: dict = {}
    for key, value in sensor_data_map.items():
        if "S" in value:
            result[key] = value["S"]
        elif "N" in value:
            number = value["N"]
            result[key] = float(number) if "." in number else int(number)
        elif "BOOL" in value:
            result[key] = value["BOOL"]
    return result


@dataclass
class GeoLocation:
    lat: float
    lon: float

    def to_dict(self) -> dict:
        return {"lat": str(self.lat), "lon": str(self.lon)}

    @classmethod
    def from_dict(cls, data: dict) -> GeoLocation:
        return cls(lat=float(data["lat"]), lon=float(data["lon"]))


@dataclass
class Report:
    """Primary data entity owned by this service."""

    # Identifiers
    report_id: str = field(default_factory=_generate_report_id)

    # Source info
    source_platform: str = SourcePlatform.OFFICIAL_APP.value
    source_external_id: Optional[str] = None
    reporter_id: str = ""

    # Content
    raw_content: str = ""
    media_urls: list[str] = field(default_factory=list)
    sensor_data: Optional[dict] = None
    geo_location: Optional[GeoLocation] = None

    # Timestamps
    event_timestamp: Optional[str] = None       # when the event occurred
    ingested_at: str = field(default_factory=_now_iso)

    # AI Analysis
    trust_score: int = 0
    ai_analysis_tags: list[str] = field(default_factory=list)
    ai_reasoning: str = ""
    suggested_category: str = ""
    ai_analysis_failed: bool = False
    priority: int = 0

    # Status
    validation_status: str = ValidationStatus.RECEIVED.value
    verified_by: Optional[str] = None
    verification_notes: Optional[str] = None

    # Links
    linked_incident_id: Optional[str] = None
    potential_duplicates: list[str] = field(default_factory=list)

    def to_dynamodb_item(self) -> dict:
        """Convert to a flat dict suitable for DynamoDB put_item."""
        item = {
            "report_id": {"S": self.report_id},
            "source_platform": {"S": self.source_platform},
            "reporter_id": {"S": self.reporter_id},
            "raw_content": {"S": self.raw_content},
            "ingested_at": {"S": self.ingested_at},
            "trust_score": {"N": str(self.trust_score)},
            "validation_status": {"S": self.validation_status},
            "ai_analysis_failed": {"BOOL": self.ai_analysis_failed},
            "priority": {"N": str(self.priority)},
        }
        if self.source_external_id:
            item["source_external_id"] = {"S": self.source_external_id}
        if self.media_urls:
            item["media_urls"] = {"L": [{"S": u} for u in self.media_urls]}
        if self.sensor_data:
            item["sensor_data"] = {"M": _sensor_data_to_dynamodb_map(self.sensor_data)}
        if self.geo_location:
            item["geo_location"] = {"M": {
                "lat": {"N": str(self.geo_location.lat)},
                "lon": {"N": str(self.geo_location.lon)},
            }}
        if self.event_timestamp:
            item["event_timestamp"] = {"S": self.event_timestamp}
        if self.ai_analysis_tags:
            item["ai_analysis_tags"] = {"L": [{"S": t} for t in self.ai_analysis_tags]}
        if self.ai_reasoning:
            item["ai_reasoning"] = {"S": self.ai_reasoning}
        if self.suggested_category:
            item["suggested_category"] = {"S": self.suggested_category}
        if self.verified_by:
            item["verified_by"] = {"S": self.verified_by}
        if self.verification_notes:
            item["verification_notes"] = {"S": self.verification_notes}
        if self.linked_incident_id:
            item["linked_incident_id"] = {"S": self.linked_incident_id}
        if self.potential_duplicates:
            item["potential_duplicates"] = {"L": [{"S": d} for d in self.potential_duplicates]}
        return item

    @classmethod
    def from_dynamodb_item(cls, item: dict) -> Report:
        """Parse a DynamoDB item back into a Report object."""
        geo = None
        if "geo_location" in item:
            geo_m = item["geo_location"]["M"]
            geo = GeoLocation(
                lat=float(geo_m["lat"]["N"]),
                lon=float(geo_m["lon"]["N"]),
            )

        return cls(
            report_id=item["report_id"]["S"],
            source_platform=item["source_platform"]["S"],
            source_external_id=item.get("source_external_id", {}).get("S"),
            reporter_id=item["reporter_id"]["S"],
            raw_content=item["raw_content"]["S"],
            media_urls=[u["S"] for u in item.get("media_urls", {}).get("L", [])],
            sensor_data=_sensor_data_from_dynamodb_map(item["sensor_data"]["M"]) if "sensor_data" in item else None,
            geo_location=geo,
            event_timestamp=item.get("event_timestamp", {}).get("S"),
            ingested_at=item["ingested_at"]["S"],
            trust_score=int(item.get("trust_score", {}).get("N", 0)),
            ai_analysis_tags=[t["S"] for t in item.get("ai_analysis_tags", {}).get("L", [])],
            ai_reasoning=item.get("ai_reasoning", {}).get("S", ""),
            suggested_category=item.get("suggested_category", {}).get("S", ""),
            ai_analysis_failed=item.get("ai_analysis_failed", {}).get("BOOL", False),
            priority=int(item.get("priority", {}).get("N", 0)),
            validation_status=item["validation_status"]["S"],
            verified_by=item.get("verified_by", {}).get("S"),
            verification_notes=item.get("verification_notes", {}).get("S"),
            linked_incident_id=item.get("linked_incident_id", {}).get("S"),
            potential_duplicates=[d["S"] for d in item.get("potential_duplicates", {}).get("L", [])],
        )

    def to_api_summary(self) -> dict:
        """Short representation for list endpoints."""
        from datetime import datetime as dt
        try:
            ingested = dt.fromisoformat(self.ingested_at.replace("Z", "+00:00"))
            delta = datetime.now(timezone.utc) - ingested
            minutes = int(delta.total_seconds() / 60)
            if minutes < 60:
                time_ago = f"{minutes} mins"
            else:
                time_ago = f"{minutes // 60}h {minutes % 60}m"
        except Exception:
            time_ago = "unknown"

        return {
            "report_id": self.report_id,
            "content": (self.raw_content[:80] + "...") if len(self.raw_content) > 80 else self.raw_content,
            "trust_score": self.trust_score,
            "suggested_category": self.suggested_category,
            "priority": "HIGH" if self.priority > 0 else "NORMAL",
            "time_ago": time_ago,
        }

    def to_api_detail(self) -> dict:
        """Full representation for detail endpoint."""
        result = {
            "report_id": self.report_id,
            "reporter_info": {
                "source": self.source_platform,
                "reporter_id": self.reporter_id,
                "source_external_id": self.source_external_id,
            },
            "content": {
                "text": self.raw_content,
                "images": [u for u in self.media_urls if u.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))],
                "video": next((u for u in self.media_urls if u.endswith((".mp4", ".mov", ".avi"))), None),
                "sensor_data": self.sensor_data,
            },
            "analysis": {
                "trust_score": self.trust_score,
                "ai_reasoning": self.ai_reasoning,
                "suggested_category": self.suggested_category,
                "ai_analysis_tags": self.ai_analysis_tags,
                "ai_analysis_failed": self.ai_analysis_failed,
                "potential_duplicates": self.potential_duplicates,
            },
            "priority": "HIGH" if self.priority > 0 else "NORMAL",
            "geo_location": self.geo_location.to_dict() if self.geo_location else None,
            "status": self.validation_status,
            "verified_by": self.verified_by,
            "verification_notes": self.verification_notes,
            "linked_incident_id": self.linked_incident_id,
            "created_at": self.ingested_at,
            "event_timestamp": self.event_timestamp,
        }
        return result


@dataclass
class AuditLog:
    """Audit log entry for tracking all changes to reports."""

    log_id: str = field(default_factory=lambda: f"log-{uuid.uuid4().hex[:12]}")
    report_ref_id: str = ""
    actor_id: str = ""
    action_type: str = ""
    previous_value: Optional[dict] = None
    new_value: Optional[dict] = None
    timestamp: str = field(default_factory=_now_iso)

    def to_dynamodb_item(self) -> dict:
        import json
        item = {
            "log_id": {"S": self.log_id},
            "report_ref_id": {"S": self.report_ref_id},
            "actor_id": {"S": self.actor_id},
            "action_type": {"S": self.action_type},
            "timestamp": {"S": self.timestamp},
        }
        if self.new_value is not None:
            item["new_value"] = {"S": json.dumps(self.new_value, ensure_ascii=False)}
        if self.previous_value is not None:
            item["previous_value"] = {"S": json.dumps(self.previous_value, ensure_ascii=False)}
        return item
