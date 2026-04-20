"""
Unit tests for src/handlers/api_handler.py
Uses mocked DynamoDB (no real AWS calls).
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.handlers import api_handler
from src.handlers.api_handler import handler


class TestApiHandlerRouting:
    """Test that requests are routed to correct handlers."""

    @patch("src.handlers.api_handler.boto3")
    def test_get_changelog_rss_route(self, mock_boto3, api_gateway_event, lambda_context):
        """GET /v1/changelog.xml should return RSS XML payload."""
        mock_boto3.client.return_value = MagicMock()

        event = api_gateway_event(method="GET", path="/v1/changelog.xml")
        result = handler(event, lambda_context)

        assert result["statusCode"] == 200
        assert "application/rss+xml" in result["headers"]["Content-Type"]
        assert "<rss" in result["body"]

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

    @patch("src.handlers.api_handler.boto3")
    def test_priority_filter_high(self, mock_boto3, api_gateway_event, lambda_context):
        """GET /reports?priority=high should return only high-priority reports."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        mock_client.query.return_value = {
            "Items": [
                {
                    "report_id": {"S": "r-normal"},
                    "source_platform": {"S": "TWITTER"},
                    "reporter_id": {"S": "u-normal"},
                    "raw_content": {"S": "Minor road issue"},
                    "ingested_at": {"S": "2026-02-18T10:00:00Z"},
                    "trust_score": {"N": "70"},
                    "validation_status": {"S": "PENDING_REVIEW"},
                    "ai_analysis_failed": {"BOOL": False},
                    "priority": {"N": "0"},
                },
                {
                    "report_id": {"S": "r-high"},
                    "source_platform": {"S": "TWITTER"},
                    "reporter_id": {"S": "u-high"},
                    "raw_content": {"S": "Building collapse with people trapped"},
                    "ingested_at": {"S": "2026-02-18T10:05:00Z"},
                    "trust_score": {"N": "92"},
                    "validation_status": {"S": "PENDING_REVIEW"},
                    "ai_analysis_failed": {"BOOL": False},
                    "priority": {"N": "1"},
                },
            ],
            "Count": 2,
        }

        event = api_gateway_event(
            method="GET",
            path="/reports",
            query_params={"status": "PENDING_REVIEW", "priority": "high"},
        )
        result = handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["total_count"] == 1
        assert len(body["data"]) == 1
        assert body["data"][0]["report_id"] == "r-high"


class TestStatsAndUpload:
    """Tests for stats and upload-url enhancements."""

    @patch("src.handlers.api_handler.boto3")
    def test_stats_region_filter(self, mock_boto3, api_gateway_event, lambda_context):
        """GET /reports/stats?region=bkk should filter by configured region boundaries."""
        api_handler._STATS_CACHE.clear()

        bkk_item = {
            "report_id": {"S": "r-bkk-1"},
            "validation_status": {"S": "PENDING_REVIEW"},
            "ingested_at": {"S": "2026-02-18T10:00:00Z"},
            "ai_analysis_tags": {"L": [{"S": "fire"}]},
            "suggested_category": {"S": "FIRE"},
            "geo_location": {"M": {"lat": {"N": "13.7563"}, "lon": {"N": "100.5018"}}},
        }
        outside_item = {
            "report_id": {"S": "r-cnx-1"},
            "validation_status": {"S": "VERIFIED"},
            "ingested_at": {"S": "2026-02-18T10:10:00Z"},
            "ai_analysis_tags": {"L": [{"S": "flood"}]},
            "suggested_category": {"S": "FLOOD"},
            "geo_location": {"M": {"lat": {"N": "18.7883"}, "lon": {"N": "98.9853"}}},
        }

        def query_side_effect(**kwargs):
            status = kwargs["ExpressionAttributeValues"][":status"]["S"]
            if status == "PENDING_REVIEW":
                return {"Items": [bkk_item]}
            if status == "VERIFIED":
                return {"Items": [outside_item]}
            return {"Items": []}

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.query.side_effect = query_side_effect

        event = api_gateway_event(
            method="GET",
            path="/reports/stats",
            query_params={"region": "bkk", "timeframe": "today"},
        )
        result = handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["summary"]["total_received_today"] == 1
        assert body["summary"]["pending_review"] == 1
        assert body["summary"]["verified_incidents"] == 0
        assert len(body["heatmap_data"]) == 1
        assert body["heatmap_data"][0]["region"] == "bkk"

    @patch("src.handlers.api_handler.boto3")
    def test_upload_url_rejects_oversized_file(self, mock_boto3, api_gateway_event, lambda_context):
        """POST /upload-url should reject files over configured max size."""
        with patch.object(api_handler.config, "MEDIA_BUCKET", "test-media-bucket"), \
             patch.object(api_handler.config, "UPLOAD_MAX_FILE_BYTES", 10):
            event = api_gateway_event(
                method="POST",
                path="/v1/upload-url",
                body={
                    "filename": "photo.jpg",
                    "content_type": "image/jpeg",
                    "file_size_bytes": 100,
                },
            )
            result = handler(event, lambda_context)

        assert result["statusCode"] == 400

    @patch("src.handlers.api_handler.boto3")
    def test_upload_url_success_includes_media_id(self, mock_boto3, api_gateway_event, lambda_context):
        """POST /upload-url success response should include media_id and upload_url."""
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://signed-upload-url"
        mock_boto3.client.return_value = mock_client

        with patch.object(api_handler.config, "MEDIA_BUCKET", "test-media-bucket"), \
             patch.object(api_handler.config, "AWS_REGION", "us-east-1"):
            event = api_gateway_event(
                method="POST",
                path="/v1/upload-url",
                body={
                    "filename": "photo.jpg",
                    "content_type": "image/jpeg",
                    "file_size_bytes": 1024,
                },
            )
            result = handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["upload_url"] == "https://signed-upload-url"
        assert body["media_id"].startswith("m-")


