"""
core/exceptions.py
~~~~~~~~~~~~~~~~~~
Custom exception classes used throughout the app.

The global exception handlers in main.py convert these into the standard
{ "data": null, "error": {...} } API envelope automatically.
"""


class PatientNotFoundError(Exception):
    """Raised when a patient_id doesn't exist or has been soft-deleted."""

    def __init__(self, patient_id) -> None:
        self.patient_id = patient_id
        super().__init__(f"Patient '{patient_id}' not found or has been deleted.")


class PatientServiceError(Exception):
    """Wraps unexpected Supabase / database-level errors."""
    pass
