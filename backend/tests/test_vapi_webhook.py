"""
tests/test_vapi_webhook.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Pytest + httpx tests for POST /webhooks/vapi.

Phase 0: test stubs with docstrings only.
Phase 3 / 5 will implement assertions.
"""

import pytest


class TestWebhookAuth:
    def test_missing_secret_header_returns_401(self):
        """POST /webhooks/vapi without X-Vapi-Secret → 401 Unauthorized."""
        pytest.skip("Implement in Phase 3/5")

    def test_wrong_secret_returns_401(self):
        """POST /webhooks/vapi with an incorrect secret → 401 Unauthorized."""
        pytest.skip("Implement in Phase 3/5")


class TestUpdatePatientToolCall:
    def test_valid_update_patient_tool_call(self):
        """Valid update_patient tool-calls payload → 200 + Vapi results envelope."""
        pytest.skip("Implement in Phase 3/5")


class TestEndOfCallReport:
    def test_end_of_call_report_returns_200(self):
        """end-of-call-report payload → 200 and transcript logged to stdout."""
        pytest.skip("Implement in Phase 3/5")
