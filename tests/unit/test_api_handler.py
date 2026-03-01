"""
Unit tests for src/handlers/api_handler.py
Uses mocked DynamoDB (no real AWS calls).
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.handlers.api_handler import handler


class TestApiHandlerRouting:
    """Test that requests are routed to correct handlers."""

    @patch("src.handlers.api_handler.boto3")
    def test_get_reports_route(self, mock_boto3, api_gateway_event, lambda_context):
        """GET /reports should hit list reports handler."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.query.return_value = {"Items": [], "Count": 0}

        event = api_gateway_event(method="GET", path="/reports", query_params={"status": "PENDING_REVIEW"})
        result = handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "data" in body
        assert "total_count" in body

    @patch("src.handlers.api_handler.boto3")
    def test_get_report_detail_route(self, mock_boto3, api_gateway_event, lambda_context):
        """GET /reports/{report_id} should return detail."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_item.return_value = {
            "Item": {
                "report_id": {"S": "r-test123"},
                "source_platform": {"S": "TWITTER"},
                "reporter_id": {"S": "@test"},
                "raw_content": {"S": "Test content"},
                "ingested_at": {"S": "2026-02-18T10:00:00Z"},
                "trust_score": {"N": "85"},
                "validation_status": {"S": "PENDING_REVIEW"},
                "ai_analysis_failed": {"BOOL": False},
            }
        }

        event = api_gateway_event(
            method="GET",
            path="/reports/{report_id}",
            path_params={"report_id": "r-test123"},
        )
        result = handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["report_id"] == "r-test123"

    @patch("src.handlers.api_handler.boto3")
    def test_get_report_not_found(self, mock_boto3, api_gateway_event, lambda_context):
        """GET /reports/{report_id} should return 404 if not exists."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_item.return_value = {}

        event = api_gateway_event(
            method="GET",
            path="/reports/{report_id}",
            path_params={"report_id": "r-nonexistent"},
        )
        result = handler(event, lambda_context)
        assert result["statusCode"] == 404

    @patch("src.handlers.api_handler.boto3")
    def test_delete_report_missing_body(self, mock_boto3, api_gateway_event, lambda_context):
        """DELETE without reason/deleted_by should return 400."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        event = api_gateway_event(
            method="DELETE",
            path="/reports/{report_id}",
            path_params={"report_id": "r-test123"},
            body={},
        )
        result = handler(event, lambda_context)
        assert result["statusCode"] == 400

    def test_options_returns_cors(self, api_gateway_event, lambda_context):
        """OPTIONS should return 200 for CORS preflight."""
        event = api_gateway_event(method="OPTIONS", path="/reports")
        result = handler(event, lambda_context)
        assert result["statusCode"] == 200

    def test_unknown_route_returns_404(self, api_gateway_event, lambda_context):
        """Unknown routes should return 404."""
        event = api_gateway_event(method="PUT", path="/unknown")
        result = handler(event, lambda_context)
        assert result["statusCode"] == 404


class TestVerifyHandler:
    """Test PATCH /reports/{report_id} verification logic."""

    @patch("src.handlers.api_handler.EventPublisher")
    @patch("src.handlers.api_handler.AuditService")
    @patch("src.handlers.api_handler.boto3")
    def test_verify_success(self, mock_boto3, mock_audit, mock_events, api_gateway_event, lambda_context):
        """Valid VERIFIED request should update status and return 200."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        # Mock get_item (current state)
        mock_client.get_item.return_value = {
            "Item": {
                "report_id": {"S": "r-test123"},
                "source_platform": {"S": "TWITTER"},
                "reporter_id": {"S": "@test"},
                "raw_content": {"S": "Fire!"},
                "ingested_at": {"S": "2026-02-18T10:00:00Z"},
                "trust_score": {"N": "85"},
                "validation_status": {"S": "PENDING_REVIEW"},
                "ai_analysis_failed": {"BOOL": False},
            }
        }

        # Mock update_item success
        mock_client.update_item.return_value = {}

        event = api_gateway_event(
            method="PATCH",
            path="/reports/{report_id}",
            path_params={"report_id": "r-test123"},
            body={
                "validation_status": "VERIFIED",
                "reviewer_id": "officer_007",
                "reviewer_notes": "Confirmed",
            },
        )
        result = handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["validation_status"] == "VERIFIED"
        assert body["action_taken"] == "TRIGGER_NEW_INCIDENT"

    @patch("src.handlers.api_handler.boto3")
    def test_verify_invalid_transition(self, mock_boto3, api_gateway_event, lambda_context):
        """Cannot transition already VERIFIED report."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_item.return_value = {
            "Item": {
                "report_id": {"S": "r-test123"},
                "source_platform": {"S": "TWITTER"},
                "reporter_id": {"S": "@test"},
                "raw_content": {"S": "Fire!"},
                "ingested_at": {"S": "2026-02-18T10:00:00Z"},
                "trust_score": {"N": "85"},
                "validation_status": {"S": "VERIFIED"},
                "ai_analysis_failed": {"BOOL": False},
            }
        }

        event = api_gateway_event(
            method="PATCH",
            path="/reports/{report_id}",
            path_params={"report_id": "r-test123"},
            body={
                "validation_status": "SPAM",
                "reviewer_id": "officer_007",
            },
        )
        result = handler(event, lambda_context)
        assert result["statusCode"] == 409

    @patch("src.handlers.api_handler.boto3")
    def test_verify_missing_reviewer_id(self, mock_boto3, api_gateway_event, lambda_context):
        """VERIFIED without reviewer_id should return 400."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        event = api_gateway_event(
            method="PATCH",
            path="/reports/{report_id}",
            path_params={"report_id": "r-test123"},
            body={"validation_status": "VERIFIED"},
        )
        result = handler(event, lambda_context)
        assert result["statusCode"] == 400


class TestListReports:
    """Test GET /reports with query params."""

    @patch("src.handlers.api_handler.boto3")
    def test_invalid_query_params(self, mock_boto3, api_gateway_event, lambda_context):
        """Invalid status should return 400."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        event = api_gateway_event(
            method="GET",
            path="/reports",
            query_params={"status": "INVALID_STATUS"},
        )
        result = handler(event, lambda_context)
        assert result["statusCode"] == 400
