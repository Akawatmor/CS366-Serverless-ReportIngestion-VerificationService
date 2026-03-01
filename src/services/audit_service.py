"""
Audit Service — writes immutable audit log entries to the AuditLogs table.
Every status change, data edit, or soft-delete is recorded here.
"""
from __future__ import annotations

from typing import Any, Optional

import boto3

from src.config import config
from src.models.report import AuditLog
from src.models.enums import AuditActionType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AuditService:
    """Append-only audit trail for all report mutations."""

    def __init__(self, dynamodb_client=None):
        self.dynamodb = dynamodb_client or boto3.client("dynamodb", region_name=config.AWS_REGION)
        self.table_name = config.AUDIT_TABLE

    def log_status_change(
        self,
        report_id: str,
        actor_id: str,
        old_status: str,
        new_status: str,
        notes: str = "",
    ) -> str:
        """Record a status transition."""
        return self._write_log(
            report_id=report_id,
            actor_id=actor_id,
            action_type=AuditActionType.STATUS_CHANGE.value,
            previous_value={"status": old_status},
            new_value={"status": new_status, "notes": notes},
        )

    def log_soft_delete(
        self,
        report_id: str,
        deleted_by: str,
        reason: str,
    ) -> str:
        """Record a soft-delete action."""
        return self._write_log(
            report_id=report_id,
            actor_id=deleted_by,
            action_type=AuditActionType.SOFT_DELETE.value,
            previous_value=None,
            new_value={"reason": reason},
        )

    def log_ai_analysis(
        self,
        report_id: str,
        analysis_result: dict[str, Any],
    ) -> str:
        """Record the AI analysis result for traceability."""
        return self._write_log(
            report_id=report_id,
            actor_id="SYSTEM_AI",
            action_type=AuditActionType.AI_ANALYSIS.value,
            previous_value=None,
            new_value=analysis_result,
        )

    def _write_log(
        self,
        report_id: str,
        actor_id: str,
        action_type: str,
        previous_value: Optional[dict],
        new_value: Optional[dict],
    ) -> str:
        """Write a single audit log entry to DynamoDB."""
        entry = AuditLog(
            report_ref_id=report_id,
            actor_id=actor_id,
            action_type=action_type,
            previous_value=previous_value,
            new_value=new_value,
        )

        try:
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=entry.to_dynamodb_item(),
            )
            logger.info(
                "Audit log written",
                extra={"data": {
                    "log_id": entry.log_id,
                    "report_id": report_id,
                    "action": action_type,
                    "actor": actor_id,
                }},
            )
            return entry.log_id

        except Exception as e:
            logger.error(
                "Failed to write audit log — data may be lost",
                extra={"data": {"report_id": report_id, "action": action_type, "error": str(e)}},
            )
            raise
