"""
Integration tests for SQS → Ingestion Worker flow using moto mock.
"""
import json
import pytest
import boto3
from unittest.mock import patch, MagicMock
from moto import mock_aws

from src.config import config


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
        # Mock Gemini response
        mock_gemini.analyze_report.return_value = {
            "trust_score": 85,
            "suggested_category": "FIRE",
            "keywords": ["fire", "smoke"],
            "reasoning": "Fire detected in content",
            "is_spam_likely": False,
            "ai_analysis_failed": False,
        }

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
        assert item["trust_score"]["N"] == "85"
        assert item["validation_status"]["S"] == "PENDING_REVIEW"

    @patch("src.handlers.ingestion_worker.gemini_service")
    def test_worker_auto_rejects_spam(self, mock_gemini, aws_environment, sample_sqs_message):
        """Low trust score should auto-mark as SPAM."""
        mock_gemini.analyze_report.return_value = {
            "trust_score": 10,
            "suggested_category": "OTHER",
            "keywords": [],
            "reasoning": "Spam detected",
            "is_spam_likely": True,
            "ai_analysis_failed": False,
        }

        sqs_event = {
            "Records": [
                {
                    "messageId": "msg-spam",
                    "body": json.dumps(sample_sqs_message),
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
            Key={"report_id": {"S": sample_sqs_message["report_id"]}},
        )
        assert resp["Item"]["validation_status"]["S"] == "SPAM"
