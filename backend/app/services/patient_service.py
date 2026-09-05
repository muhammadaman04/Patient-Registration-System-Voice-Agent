"""
services/patient_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Business logic shared by the REST routes AND the Vapi webhook handler.

All Supabase queries live here. Neither the route layer nor the webhook
layer touches the database directly.

Error strategy:
  - PatientNotFoundError  →  route layer turns it into 404
  - PatientServiceError   →  route layer turns it into 500
  - Pydantic errors       →  FastAPI's RequestValidationError handler → 422
"""

from datetime import datetime, timezone
from uuid import UUID

from postgrest.exceptions import APIError

from app.core.exceptions import PatientNotFoundError, PatientServiceError
from app.db.supabase_client import get_supabase
from app.schemas.patient import PatientCreate, PatientUpdate

TABLE = "patients"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _row_or_404(data: list[dict], patient_id) -> dict:
    """Return the first row or raise PatientNotFoundError."""
    if not data:
        raise PatientNotFoundError(patient_id)
    return data[0]


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------


def list_patients(
    *,
    last_name: str | None = None,
    date_of_birth: str | None = None,
    phone_number: str | None = None,
) -> list[dict]:
    """
    Return active patients matching the supplied filters (all optional).
    Soft-deleted rows (deleted_at IS NOT NULL) are always excluded.

    last_name is a case-insensitive partial match.
    date_of_birth must be an ISO date string (YYYY-MM-DD).
    phone_number is an exact match on the 10-digit stored value.
    """
    db = get_supabase()
    query = db.table(TABLE).select("*").is_("deleted_at", "null")

    if last_name:
        query = query.ilike("last_name", f"%{last_name}%")
    if date_of_birth:
        query = query.eq("date_of_birth", date_of_birth)
    if phone_number:
        query = query.eq("phone_number", phone_number)

    try:
        resp = query.execute()
        return resp.data
    except Exception as exc:
        msg = getattr(exc, "message", str(exc))
        raise PatientServiceError(f"Database error while listing patients: {msg}") from exc


def get_patient(patient_id: UUID) -> dict:
    """
    Return a single active patient by UUID.
    Raises PatientNotFoundError if not found or soft-deleted.
    """
    db = get_supabase()
    try:
        resp = (
            db.table(TABLE)
            .select("*")
            .eq("patient_id", str(patient_id))
            .is_("deleted_at", "null")
            .execute()
        )
    except Exception as exc:
        msg = getattr(exc, "message", str(exc))
        raise PatientServiceError(f"Database error fetching patient: {msg}") from exc

    return _row_or_404(resp.data, patient_id)


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------


def create_patient(data: PatientCreate) -> dict:
    """
    Insert a new patient row.
    Returns the created record (Supabase returns the inserted row by default).
    Raises PatientServiceError if a DB constraint is violated.
    """
    db = get_supabase()

    # model_dump excludes unset optional fields so we don't send null for
    # columns that have DB defaults (e.g. preferred_language).
    payload = data.model_dump(exclude_none=True)

    # Supabase expects ISO strings for date columns
    if "date_of_birth" in payload:
        payload["date_of_birth"] = payload["date_of_birth"].isoformat()

    try:
        resp = db.table(TABLE).insert(payload).execute()
        return resp.data[0]
    except Exception as exc:
        msg = getattr(exc, "message", str(exc))
        raise PatientServiceError(
            f"Could not create patient record: {msg}"
        ) from exc


def update_patient(patient_id: UUID, data: PatientUpdate) -> dict:
    """
    Partially update an existing patient (only supplied fields are changed).
    Raises PatientNotFoundError if the patient doesn't exist or is soft-deleted.

    Called by both:
      PUT /patients/{id}   (REST route)
      POST /webhooks/vapi  (Vapi Function tool — update_patient)
    """
    db = get_supabase()

    # Confirm the patient exists first (raises PatientNotFoundError if not)
    get_patient(patient_id)

    # Only include fields that were actually sent in the request body
    payload = data.model_dump(exclude_unset=True)

    if not payload:
        # Nothing to change — return the current record unchanged
        return get_patient(patient_id)

    if "date_of_birth" in payload and payload["date_of_birth"] is not None:
        payload["date_of_birth"] = payload["date_of_birth"].isoformat()

    try:
        resp = (
            db.table(TABLE)
            .update(payload)
            .eq("patient_id", str(patient_id))
            .is_("deleted_at", "null")
            .execute()
        )
        return _row_or_404(resp.data, patient_id)
    except PatientNotFoundError:
        raise
    except Exception as exc:
        msg = getattr(exc, "message", str(exc))
        raise PatientServiceError(
            f"Could not update patient record: {msg}"
        ) from exc


def soft_delete_patient(patient_id: UUID) -> dict:
    """
    Soft-delete a patient by setting deleted_at = now().
    Never issues a hard DELETE.
    Raises PatientNotFoundError if the patient doesn't exist or is already deleted.
    """
    db = get_supabase()

    # Confirm the patient exists first
    get_patient(patient_id)

    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        resp = (
            db.table(TABLE)
            .update({"deleted_at": now_iso})
            .eq("patient_id", str(patient_id))
            .is_("deleted_at", "null")
            .execute()
        )
        return _row_or_404(resp.data, patient_id)
    except PatientNotFoundError:
        raise
    except Exception as exc:
        msg = getattr(exc, "message", str(exc))
        raise PatientServiceError(
            f"Could not delete patient record: {msg}"
        ) from exc
