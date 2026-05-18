"""
Event Publisher — publishes async events to Amazon EventBridge.

Two event types (matching the Async Contract in Service Proposal):
  1. ReportVerifiedEvent   → consumed by Incident Tracking Service
  2. ReportStatusChangedEvent → broadcast to Dashboard, Notification, etc.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EventPublisher:
    """Publish domain events to EventBridge."""

    def __init__(self, eventbridge_client=None):
        self.eventbridge = eventbridge_client or boto3.client(
            "events", region_name=config.AWS_REGION
        )
        self.bus_name = config.EVENT_BUS_NAME
        self.source = config.EVENT_SOURCE

    # ------------------------------------------------------------------
    # Event #1: ReportVerifiedEvent
    # ------------------------------------------------------------------

    def publish_report_verified(
        self,
        report_id: str,
        suggested_incident_data: dict[str, Any],
        verified_by: str,
        verification_notes: str = "",
        action: str = "CREATE_NEW_INCIDENT",
        target_incident_id: str | None = None,
    ) -> str:
        """
        Publish when a report is verified and should create/merge an Incident.

        Returns the event_id on success, or empty string on failure.
        """
        event_id = f"evt-{uuid.uuid4().hex[:16]}"

        detail = {
            "schemaVersion": "1.0",
            "report_ref_id": report_id,
            "suggested_incident_data": suggested_incident_data,
            "verified_by": verified_by,
            "verification_notes": verification_notes,
            "action": action,
        }
        if target_incident_id:
            detail["target_incident_id"] = target_incident_id

        return self._put_event(
            event_id=event_id,
            detail_type="ReportVerifiedEvent",
            detail=detail,
            action=action,
        )

    # ------------------------------------------------------------------
    # Event #2: ReportStatusChangedEvent
    # ------------------------------------------------------------------

    def publish_status_changed(
        self,
        report_id: str,
        old_status: str,
        new_status: str,
        changed_by: str,
        reason: str = "",
    ) -> str:
        """
        Broadcast whenever a report's status changes.

        Returns the event_id on success, or empty string on failure.
        """
        event_id = f"evt-{uuid.uuid4().hex[:16]}"

        detail = {
            "schemaVersion": "1.0",
            "report_id": report_id,
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason,
            "changed_by": changed_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return self._put_event(
            event_id=event_id,
            detail_type="ReportStatusChangedEvent",
            detail=detail,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _put_event(
        self,
        event_id: str,
        detail_type: str,
        detail: dict[str, Any],
        action: str | None = None,
    ) -> str:
        """Put a single event onto EventBridge."""
        try:
            entry: dict[str, Any] = {
                "Source": self.source,
                "DetailType": detail_type,
                "Detail": json.dumps(detail, ensure_ascii=False, default=str),
                "EventBusName": self.bus_name,
            }

            resp = self.eventbridge.put_events(Entries=[entry])

            failed = resp.get("FailedEntryCount", 0)
            if failed > 0:
                error_msg = resp["Entries"][0].get("ErrorMessage", "unknown")
                logger.error(
                    "EventBridge put_events partially failed",
                    extra={"data": {
                        "event_id": event_id,
                        "detail_type": detail_type,
                        "error": error_msg,
                    }},
                )
                return ""

            logger.info(
                "Event published",
                extra={"data": {
                    "event_id": event_id,
                    "detail_type": detail_type,
                    "bus": self.bus_name,
                }},
            )
            return event_id

        except Exception as e:
            logger.error(
                "Failed to publish event — consider Outbox pattern retry",
                extra={"data": {
                    "event_id": event_id,
                    "detail_type": detail_type,
                    "error": str(e),
                }},
            )
            return ""

    def health_check(self) -> dict[str, Any]:
        """Verify EventBridge bus exists."""
        try:
            self.eventbridge.describe_event_bus(Name=self.bus_name)
            return {"status": "healthy", "bus": self.bus_name}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
