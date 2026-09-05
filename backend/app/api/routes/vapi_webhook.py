"""
api/routes/vapi_webhook.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
POST /webhooks/vapi

Handles inbound messages from Vapi's server:

  message.type == "tool-calls"
      → dispatches to the appropriate tool handler.
        Currently handles: update_patient (the only Function tool).
        lookup_patient_by_phone and create_patient are apiRequest tools so
        Vapi calls the REST endpoints directly — they never arrive here.

  message.type == "end-of-call-report"
      → logs call summary and transcript to stdout for debugging.

  anything else
      → acknowledged with 200 {} (Vapi sends several event types we ignore).

Security: every request must carry the X-Vapi-Secret header matching
VAPI_SERVER_SECRET from the environment. Requests missing or mismatching
this header are rejected with 401 before any processing.
"""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings
from app.core.exceptions import PatientNotFoundError, PatientServiceError
from app.schemas.patient import PatientUpdate
from app.services import patient_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------


def _verify_secret(x_vapi_secret: str | None) -> None:
    """Reject the request if the shared secret header is missing or wrong."""
    if not settings.vapi_server_secret or x_vapi_secret != settings.vapi_server_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Vapi-Secret header.",
        )


# ---------------------------------------------------------------------------
# Tool-call dispatcher
# ---------------------------------------------------------------------------


def _handle_update_patient(tool_call: dict) -> dict:
    """
    Process an update_patient Function tool call from Vapi.

    Returns a single Vapi result dict:
      { "toolCallId": "...", "result": "<string the LLM sees>" }
    """
    tool_call_id = tool_call.get("id", "unknown")

    # Arguments arrive as a JSON string or already-parsed dict
    raw_args = tool_call.get("function", {}).get("arguments", "{}")
    args: dict = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

    # Extract patient_id — required
    patient_id_str = args.pop("patient_id", None)
    if not patient_id_str:
        return {
            "toolCallId": tool_call_id,
            "result": "Error: patient_id is required to update a record.",
        }

    try:
        patient_id = UUID(patient_id_str)
    except ValueError:
        return {
            "toolCallId": tool_call_id,
            "result": f"Error: '{patient_id_str}' is not a valid patient ID.",
        }

    # Build a PatientUpdate from remaining args (all optional)
    try:
        update_data = PatientUpdate(**args)
    except Exception as exc:
        # Pydantic validation failure — relay the message so the agent can re-prompt
        return {
            "toolCallId": tool_call_id,
            "result": f"Validation error: {exc}",
        }

    # Call the shared service function
    try:
        record = patient_service.update_patient(patient_id, update_data)
        name = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip()
        return {
            "toolCallId": tool_call_id,
            "result": (
                f"Success: patient record for {name} has been updated. "
                f"patient_id={record['patient_id']}"
            ),
        }
    except PatientNotFoundError:
        return {
            "toolCallId": tool_call_id,
            "result": (
                "Error: patient record not found. "
                "It may have been deleted, or the ID is incorrect."
            ),
        }
    except PatientServiceError as exc:
        logger.error("PatientServiceError in update_patient webhook: %s", exc)
        return {
            "toolCallId": tool_call_id,
            "result": (
                "Error: there was a problem saving the update. "
                "Please try again in a moment — your other information was not lost."
            ),
        }


def _handle_tool_calls(message: dict) -> dict:
    """
    Dispatch each tool call in the message and collect results.
    Returns the Vapi-expected  { "results": [...] }  envelope.
    """
    tool_call_list = message.get("toolCallList", [])
    results = []

    for tc in tool_call_list:
        fn_name = tc.get("function", {}).get("name", "")

        if fn_name == "update_patient":
            results.append(_handle_update_patient(tc))
        else:
            # Unknown tool — return an explanatory error so the LLM knows
            results.append({
                "toolCallId": tc.get("id", "unknown"),
                "result": f"Error: unknown tool '{fn_name}'.",
            })

    return {"results": results}


# ---------------------------------------------------------------------------
# Call-report logger
# ---------------------------------------------------------------------------


def _log_call_report(message: dict) -> None:
    """
    Log the end-of-call report (summary + transcript) to stdout.
    Phase 9 (stretch) can extend this to persist the transcript to Supabase.
    """
    call_id = message.get("call", {}).get("id", "unknown")
    summary = message.get("summary", "(no summary)")
    transcript = message.get("transcript", "(no transcript)")
    recording_url = message.get("recordingUrl", "")
    ended_reason = message.get("endedReason", "unknown")

    logger.info(
        "=== END OF CALL REPORT ===\n"
        "call_id       : %s\n"
        "ended_reason  : %s\n"
        "recording_url : %s\n"
        "summary       :\n%s\n"
        "transcript    :\n%s\n"
        "==========================",
        call_id,
        ended_reason,
        recording_url,
        summary,
        transcript,
    )


# ---------------------------------------------------------------------------
# Main webhook endpoint
# ---------------------------------------------------------------------------


@router.post("/vapi")
async def vapi_webhook(
    request: Request,
    x_vapi_secret: str | None = Header(None, alias="x-vapi-secret"),
):
    """
    Main Vapi server-message endpoint.

    Dispatches on message.type:
      - "tool-calls"          → run tool handlers, return results envelope
      - "end-of-call-report"  → log to stdout, return 200 {}
      - (anything else)       → return 200 {}
    """
    _verify_secret(x_vapi_secret)

    payload = await request.json()
    message = payload.get("message", {})
    message_type = message.get("type")

    if message_type == "tool-calls":
        return _handle_tool_calls(message)

    if message_type == "end-of-call-report":
        _log_call_report(message)
        return {}

    # All other Vapi event types (status-update, speech-update, etc.)
    return {}
