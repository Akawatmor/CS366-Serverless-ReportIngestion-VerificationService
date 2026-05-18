"""
Integration tests for SQS → Ingestion Worker flow using moto mock.
"""
import json
import pytest
import boto3
from unittest.mock import patch, MagicMock
from moto import mock_aws

from src.config import config
from src.models.report import GeoLocation, Report


@pytest.fixture
def aws_environment():
    """Set up mocked SQS + DynamoDB environment."""
    with mock_aws():
        region = "us-east-1"

        # Create SQS queues
        sqs = boto3.client("sqs", region_name=region)
        queue = sqs.create_queue(QueueName="test-ingestion-queue")
        queue_url = queue["QueueUrl"]

        dlq = sqs.create_queue(QueueName="test-ingestion-dlq")
        dlq_url = dlq["QueueUrl"]

        # Create DynamoDB tables
        dynamodb = boto3.client("dynamodb", region_name=region)
        dynamodb.create_table(
            TableName=config.REPORTS_TABLE,
            KeySchema=[{"AttributeName": "report_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "report_id", "AttributeType": "S"},
                {"AttributeName": "validation_status", "AttributeType": "S"},
                {"AttributeName": "ingested_at", "AttributeType": "S"},
                {"AttributeName": "source_external_id", "AttributeType": "S"},
                {"AttributeName": "reporter_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi_status_ingested",
                    "KeySchema": [
                        {"AttributeName": "validation_status", "KeyType": "HASH"},
                        {"AttributeName": "ingested_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "gsi_source_external_id",
                    "KeySchema": [
                        {"AttributeName": "source_external_id", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "KEYS_ONLY"},
                },
                {
                    "IndexName": "gsi_reporter",
                    "KeySchema": [
                        {"AttributeName": "reporter_id", "KeyType": "HASH"},
                        {"AttributeName": "ingested_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        dynamodb.create_table(
            TableName=config.AUDIT_TABLE,
            KeySchema=[{"AttributeName": "log_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "log_id", "AttributeType": "S"},
                {"AttributeName": "report_ref_id", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi_report_timestamp",
                    "KeySchema": [
                        {"AttributeName": "report_ref_id", "KeyType": "HASH"},
                        {"AttributeName": "timestamp", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        dynamodb.create_table(
            TableName=config.STATS_TABLE,
            KeySchema=[{"AttributeName": "stat_key", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "stat_key", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield {
            "sqs": sqs,
            "dynamodb": dynamodb,
            "queue_url": queue_url,
            "dlq_url": dlq_url,
        }


class TestSQSFlow:
    """Test the SQS message → Worker processing flow."""

    def test_send_message_to_queue(self, aws_environment, sample_sqs_message):
        """Verify message can be sent and received from SQS."""
        sqs = aws_environment["sqs"]
        queue_url = aws_environment["queue_url"]

        # Send
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(sample_sqs_message),
        )

        # Receive
        resp = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
        messages = resp.get("Messages", [])
        assert len(messages) == 1

        body = json.loads(messages[0]["Body"])
        assert body["report_id"] == sample_sqs_message["report_id"]

    @patch("src.handlers.ingestion_worker.gemini_service")
    def test_worker_processes_message(self, mock_gemini, aws_environment, sample_sqs_message):
        """Worker should process SQS message and write to DynamoDB."""
        # Mock Gemini response — content_score only (0-30)
        # Expected final trust_score: 25(content) + 8(TWITTER) + 10(history) + 8(media) + 10(geo) = 61
        mock_gemini.analyze_report.return_value = {
            "content_score": 25,
            "content_score_reasoning": "Street name and smoke mentioned",
            "suggested_category": "FIRE",
            "keywords": ["fire", "smoke"],
            "spam_signals": [],
            "is_spam_likely": False,
            "ai_analysis_failed": False,
            "vision_used": False,
        }

        placeholder = Report(
            report_id=sample_sqs_message["report_id"],
            source_platform=sample_sqs_message["reporter_source"],
            source_external_id=sample_sqs_message["source_external_id"],
            reporter_id=sample_sqs_message["reporter_id"],
            raw_content=sample_sqs_message["raw_content"],
            media_urls=sample_sqs_message["media_urls"],
            geo_location=GeoLocation(
                lat=sample_sqs_message["geo_location"]["lat"],
                lon=sample_sqs_message["geo_location"]["lon"],
            ),
            event_timestamp=sample_sqs_message["timestamp"],
            ingested_at=sample_sqs_message["ingested_at"],
            validation_status="RECEIVED",
        )
        aws_environment["dynamodb"].put_item(
            TableName=config.REPORTS_TABLE,
            Item=placeholder.to_dynamodb_item(),
        )

        # Build SQS event format
        sqs_event = {
            "Records": [
                {
                    "messageId": "msg-001",
                    "body": json.dumps(sample_sqs_message),
                    "receiptHandle": "handle-001",
                }
            ]
        }

        # Patch boto3 to use our mocked clients
        with patch("src.handlers.ingestion_worker.boto3") as mock_boto3, \
             patch("src.services.event_publisher.boto3") as mock_eb_boto3:
            mock_boto3.client.return_value = aws_environment["dynamodb"]
            mock_eb_client = MagicMock()
            mock_eb_client.put_events.return_value = {"FailedEntryCount": 0, "Entries": [{}]}
            mock_eb_boto3.client.return_value = mock_eb_client

            from src.handlers.ingestion_worker import handler
            result = handler(sqs_event, None)

        assert result["batchItemFailures"] == []

        # Verify report written to DB
        resp = aws_environment["dynamodb"].get_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": sample_sqs_message["report_id"]}},
        )
        assert "Item" in resp
        item = resp["Item"]
        assert item["trust_score"]["N"] == "61"  # 25+8+10+8+10 = 61
        assert item["validation_status"]["S"] == "PENDING_REVIEW"

    @patch("src.handlers.ingestion_worker.gemini_service")
    def test_worker_auto_rejects_spam(self, mock_gemini, aws_environment, sample_sqs_message):
        """Low content_score + no geo/media should produce trust_score < 30 → SPAM."""
        # content_score=0 + TWITTER(8) + history(10) + no_media(0) + no_geo(0) = 18 < 30
        mock_gemini.analyze_report.return_value = {
            "content_score": 0,
            "content_score_reasoning": "No location, vague, repetitive",
            "suggested_category": "OTHER",
            "keywords": [],
            "spam_signals": ["no_location", "vague"],
            "is_spam_likely": True,
            "ai_analysis_failed": False,
            "vision_used": False,
        }

        # Use a minimal body without geo or media to keep score below threshold
        spam_body = dict(sample_sqs_message)
        spam_body["media_urls"] = []
        spam_body["geo_location"] = None

        sqs_event = {
            "Records": [
                {
                    "messageId": "msg-spam",
                    "body": json.dumps(spam_body),
                }
            ]
        }

        with patch("src.handlers.ingestion_worker.boto3") as mock_boto3, \
             patch("src.services.event_publisher.boto3") as mock_eb_boto3:
            mock_boto3.client.return_value = aws_environment["dynamodb"]
            mock_eb_client = MagicMock()
            mock_eb_client.put_events.return_value = {"FailedEntryCount": 0, "Entries": [{}]}
            mock_eb_boto3.client.return_value = mock_eb_client

            from src.handlers.ingestion_worker import handler
            result = handler(sqs_event, None)

        assert result["batchItemFailures"] == []

        resp = aws_environment["dynamodb"].get_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": spam_body["report_id"]}},
        )
        assert resp["Item"]["validation_status"]["S"] == "SPAM"
