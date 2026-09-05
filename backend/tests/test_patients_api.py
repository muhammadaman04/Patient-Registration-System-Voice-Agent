"""
tests/test_patients_api.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Pytest + httpx tests for the /patients REST endpoints.

Phase 0: test stubs with docstrings only.
Phase 5 / 8 will implement the actual assertions against a test Supabase project.
"""

import pytest


# ---------------------------------------------------------------------------
# TODO (Phase 5/8): configure an async httpx.AsyncClient pointed at the app
# ---------------------------------------------------------------------------


class TestCreatePatient:
    def test_create_with_valid_data(self):
        """POST /patients with all required fields → 201 + patient record."""
        pytest.skip("Implement in Phase 2/5")

    def test_create_with_invalid_phone_number(self):
        """POST /patients with a non-10-digit phone → 422 + caller-readable error message."""
        pytest.skip("Implement in Phase 5")

    def test_create_with_future_date_of_birth(self):
        """POST /patients with a future DOB → 422 + caller-readable error message."""
        pytest.skip("Implement in Phase 5")


class TestGetPatient:
    def test_get_existing_patient(self):
        """GET /patients/{id} for a known record → 200 + full record."""
        pytest.skip("Implement in Phase 2/5")

    def test_get_missing_patient(self):
        """GET /patients/{id} for an unknown UUID → 404."""
        pytest.skip("Implement in Phase 5")


class TestListPatients:
    def test_list_filtered_by_last_name(self):
        """GET /patients?last_name=Smith → only matching rows."""
        pytest.skip("Implement in Phase 5")

    def test_list_filtered_by_phone(self):
        """GET /patients?phone_number=5550001234 → only matching rows."""
        pytest.skip("Implement in Phase 5")

    def test_soft_deleted_rows_excluded(self):
        """Soft-deleted patients never appear in GET /patients."""
        pytest.skip("Implement in Phase 5")


class TestUpdatePatient:
    def test_partial_update_via_put(self):
        """PUT /patients/{id} with one changed field → 200 + updated record."""
        pytest.skip("Implement in Phase 5")


class TestSoftDelete:
    def test_soft_delete_sets_deleted_at(self):
        """DELETE /patients/{id} → deleted_at is set; record gone from list."""
        pytest.skip("Implement in Phase 5")
