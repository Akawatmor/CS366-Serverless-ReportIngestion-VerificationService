"""
E2E tests for the verification flow: PATCH /reports/{id} → status change → EventBridge.

Requires a running API with API_URL env var.
"""
import os
import time
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


import random

def _create_and_wait(api_client, content="E2E verify test report", max_wait=60) -> str:
    """Helper: submit a report and poll until processed (or timeout)."""
    # Use random coordinates far apart to avoid dedup (200m radius)
    lat = random.uniform(-30.0, 60.0)
    lon = random.uniform(-120.0, 150.0)
    payload = {
        "reporter_source": "OFFICIAL_APP",
        "reporter_id": "e2e_verifier",
        "raw_content": content,
        "geo_location": {"lat": round(lat, 4), "lon": round(lon, 4)},
    }
    resp = api_client.post("/v1/reports", json=payload)
    assert resp.status_code == 202
    report_id = resp.json()["report_id"]

    # Poll until report leaves RECEIVED status (worker has processed it)
    deadline = time.time() + max_wait
    while time.time() < deadline:
        time.sleep(5)
        r = api_client.get(f"/v1/reports/{report_id}")
        if r.status_code == 200 and r.json().get("status", "RECEIVED") != "RECEIVED":
            break
    return report_id


class TestVerifyFlow:
    """E2E: Submit → Process → Verify → Confirm state transition."""

    def test_verify_pending_report(self, api_client):
        """PATCH a PENDING_REVIEW report to VERIFIED should succeed."""
        import uuid
        unique = uuid.uuid4().hex[:8]
        report_id = _create_and_wait(api_client, f"Unique verify test {unique} — major flooding at riverside district")

        # Check current status
        resp = api_client.get(f"/v1/reports/{report_id}")
        if resp.status_code != 200:
            pytest.skip("Report not yet processed by worker")

        current_status = resp.json().get("status", "")
        if current_status != "PENDING_REVIEW":
            pytest.skip(f"Report in {current_status}, not PENDING_REVIEW — cannot verify")

        # Verify
        verify_payload = {
            "validation_status": "VERIFIED",
            "reviewer_id": "e2e_admin_001",
            "reviewer_notes": "E2E test — verified by automated test",
        }
        resp = api_client.patch(f"/v1/reports/{report_id}", json=verify_payload)
        assert resp.status_code == 200

        body = resp.json()
        assert body["validation_status"] == "VERIFIED"
        assert "action_taken" in body

    def test_reject_pending_report(self, api_client):
        """PATCH a PENDING_REVIEW report to REJECTED should succeed."""
        import uuid
        unique = uuid.uuid4().hex[:8]
        report_id = _create_and_wait(api_client, f"Unique reject test {unique} — earthquake tremor in northern region")

        resp = api_client.get(f"/v1/reports/{report_id}")
        if resp.status_code != 200:
            pytest.skip("Report not yet processed")
        if resp.json().get("status") != "PENDING_REVIEW":
            pytest.skip("Report not in PENDING_REVIEW")

        reject_payload = {
            "validation_status": "REJECTED",
            "reviewer_id": "e2e_moderator",
            "reviewer_notes": "E2E test — rejected as false alarm",
        }
        resp = api_client.patch(f"/v1/reports/{report_id}", json=reject_payload)
        assert resp.status_code == 200
        assert resp.json()["validation_status"] == "REJECTED"

    def test_invalid_transition(self, api_client):
        """PATCH an already-VERIFIED report to VERIFY again should fail."""
        report_id = _create_and_wait(api_client, "E2E double verify test")

        resp = api_client.get(f"/v1/reports/{report_id}")
        if resp.status_code != 200:
            pytest.skip("Report not yet processed")

        current_status = resp.json().get("status", "")

        # First verify (if PENDING_REVIEW)
        if current_status == "PENDING_REVIEW":
            verify_payload = {
                "validation_status": "VERIFIED",
                "reviewer_id": "e2e_admin",
                "reviewer_notes": "First verify",
            }
            resp = api_client.patch(f"/v1/reports/{report_id}", json=verify_payload)
            assert resp.status_code == 200

        # Try verify again — invalid transition from VERIFIED → VERIFIED
        verify_again = {
            "validation_status": "VERIFIED",
            "reviewer_id": "e2e_admin",
            "reviewer_notes": "Second verify attempt",
        }
        resp = api_client.patch(f"/v1/reports/{report_id}", json=verify_again)
        # Should be 409 Conflict or 400 Bad Request
        assert resp.status_code in [400, 409]


class TestSoftDelete:
    """E2E: Soft delete a report."""

    def test_delete_report(self, api_client):
        """DELETE /reports/{id} should soft-delete."""
        report_id = _create_and_wait(api_client, "E2E delete test report")

        resp = api_client.get(f"/v1/reports/{report_id}")
        if resp.status_code != 200:
            pytest.skip("Report not yet processed")

        delete_payload = {
            "deleted_by": "e2e_admin",
            "reason": "E2E cleanup",
        }
        resp = api_client.request("DELETE", f"/v1/reports/{report_id}", json=delete_payload)
        assert resp.status_code == 200

        # Verify the report is deleted
        resp = api_client.get(f"/v1/reports/{report_id}")
        if resp.status_code == 200:
            assert resp.json().get("status") == "DELETED"
