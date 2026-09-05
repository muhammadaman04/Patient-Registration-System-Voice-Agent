"""
models/patient.py
~~~~~~~~~~~~~~~~~
SQLAlchemy-style or plain dataclass representation of the `patients` table.

Phase 0: skeleton only — no logic yet.
Phase 2 will flesh out the actual Supabase query wrappers.

Note: Because we're using the Supabase Python SDK (not SQLAlchemy), this
module primarily documents the table schema as Python types. The canonical
schema lives in supabase/migrations/0001_init.sql.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID


@dataclass
class Patient:
    """
    In-memory representation of a patients row.
    Mirrors the columns in 0001_init.sql exactly.
    """

    patient_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    address_line_1: str
    city: str
    state: str
    zip_code: str
    created_at: datetime
    updated_at: datetime

    # Optional fields
    email: str | None = None
    address_line_2: str | None = None
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str = "English"
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    deleted_at: datetime | None = None
