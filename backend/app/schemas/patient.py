"""
schemas/patient.py
~~~~~~~~~~~~~~~~~~
Pydantic request/response models for the /patients REST endpoints.

Validation rules are written in plain, caller-readable language because the
voice agent will relay error messages verbatim to a phone caller.
"""

import re
from datetime import date, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# All valid USPS 2-letter state/territory abbreviations
USPS_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "GU", "VI", "AS", "MP",
}

VALID_SEX_VALUES = {"Male", "Female", "Other", "Decline to Answer"}

# ---------------------------------------------------------------------------
# Generic API envelope  { "data": T, "error": null }  /  { "data": null, "error": {...} }
# ---------------------------------------------------------------------------

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str
    field: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    error: ApiError | None = None


# ---------------------------------------------------------------------------
# Shared validators (applied to both PatientCreate and PatientUpdate)
# ---------------------------------------------------------------------------


def _validate_phone(v: str | None) -> str | None:
    """Strip formatting, then require exactly 10 digits."""
    if v is None:
        return v
    digits = re.sub(r"\D", "", v)
    if len(digits) != 10:
        raise ValueError("phone number must be exactly 10 digits — please say just the ten numbers")
    return digits  # always stored as bare digits


def _validate_state(v: str | None) -> str | None:
    if v is None:
        return v
    upper = v.strip().upper()
    if upper not in USPS_STATES:
        raise ValueError(
            f"'{v}' is not a valid 2-letter US state abbreviation — "
            "please spell out just the two-letter code, like C-A for California"
        )
    return upper


def _validate_zip(v: str | None) -> str | None:
    if v is None:
        return v
    if not re.match(r"^\d{5}(-\d{4})?$", v):
        raise ValueError(
            "zip code must be 5 digits, or 5 digits followed by a dash and 4 more digits"
        )
    return v


def _validate_email(v: str | None) -> str | None:
    if v is None:
        return v
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v, re.IGNORECASE):
        raise ValueError("that doesn't look like a valid email address — can you repeat it?")
    return v.lower()


def _validate_dob(v: date | None) -> date | None:
    if v is None:
        return v
    if v > date.today():
        raise ValueError("date of birth cannot be in the future — can you check that date again?")
    return v


# ---------------------------------------------------------------------------
# PatientCreate
# ---------------------------------------------------------------------------


class PatientCreate(BaseModel):
    """Fields sent when registering a new patient via REST or Vapi tool call."""

    # Required
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    address_line_1: str
    city: str
    state: str
    zip_code: str

    # Optional
    email: str | None = None
    address_line_2: str | None = None
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str = "English"
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    # ----- validators -----

    @field_validator("first_name", "last_name")
    @classmethod
    def name_length(cls, v: str) -> str:
        v = v.strip()
        if not (1 <= len(v) <= 50):
            raise ValueError("name must be between 1 and 50 characters")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v: date) -> date:
        return _validate_dob(v)  # type: ignore[return-value]

    @field_validator("sex")
    @classmethod
    def sex_allowed(cls, v: str) -> str:
        if v not in VALID_SEX_VALUES:
            opts = ", ".join(sorted(VALID_SEX_VALUES))
            raise ValueError(f"sex must be one of: {opts}")
        return v

    @field_validator("phone_number")
    @classmethod
    def phone_digits(cls, v: str) -> str:
        result = _validate_phone(v)
        assert result is not None
        return result

    @field_validator("state")
    @classmethod
    def state_code(cls, v: str) -> str:
        result = _validate_state(v)
        assert result is not None
        return result

    @field_validator("zip_code")
    @classmethod
    def zip_format(cls, v: str) -> str:
        result = _validate_zip(v)
        assert result is not None
        return result

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str | None) -> str | None:
        return _validate_email(v)

    @field_validator("emergency_contact_phone")
    @classmethod
    def ec_phone_digits(cls, v: str | None) -> str | None:
        return _validate_phone(v)


# ---------------------------------------------------------------------------
# PatientUpdate  (all fields optional — PATCH semantics via PUT)
# ---------------------------------------------------------------------------


class PatientUpdate(BaseModel):
    """All fields optional. Only supplied fields are written to the database."""

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    sex: str | None = None
    phone_number: str | None = None
    email: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    # ----- validators (same rules, but only fire when the field is present) -----

    @field_validator("first_name", "last_name")
    @classmethod
    def name_length(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not (1 <= len(v) <= 50):
                raise ValueError("name must be between 1 and 50 characters")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v: date | None) -> date | None:
        return _validate_dob(v)

    @field_validator("sex")
    @classmethod
    def sex_allowed(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_SEX_VALUES:
            opts = ", ".join(sorted(VALID_SEX_VALUES))
            raise ValueError(f"sex must be one of: {opts}")
        return v

    @field_validator("phone_number")
    @classmethod
    def phone_digits(cls, v: str | None) -> str | None:
        return _validate_phone(v)

    @field_validator("state")
    @classmethod
    def state_code(cls, v: str | None) -> str | None:
        return _validate_state(v)

    @field_validator("zip_code")
    @classmethod
    def zip_format(cls, v: str | None) -> str | None:
        return _validate_zip(v)

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str | None) -> str | None:
        return _validate_email(v)

    @field_validator("emergency_contact_phone")
    @classmethod
    def ec_phone_digits(cls, v: str | None) -> str | None:
        return _validate_phone(v)


# ---------------------------------------------------------------------------
# PatientOut  (full record returned to callers)
# ---------------------------------------------------------------------------


class PatientOut(BaseModel):
    """Full patient record returned in API responses."""

    patient_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    email: str | None = None
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state: str
    zip_code: str
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}
