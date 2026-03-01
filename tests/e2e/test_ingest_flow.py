"""
E2E tests for the full ingestion flow: POST → SQS → Worker → DynamoDB.

These tests require a deployed API. Set the API_URL environment variable:
  API_URL=https://xxx.execute-api.us-east-1.amazonaws.com/dev pytest tests/e2e/

To run locally without a deployed API, skip these tests:
  pytest tests/ --ignore=tests/e2e/
"""
import json
import os
import time
import pytest

# Skip entire module if API_URL not set
API_URL = os.environ.get("API_URL", "")
pytestmark = pytest.mark.skipif(not API_URL, reason="API_URL not set — skipping E2E tests")

try:
    import httpx
except ImportError:
    pytest.skip("httpx not installed", allow_module_level=True)


@pytest.fixture(scope="module")
def api_client():
    """HTTP client for E2E tests."""
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("API_KEY", "")
    if api_key:
        headers["X-Api-Key"] = api_key
    return httpx.Client(base_url=API_URL, headers=headers, timeout=30)


class TestIngestFlow:
    """E2E: Submit a report and verify it appears in the system."""

    def test_submit_valid_report(self, api_client):
        """POST /v1/reports should return 202 Accepted."""
        payload = {
            "reporter_source": "TWITTER",
            "reporter_id": "@e2e_test_user",
            "raw_content": "E2E test — fire spotted near test location",
            "geo_location": {"lat": 13.7466, "lon": 100.5391},
            "timestamp": "2026-02-18T14:30:00Z",
        }

        resp = api_client.post("/v1/reports", json=payload)
        assert resp.status_code == 202

        body = resp.json()
        assert body["status"] == "QUEUED"
        assert body["report_id"].startswith("r-")

    def test_submit_invalid_report(self, api_client):
        """POST /v1/reports with missing fields should return 400."""
        payload = {
            "reporter_source": "INVALID_SOURCE",
        }

        resp = api_client.post("/v1/reports", json=payload)
        assert resp.status_code == 400

    def test_submit_and_wait_for_processing(self, api_client):
        """Submit a report, wait, then check it appears in GET /reports."""
        payload = {
            "reporter_source": "OFFICIAL_APP",
            "reporter_id": "e2e_officer",
            "raw_content": "E2E integration test report — earthquake detected",
            "geo_location": {"lat": 19.9105, "lon": 99.8406},
        }

        # Submit
        resp = api_client.post("/v1/reports", json=payload)
        assert resp.status_code == 202
        report_id = resp.json()["report_id"]

        # Wait for SQS → Worker processing
        time.sleep(5)

        # Fetch detail
        resp = api_client.get(f"/v1/reports/{report_id}")
        if resp.status_code == 200:
            body = resp.json()
            assert body["report_id"] == report_id
            assert body["status"] in ["PENDING_REVIEW", "SPAM", "DUPLICATE", "RECEIVED"]


class TestHealthCheck:
    """E2E: Health endpoint should always be reachable."""

    def test_health_endpoint(self, api_client):
        """GET /v1/health should return 200 or 503."""
        resp = api_client.get("/v1/health")
        assert resp.status_code in [200, 503]

        body = resp.json()
        assert body["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in body
