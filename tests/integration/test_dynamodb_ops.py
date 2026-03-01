"""
Integration tests for DynamoDB operations using moto mock.
Tests the full flow from Report model → DynamoDB → Report model.
"""
import json
import pytest
import boto3
from moto import mock_aws

from src.config import config
from src.models.report import Report, GeoLocation, AuditLog
from src.services.audit_service import AuditService


@pytest.fixture
def dynamodb_tables():
    """Create mocked DynamoDB tables for testing."""
    with mock_aws():
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")

        # Reports table
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

        # Audit logs table
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

        # Stats table
        dynamodb.create_table(
            TableName=config.STATS_TABLE,
            KeySchema=[{"AttributeName": "stat_key", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "stat_key", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield dynamodb


class TestReportCRUD:
    """Test Report read/write operations against mocked DynamoDB."""

    def test_put_and_get_report(self, dynamodb_tables):
        """Write a report and read it back."""
        db = dynamodb_tables

        report = Report(
            report_id="r-test123",
            source_platform="TWITTER",
            reporter_id="@somchai",
            raw_content="ไฟไหม้ร้านทอง เยาวราช!",
            media_urls=["https://img.host/fire.jpg"],
            geo_location=GeoLocation(lat=13.7411, lon=100.5104),
            trust_score=85,
            validation_status="PENDING_REVIEW",
            suggested_category="FIRE",
            ai_analysis_tags=["FIRE", "URGENT"],
        )

        # Write
        db.put_item(TableName=config.REPORTS_TABLE, Item=report.to_dynamodb_item())

        # Read
        resp = db.get_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": "r-test123"}},
        )
        loaded = Report.from_dynamodb_item(resp["Item"])

        assert loaded.report_id == "r-test123"
        assert loaded.source_platform == "TWITTER"
        assert loaded.raw_content == "ไฟไหม้ร้านทอง เยาวราช!"
        assert loaded.trust_score == 85
        assert loaded.validation_status == "PENDING_REVIEW"
        assert loaded.geo_location.lat == 13.7411
        assert loaded.geo_location.lon == 100.5104
        assert "FIRE" in loaded.ai_analysis_tags

    def test_query_by_status(self, dynamodb_tables):
        """Query reports by validation_status via GSI."""
        db = dynamodb_tables

        for i in range(5):
            status = "PENDING_REVIEW" if i < 3 else "SPAM"
            report = Report(
                report_id=f"r-test{i}",
                source_platform="TWITTER",
                reporter_id=f"@user{i}",
                raw_content=f"Report {i}",
                trust_score=50 + i * 10,
                validation_status=status,
            )
            db.put_item(TableName=config.REPORTS_TABLE, Item=report.to_dynamodb_item())

        # Query pending
        resp = db.query(
            TableName=config.REPORTS_TABLE,
            IndexName="gsi_status_ingested",
            KeyConditionExpression="validation_status = :s",
            ExpressionAttributeValues={":s": {"S": "PENDING_REVIEW"}},
        )
        assert resp["Count"] == 3

        # Query spam
        resp = db.query(
            TableName=config.REPORTS_TABLE,
            IndexName="gsi_status_ingested",
            KeyConditionExpression="validation_status = :s",
            ExpressionAttributeValues={":s": {"S": "SPAM"}},
        )
        assert resp["Count"] == 2

    def test_update_status_with_condition(self, dynamodb_tables):
        """Test optimistic locking with ConditionExpression."""
        db = dynamodb_tables

        report = Report(
            report_id="r-lock-test",
            source_platform="TWITTER",
            reporter_id="@test",
            raw_content="Test",
            validation_status="PENDING_REVIEW",
        )
        db.put_item(TableName=config.REPORTS_TABLE, Item=report.to_dynamodb_item())

        # Update should succeed
        db.update_item(
            TableName=config.REPORTS_TABLE,
            Key={"report_id": {"S": "r-lock-test"}},
            UpdateExpression="SET validation_status = :new",
            ConditionExpression="validation_status = :expected",
            ExpressionAttributeValues={
                ":new": {"S": "VERIFIED"},
                ":expected": {"S": "PENDING_REVIEW"},
            },
        )

        # Second update should fail (already VERIFIED, not PENDING_REVIEW)
        with pytest.raises(db.exceptions.ConditionalCheckFailedException):
            db.update_item(
                TableName=config.REPORTS_TABLE,
                Key={"report_id": {"S": "r-lock-test"}},
                UpdateExpression="SET validation_status = :new",
                ConditionExpression="validation_status = :expected",
                ExpressionAttributeValues={
                    ":new": {"S": "SPAM"},
                    ":expected": {"S": "PENDING_REVIEW"},
                },
            )

    def test_idempotency_check(self, dynamodb_tables):
        """Test source_external_id GSI for duplicate detection."""
        db = dynamodb_tables

        report = Report(
            report_id="r-first",
            source_platform="TWITTER",
            reporter_id="@test",
            raw_content="Fire!",
            source_external_id="tweet_99999",
            validation_status="PENDING_REVIEW",
        )
        db.put_item(TableName=config.REPORTS_TABLE, Item=report.to_dynamodb_item())

        # Query by source_external_id
        resp = db.query(
            TableName=config.REPORTS_TABLE,
            IndexName="gsi_source_external_id",
            KeyConditionExpression="source_external_id = :sid",
            ExpressionAttributeValues={":sid": {"S": "tweet_99999"}},
            Limit=1,
        )
        assert resp["Count"] == 1
        assert resp["Items"][0]["report_id"]["S"] == "r-first"


class TestAuditLogCRUD:
    """Test audit log operations."""

    def test_write_and_query_audit_log(self, dynamodb_tables):
        """Write audit log and query by report_id."""
        db = dynamodb_tables
        audit_svc = AuditService(dynamodb_client=db)

        log_id = audit_svc.log_status_change(
            report_id="r-test123",
            actor_id="officer_007",
            old_status="PENDING_REVIEW",
            new_status="VERIFIED",
            notes="Confirmed via CCTV",
        )

        assert log_id.startswith("log-")

        # Query logs for this report
        resp = db.query(
            TableName=config.AUDIT_TABLE,
            IndexName="gsi_report_timestamp",
            KeyConditionExpression="report_ref_id = :rid",
            ExpressionAttributeValues={":rid": {"S": "r-test123"}},
        )
        assert resp["Count"] == 1
        item = resp["Items"][0]
        assert item["actor_id"]["S"] == "officer_007"
        assert item["action_type"]["S"] == "STATUS_CHANGE"


class TestStatsCounter:
    """Test atomic stats counter operations."""

    def test_increment_counter(self, dynamodb_tables):
        """Atomic ADD should increment counter."""
        db = dynamodb_tables

        # Increment 3 times
        for _ in range(3):
            db.update_item(
                TableName=config.STATS_TABLE,
                Key={"stat_key": {"S": "2026-03-01#total_received"}},
                UpdateExpression="ADD stat_value :inc",
                ExpressionAttributeValues={":inc": {"N": "1"}},
            )

        resp = db.get_item(
            TableName=config.STATS_TABLE,
            Key={"stat_key": {"S": "2026-03-01#total_received"}},
        )
        assert int(resp["Item"]["stat_value"]["N"]) == 3