class TestVerifiedEventPayload:
    """Tests for enriched ReportVerifiedEvent payload content."""

    @patch("src.handlers.api_handler.reverse_geocoding_service.reverse_geocode", return_value="Bangkok, Thailand")
    @patch("src.handlers.api_handler.EventPublisher")
    @patch("src.handlers.api_handler.AuditService")
    @patch("src.handlers.api_handler.boto3")
    def test_verify_enriches_event_payload(
        self,
        mock_boto3,
        mock_audit,
        mock_events,
        mock_reverse,
        api_gateway_event,
        lambda_context,
    ):
        """VERIFIED flow should publish dynamic severity, actual reporter_count, and address_text."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        mock_client.get_item.return_value = {
            "Item": {
                "report_id": {"S": "r-verify-1"},
                "source_platform": {"S": "TWITTER"},
                "reporter_id": {"S": "u-1"},
                "raw_content": {"S": "ไฟไหม้อาคาร มีคนติดอยู่ ขอความช่วยเหลือด่วน"},
                "media_urls": {"L": [{"S": "https://example.com/photo.jpg"}]},
                "geo_location": {"M": {"lat": {"N": "13.7563"}, "lon": {"N": "100.5018"}}},
                "ai_analysis_tags": {"L": [{"S": "ไฟไหม้"}, {"S": "ติดอยู่"}]},
                "suggested_category": {"S": "FIRE"},
                "potential_duplicates": {"L": [{"S": "r-dup-1"}, {"S": "r-dup-2"}]},
                "ingested_at": {"S": "2026-02-18T10:00:00Z"},
                "trust_score": {"N": "95"},
                "validation_status": {"S": "PENDING_REVIEW"},
                "ai_analysis_failed": {"BOOL": False},
            }
        }
        mock_client.update_item.return_value = {}
        mock_client.batch_get_item.return_value = {
            "Responses": {
                "test-reports": [
                    {"report_id": {"S": "r-dup-1"}, "reporter_id": {"S": "u-2"}},
                    {"report_id": {"S": "r-dup-2"}, "reporter_id": {"S": "u-1"}},
                ]
            }
        }

        event = api_gateway_event(
            method="PATCH",
            path="/reports/{report_id}",
            path_params={"report_id": "r-verify-1"},
            body={
                "validation_status": "VERIFIED",
                "reviewer_id": "officer_007",
                "reviewer_notes": "Confirmed",
            },
        )
        result = handler(event, lambda_context)

        assert result["statusCode"] == 200

        publish_kwargs = mock_events.return_value.publish_report_verified.call_args.kwargs
        incident_data = publish_kwargs["suggested_incident_data"]

        assert incident_data["severity_level"] >= 4
        assert incident_data["reporter_count"] == 2
        assert incident_data["address_text"] == "Bangkok, Thailand"
