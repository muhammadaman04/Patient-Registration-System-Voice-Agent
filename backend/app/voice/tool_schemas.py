"""
voice/tool_schemas.py
~~~~~~~~~~~~~~~~~~~~~
Vapi tool definitions as Python dicts — fully fleshed-out parameter schemas.

Sent to the Vapi API by scripts/setup_vapi_assistant.py when creating or
updating the assistant. The structure mirrors the Vapi REST API schema exactly
so they can be serialised directly with json.dumps().

Tool types used:
  - "apiRequest" : Vapi builds and sends the HTTP call itself (GET/POST/PUT/
                   PATCH/DELETE). Fields (url, method, headers, timeoutSeconds,
                   backoffPlan) go FLAT on the tool object. The model-facing
                   argument schema goes under "body" (a JSON Schema) — NOT
                   "parameters". "parameters" on this tool type means a
                   separate list of server-trusted STATIC key/value pairs
                   merged in without the LLM seeing them; we don't use that
                   here.
  - "function"   : Vapi posts the call to our /webhooks/vapi endpoint.
                   name/description/parameters must be nested inside a
                   "function" sub-object (mirrors OpenAI's function-calling
                   shape). "server" stays flat on the tool.
                   Needed for update_patient because PUT is not supported by
                   the apiRequest type.
  - "endCall"    : Vapi built-in — terminates the active call. Schema is
                   auto-derived by Vapi; you don't define parameters for it.
"""

from app.core.config import settings

_BASE = settings.public_api_base_url.rstrip("/")

# ---------------------------------------------------------------------------
# Tool 1 — lookup_patient_by_phone  (apiRequest / GET)
# ---------------------------------------------------------------------------

LOOKUP_PATIENT_BY_PHONE: dict = {
    "type": "apiRequest",
    "name": "lookup_patient_by_phone",
    "description": (
        "Look up an existing patient by their 10-digit US phone number. "
        "Call this as soon as the caller's phone number has been collected, "
        "before collecting any more information, to detect returning patients."
    ),
    "method": "GET",
    "url": _BASE + "/patients?phone_number={{phone_number}}",
    "timeoutSeconds": 15,
    "body": {
        "type": "object",
        "properties": {
            "phone_number": {
                "type": "string",
                "description": (
                    "10-digit US phone number, digits only — no dashes, spaces, "
                    "or country code. Example: 5551234567"
                ),
            }
        },
        "required": ["phone_number"],
    },
}

# ---------------------------------------------------------------------------
# Tool 2 — create_patient  (apiRequest / POST)
# ---------------------------------------------------------------------------

CREATE_PATIENT: dict = {
    "type": "apiRequest",
    "name": "create_patient",
    "description": (
        "Create a new patient record in the system. "
        "Only call this AFTER the caller has explicitly confirmed every "
        "collected field is correct. Never call without that confirmation."
    ),
    "method": "POST",
    "url": _BASE + "/patients",
    # No explicit "headers" — Vapi sends Content-Type: application/json
    # automatically for a JSON body, and the exact accepted shape for this
    # field wasn't worth further guessing against a tight credit budget.
    "timeoutSeconds": 20,
    # No "backoffPlan" — optional, exact valid shape wasn't worth guessing
    # further against a tight credit budget. A failed create_patient call
    # will just not auto-retry; the assistant still needs to handle and
    # relay that failure gracefully per the assessment's edge-case
    # requirements, which doesn't depend on this field.
    "body": {
        "type": "object",
        "properties": {
            # ── Required ──────────────────────────────────────────────────
            "first_name": {
                "type": "string",
                "description": "Patient's legal first name, 1–50 characters.",
            },
            "last_name": {
                "type": "string",
                "description": "Patient's legal last name, 1–50 characters.",
            },
            "date_of_birth": {
                "type": "string",
                "description": (
                    "Date of birth in ISO format YYYY-MM-DD. "
                    "Must not be in the future. Example: 1985-06-15"
                ),
            },
            "sex": {
                "type": "string",
                "enum": ["Male", "Female", "Other", "Decline to Answer"],
                "description": "Patient's sex — must be one of the four listed values.",
            },
            "phone_number": {
                "type": "string",
                "description": "10-digit US phone number, digits only. Example: 5551234567",
            },
            "address_line_1": {
                "type": "string",
                "description": "Street address, line 1.",
            },
            "city": {
                "type": "string",
                "description": "City name, 1–100 characters.",
            },
            "state": {
                "type": "string",
                "description": (
                    "2-letter USPS state abbreviation, uppercase. "
                    "Example: CA, TX, NY"
                ),
            },
            "zip_code": {
                "type": "string",
                "description": (
                    "US ZIP code — 5 digits, or 5 digits hyphen 4 digits. "
                    "Example: 90210 or 90210-1234"
                ),
            },
            # ── Optional ──────────────────────────────────────────────────
            "email": {
                "type": "string",
                "description": "Patient's email address (optional).",
            },
            "address_line_2": {
                "type": "string",
                "description": "Apartment, suite, unit, etc. (optional).",
            },
            "insurance_provider": {
                "type": "string",
                "description": "Name of the insurance provider (optional).",
            },
            "insurance_member_id": {
                "type": "string",
                "description": "Insurance member ID number (optional).",
            },
            "preferred_language": {
                "type": "string",
                "description": "Preferred language. Defaults to English if not provided.",
            },
            "emergency_contact_name": {
                "type": "string",
                "description": "Full name of the emergency contact (optional).",
            },
            "emergency_contact_phone": {
                "type": "string",
                "description": (
                    "10-digit US phone number for emergency contact, digits only (optional)."
                ),
            },
        },
        "required": [
            "first_name",
            "last_name",
            "date_of_birth",
            "sex",
            "phone_number",
            "address_line_1",
            "city",
            "state",
            "zip_code",
        ],
    },
}

