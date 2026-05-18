"""
Integration tests for EventBridge publishing using moto mock.
"""
import json
import pytest
import boto3
from moto import mock_aws

from src.config import config
from src.services.event_publisher import EventPublisher


@pytest.fixture
def eventbridge_env():
    """Set up mocked EventBridge environment."""
    with mock_aws():
        region = "us-east-1"
        client = boto3.client("events", region_name=region)

        # Create custom event bus
        client.create_event_bus(Name=config.EVENT_BUS_NAME)

        yield client


class TestEventPublisher:
    """Test EventBridge event publishing."""

    def test_publish_report_verified(self, eventbridge_env):
        """Should publish ReportVerifiedEvent without errors."""
        publisher = EventPublisher(eventbridge_client=eventbridge_env)

        event_id = publisher.publish_report_verified(
            report_id="r-test123",
            suggested_incident_data={
                "type": "FIRE",
                "description": "Fire at Central World",
                "severity_level": 3,
                "location": {"lat": "13.746", "lon": "100.539"},
                "reporter_count": 5,
                "media_evidence": ["https://img.host/fire.jpg"],
            },
            verified_by="officer_007",
            verification_notes="Confirmed via CCTV",
            action="MERGED_EXISTING_INCIDENT",
            target_incident_id="019C774D-1AC5-75BB-AE95-5CD4AEB8925B",
        )

        assert event_id.startswith("evt-")

    def test_publish_status_changed(self, eventbridge_env):
        """Should publish ReportStatusChangedEvent without errors."""
        publisher = EventPublisher(eventbridge_client=eventbridge_env)

        event_id = publisher.publish_status_changed(
            report_id="r-test456",
            old_status="PENDING_REVIEW",
            new_status="SPAM",
            changed_by="SYSTEM_AI",
            reason="Auto-rejected (Trust Score < 10%)",
        )

        assert event_id.startswith("evt-")

    def test_health_check_healthy(self, eventbridge_env):
        """Health check should report healthy when bus exists."""
        publisher = EventPublisher(eventbridge_client=eventbridge_env)
        result = publisher.health_check()
        assert result["status"] == "healthy"

    def test_health_check_unhealthy(self):
        """Health check should report unhealthy with invalid bus."""
        with mock_aws():
            client = boto3.client("events", region_name="us-east-1")
            publisher = EventPublisher(eventbridge_client=client)
            publisher.bus_name = "nonexistent-bus"
            result = publisher.health_check()
            assert result["status"] == "unhealthy"
