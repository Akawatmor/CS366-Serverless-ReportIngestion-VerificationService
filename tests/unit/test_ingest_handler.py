"""
Unit tests for src/handlers/ingest_handler.py
"""
import json
from unittest.mock import MagicMock, patch

from src.handlers.ingest_handler import handler


class TestIngestHandler:
    """POST /reports should persist a placeholder before queueing async work."""

    @patch("src.handlers.ingest_handler.boto3")
    def test_ingest_creates_placeholder_and_queues(
        self,
        mock_boto3,
        api_gateway_event,
        lambda_context,
        sample_ingest_payload,
    ):
        mock_dynamodb = MagicMock()
        mock_sqs = MagicMock()
        mock_boto3.client.side_effect = lambda service_name, region_name=None: {
            "dynamodb": mock_dynamodb,
            "sqs": mock_sqs,
        }[service_name]

        event = api_gateway_event(method="POST", path="/v1/reports", body=sample_ingest_payload)
        result = handler(event, lambda_context)

        assert result["statusCode"] == 202
        body = json.loads(result["body"])
        assert body["status"] == "QUEUED"

        mock_dynamodb.put_item.assert_called_once()
        placeholder_item = mock_dynamodb.put_item.call_args.kwargs["Item"]
        assert placeholder_item["report_id"]["S"] == body["report_id"]
        assert placeholder_item["validation_status"]["S"] == "RECEIVED"
        assert placeholder_item["reporter_id"]["S"] == sample_ingest_payload["reporter_id"]

        mock_sqs.send_message.assert_called_once()

    @patch("src.handlers.ingest_handler.boto3")
    def test_ingest_cleans_up_placeholder_when_enqueue_fails(
        self,
        mock_boto3,
        api_gateway_event,
        lambda_context,
        sample_ingest_payload,
    ):
        mock_dynamodb = MagicMock()
        mock_sqs = MagicMock()
        mock_sqs.send_message.side_effect = RuntimeError("queue unavailable")
        mock_boto3.client.side_effect = lambda service_name, region_name=None: {
            "dynamodb": mock_dynamodb,
            "sqs": mock_sqs,
        }[service_name]

        event = api_gateway_event(method="POST", path="/v1/reports", body=sample_ingest_payload)
        result = handler(event, lambda_context)

        assert result["statusCode"] == 500
        mock_dynamodb.put_item.assert_called_once()
        mock_dynamodb.delete_item.assert_called_once()