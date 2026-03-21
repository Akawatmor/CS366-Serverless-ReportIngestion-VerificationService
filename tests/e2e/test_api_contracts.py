"""
E2E tests for API contract validation.

Ensures every endpoint returns the expected response shape,
status codes, headers, and error formats as defined in the Service Proposal.

Requires API_URL env var.
"""
import os
import pytest

API_URL = os.environ.get("API_URL", "")
pytestmark = pytest.mark.skipif(not API_URL, reason="API_URL not set — skipping E2E tests")

try:
    import httpx
except ImportError:
    pytest.skip("httpx not installed", allow_module_level=True)


@pytest.fixture(scope="module")
def api_client():
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("API_KEY", "")
    if api_key:
        headers["X-Api-Key"] = api_key
    return httpx.Client(base_url=API_URL, headers=headers, timeout=30)


class TestCORSHeaders:
    """Verify CORS headers are present on all endpoints."""

    @pytest.mark.parametrize("path", [
        "/v1/reports",
        "/v1/health",
        "/v1/reports/stats",
    ])
    def test_options_returns_cors(self, api_client, path):
        """OPTIONS should return CORS headers."""
        resp = api_client.options(path)
        # API Gateway CORS module returns 200
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers or \
               "Access-Control-Allow-Origin" in resp.headers

    def test_get_response_has_cors(self, api_client):
        """GET responses should include CORS header."""
        resp = api_client.get("/v1/health")
        headers_lower = {k.lower(): v for k, v in resp.headers.items()}
        assert "access-control-allow-origin" in headers_lower


class TestIngestContract:
    """POST /v1/reports — Async ingestion (fire-and-forget)."""

    def test_202_accepted_schema(self, api_client):
        """Successful ingestion returns 202 with report_id, status, message."""
        payload = {
            "reporter_source": "LINE",
            "reporter_id": "e2e_contract_001",
            "raw_content": "E2E contract test — flooding in area",
        }
        resp = api_client.post("/v1/reports", json=payload)
        assert resp.status_code == 202

        body = resp.json()
        assert "report_id" in body
        assert body["status"] == "QUEUED"
        assert "message" in body

    def test_400_missing_fields(self, api_client):
        """Missing required fields returns 400 with error details."""
        resp = api_client.post("/v1/reports", json={})
        assert resp.status_code == 400

        body = resp.json()
        assert "error" in body or "errors" in body

    def test_400_invalid_source(self, api_client):
        """Invalid reporter_source returns 400."""
        payload = {
            "reporter_source": "UNKNOWN_PLATFORM",
            "reporter_id": "x",
            "raw_content": "test",
        }
        resp = api_client.post("/v1/reports", json=payload)
        assert resp.status_code == 400

    def test_400_geo_out_of_range(self, api_client):
        """geo_location with lat > 90 returns 400."""
        payload = {
            "reporter_source": "TWITTER",
            "reporter_id": "geo_test",
            "raw_content": "test",
            "geo_location": {"lat": 999, "lon": 100},
        }
        resp = api_client.post("/v1/reports", json=payload)
        assert resp.status_code == 400


class TestListContract:
    """GET /v1/reports — List reports with pagination."""

    def test_list_returns_array(self, api_client):
        """List response should contain data array and total_count."""
        resp = api_client.get("/v1/reports")
        assert resp.status_code == 200

        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)
        assert "total_count" in body

    def test_list_with_status_filter(self, api_client):
        """Filter by status should work."""
        resp = api_client.get("/v1/reports", params={"status": "PENDING_REVIEW"})
        assert resp.status_code == 200

        body = resp.json()
        assert "data" in body

    def test_list_invalid_status(self, api_client):
        """Invalid status filter returns 400."""
        resp = api_client.get("/v1/reports", params={"status": "INVALID_STATUS"})
        assert resp.status_code == 400


class TestDetailContract:
    """GET /v1/reports/{id} — Report detail."""

    def test_not_found(self, api_client):
        """Non-existent report returns 404."""
        resp = api_client.get("/v1/reports/r-nonexistent-9999")
        assert resp.status_code == 404

        body = resp.json()
        assert "error" in body


class TestVerifyContract:
    """PATCH /v1/reports/{id} — Verify/reject a report."""

    def test_400_missing_action(self, api_client):
        """Missing validation_status field returns 400."""
        resp = api_client.patch("/v1/reports/r-any-id", json={"reviewer_id": "x"})
        assert resp.status_code in [400, 404]

    def test_400_invalid_action(self, api_client):
        """Invalid validation_status returns 400."""
        payload = {
            "validation_status": "EXPLODE",
            "reviewer_id": "x",
        }
        resp = api_client.patch("/v1/reports/r-any", json=payload)
        assert resp.status_code in [400, 404]


class TestStatsContract:
    """GET /v1/reports/stats — Aggregated statistics."""

    def test_stats_returns_object(self, api_client):
        """Stats endpoint should return timestamp and summary."""
        resp = api_client.get("/v1/reports/stats")
        assert resp.status_code == 200

        body = resp.json()
        assert "timestamp" in body
        assert "summary" in body
        summary = body["summary"]
        assert "total_received_today" in summary
        assert "pending_review" in summary
        assert "verified_incidents" in summary
        assert "spam_rejected" in summary


class TestHealthContract:
    """GET /v1/health — System health."""

    def test_health_response_shape(self, api_client):
        """Health response must have status and components."""
        resp = api_client.get("/v1/health")
        assert resp.status_code in [200, 503]

        body = resp.json()
        assert "status" in body
        assert body["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in body
        assert isinstance(body["components"], dict)

    def test_health_components_shape(self, api_client):
        """Each component should have status and optional latency_ms."""
        resp = api_client.get("/v1/health")
        body = resp.json()

        for comp_name, comp_data in body.get("components", {}).items():
            assert "status" in comp_data
            assert comp_data["status"] in ["healthy", "degraded", "unhealthy"]