# ---------------------------------------------------------------------------
# Tool 3 — update_patient  (function → webhook → PUT-equivalent)
# ---------------------------------------------------------------------------
# Vapi's apiRequest tool type does not support PUT, so we use a Function tool
# that posts to /webhooks/vapi. Our webhook handler calls
# patient_service.update_patient() which is the same code path as PUT /patients.
#
# Function tools nest name/description/parameters inside "function" —
# this mirrors OpenAI's function-calling schema shape and is what the
# API actually validates against.

UPDATE_PATIENT: dict = {
    "type": "function",
    "function": {
        "name": "update_patient",
        "description": (
            "Update an existing patient's record. Use this when the caller "
            "confirms they are a returning patient and want to update their information, "
            "or to correct a specific field after read-back. "
            "Only call after the caller confirms the changes are correct."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                # patient_id is required — obtained from lookup_patient_by_phone result
                "patient_id": {
                    "type": "string",
                    "description": (
                        "UUID of the existing patient record to update. "
                        "Obtained from the result of lookup_patient_by_phone."
                    ),
                },
                # All other fields are optional (partial update)
                "first_name": {"type": "string", "description": "Updated first name."},
                "last_name": {"type": "string", "description": "Updated last name."},
                "date_of_birth": {
                    "type": "string",
                    "description": "Updated date of birth, ISO format YYYY-MM-DD.",
                },
                "sex": {
                    "type": "string",
                    "enum": ["Male", "Female", "Other", "Decline to Answer"],
                    "description": "Updated sex value.",
                },
                "phone_number": {
                    "type": "string",
                    "description": "Updated 10-digit phone number, digits only.",
                },
                "email": {"type": "string", "description": "Updated email address."},
                "address_line_1": {"type": "string", "description": "Updated street address line 1."},
                "address_line_2": {"type": "string", "description": "Updated street address line 2."},
                "city": {"type": "string", "description": "Updated city."},
                "state": {"type": "string", "description": "Updated 2-letter state code."},
                "zip_code": {"type": "string", "description": "Updated ZIP code."},
                "insurance_provider": {"type": "string", "description": "Updated insurance provider."},
                "insurance_member_id": {"type": "string", "description": "Updated insurance member ID."},
                "preferred_language": {"type": "string", "description": "Updated preferred language."},
                "emergency_contact_name": {"type": "string", "description": "Updated emergency contact name."},
                "emergency_contact_phone": {"type": "string", "description": "Updated emergency contact phone."},
            },
            "required": ["patient_id"],
        },
    },
    "server": {"url": _BASE + "/webhooks/vapi"},
}

# ---------------------------------------------------------------------------
# Tool 4 — endCall  (Vapi built-in)
# ---------------------------------------------------------------------------
# Built-in tool types have a fully Vapi-controlled/auto-derived schema —
# no "name", "description", "parameters", or "function" allowed. Any of
# those trigger "property X should not exist". Just the type.

END_CALL: dict = {
    "type": "endCall",
}

# ---------------------------------------------------------------------------
# Full list — passed to setup_vapi_assistant.py
# ---------------------------------------------------------------------------

ALL_TOOLS: list[dict] = [
    LOOKUP_PATIENT_BY_PHONE,
    CREATE_PATIENT,
    UPDATE_PATIENT,
    END_CALL,
]