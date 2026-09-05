"""
api/routes/patients.py
~~~~~~~~~~~~~~~~~~~~~~
REST CRUD endpoints for the /patients resource.

All routes wrap their response in ApiResponse[T] so the caller always sees:
  { "data": {...}, "error": null }   on success
  { "data": null, "error": {...} }   on failure  (handled globally in main.py)

Error flow:
  PatientNotFoundError  → global handler → 404
  PatientServiceError   → global handler → 500
  RequestValidationError (Pydantic) → global handler → 422
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query

from app.schemas.patient import ApiResponse, PatientCreate, PatientOut, PatientUpdate
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["patients"])


# ---------------------------------------------------------------------------
# List patients
# ---------------------------------------------------------------------------


@router.get("", response_model=ApiResponse[list[PatientOut]])
async def list_patients(
    last_name: str | None = Query(None, description="Case-insensitive partial match on last name"),
    date_of_birth: date | None = Query(None, description="Exact match — format YYYY-MM-DD"),
    phone_number: str | None = Query(None, description="Exact 10-digit match"),
):
    """
    List active patients, optionally filtered by last_name, date_of_birth,
    or phone_number. Soft-deleted records are never returned.

    Also called directly by Vapi's **lookup_patient_by_phone** API Request tool.
    """
    dob_str = date_of_birth.isoformat() if date_of_birth else None
    rows = patient_service.list_patients(
        last_name=last_name,
        date_of_birth=dob_str,
        phone_number=phone_number,
    )
    return ApiResponse(data=[PatientOut.model_validate(r) for r in rows])


# ---------------------------------------------------------------------------
# Get one patient
# ---------------------------------------------------------------------------


@router.get("/{patient_id}", response_model=ApiResponse[PatientOut])
async def get_patient(patient_id: UUID):
    """
    Return a single active patient by UUID.
    Returns 404 if the patient does not exist or has been soft-deleted.
    """
    row = patient_service.get_patient(patient_id)
    return ApiResponse(data=PatientOut.model_validate(row))


# ---------------------------------------------------------------------------
# Create patient
# ---------------------------------------------------------------------------


@router.post("", response_model=ApiResponse[PatientOut], status_code=201)
async def create_patient(body: PatientCreate):
    """
    Register a new patient.

    Returns **201** + the created record on success.
    Returns **422** on validation failure — error messages are written in plain
    caller-readable language so the voice agent can relay them verbatim.

    Also called directly by Vapi's **create_patient** API Request tool.
    """
    row = patient_service.create_patient(body)
    return ApiResponse(data=PatientOut.model_validate(row))


# ---------------------------------------------------------------------------
# Update patient (partial)
# ---------------------------------------------------------------------------


@router.put("/{patient_id}", response_model=ApiResponse[PatientOut])
async def update_patient(patient_id: UUID, body: PatientUpdate):
    """
    Partially update a patient — only the fields present in the request body
    are written; omitted fields are left unchanged.

    Returns 404 if the patient does not exist or has been soft-deleted.

    **Note:** the voice agent's *update_patient* Vapi Function tool does NOT
    hit this endpoint. It posts to `/webhooks/vapi` which calls
    `patient_service.update_patient()` directly (because Vapi's API Request
    tool only supports GET/POST, not PUT). Both paths share the same service
    function and validation logic.
    """
    row = patient_service.update_patient(patient_id, body)
    return ApiResponse(data=PatientOut.model_validate(row))


# ---------------------------------------------------------------------------
# Soft-delete patient
# ---------------------------------------------------------------------------


@router.delete("/{patient_id}", response_model=ApiResponse[PatientOut])
async def delete_patient(patient_id: UUID):
    """
    Soft-delete a patient by setting `deleted_at = now()`.
    The row is never physically removed from the database.

    Returns 404 if the patient does not exist or is already deleted.
    """
    row = patient_service.soft_delete_patient(patient_id)
    return ApiResponse(data=PatientOut.model_validate(row))
