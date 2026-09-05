"""
scripts/setup_vapi_assistant.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Creates or updates the Vapi Assistant and provisions a free US phone number.

Run once after Phase 2 is working:
    cd backend/
    python scripts/setup_vapi_assistant.py

Prerequisites:
  1. VAPI_API_KEY set in backend/.env
     → copy from dashboard.vapi.ai → Account → API Keys
  2. VAPI_SERVER_SECRET set in backend/.env
     → any strong random string you choose (e.g. from: python -c "import secrets; print(secrets.token_hex(32))")
  3. PUBLIC_API_BASE_URL set to a publicly reachable URL.
     !! IMPORTANT: http://localhost:8000 will NOT work for Vapi webhooks
     because Vapi's servers cannot reach your local machine.
     Use ngrok to expose your local server:
         ngrok http 8000
     Then set PUBLIC_API_BASE_URL=https://<your-ngrok-id>.ngrok-free.app
     and re-run this script.

After the first run:
  - Copy the printed VAPI_ASSISTANT_ID into backend/.env
  - Subsequent runs will PATCH the existing assistant instead of duplicating it.
"""

import json
import os
import sys

# ── Path setup ────────────────────────────────────────────────────────────────
# Add backend/ to sys.path so we can import app.* modules from this script.
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_DIR)

# ── Load .env before importing anything that reads settings ───────────────────
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(_BACKEND_DIR, ".env"))

# ── Now safe to import app modules ────────────────────────────────────────────
import requests

from app.voice.prompts import SYSTEM_PROMPT
from app.voice.tool_schemas import ALL_TOOLS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "").strip()
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID", "").strip()
VAPI_SERVER_SECRET = os.getenv("VAPI_SERVER_SECRET", "").strip()
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000").strip()

VAPI_BASE = "https://api.vapi.ai"
HEADERS = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json",
}

# We use Groq because it is extremely fast and free/very cheap for open source models
MODEL_PROVIDER = "groq"
MODEL_NAME = "openai/gpt-oss-120b"

ASSISTANT_NAME = "Patient Registration Agent"
FIRST_MESSAGE = (
    "Hi, thanks for calling! I can help you register as a new patient. "
    "Do you have a few minutes?"
)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_env() -> None:
    errors = []

    if not VAPI_API_KEY:
        errors.append("VAPI_API_KEY is not set. Copy it from dashboard.vapi.ai → Account → API Keys.")

    if not VAPI_SERVER_SECRET or VAPI_SERVER_SECRET == "your-vapi-webhook-shared-secret":
        errors.append(
            "VAPI_SERVER_SECRET is not set or is still the placeholder value.\n"
            "  Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"\n"
            "  Then paste it into backend/.env"
        )

    if "localhost" in PUBLIC_API_BASE_URL or "127.0.0.1" in PUBLIC_API_BASE_URL:
        print(
            "\n⚠️  WARNING: PUBLIC_API_BASE_URL is set to a local address:\n"
            f"   {PUBLIC_API_BASE_URL}\n"
            "   Vapi's servers cannot reach localhost. The update_patient webhook\n"
            "   and the apiRequest tools will fail during real calls.\n"
            "   Use ngrok to expose your local server:\n"
            "     1. ngrok http 8000\n"
            "     2. Copy the https URL (e.g. https://abc123.ngrok-free.app)\n"
            "     3. Set PUBLIC_API_BASE_URL=https://abc123.ngrok-free.app in .env\n"
            "     4. Re-run this script\n"
        )
        # Don't block — allow localhost for schema inspection / offline testing

    if errors:
        print("\n❌  Setup cannot continue. Fix these issues in backend/.env:\n")
        for e in errors:
            print(f"  • {e}\n")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Assistant payload builder
# ---------------------------------------------------------------------------


def build_assistant_payload() -> dict:
    """Return the full Vapi assistant configuration dict."""
    return {
        "name": ASSISTANT_NAME,
        "model": {
            "provider": MODEL_PROVIDER,
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT}
            ],
            "temperature": 0.3,
            "tools": ALL_TOOLS,        # ← moved here, this is where Vapi expects it
        },
        "voice": {
            "provider": "openai",
            "voiceId": "shimmer",
        },
        "firstMessage": FIRST_MESSAGE,
        "serverUrl": PUBLIC_API_BASE_URL.rstrip("/") + "/webhooks/vapi",
        "serverUrlSecret": VAPI_SERVER_SECRET,
        "endCallFunctionEnabled": True,
        "recordingEnabled": True,
    }


# ---------------------------------------------------------------------------
# Vapi API helpers
# ---------------------------------------------------------------------------


def create_assistant(payload: dict) -> dict:
    """POST /assistant — create a brand-new assistant."""
    resp = requests.post(f"{VAPI_BASE}/assistant", headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def update_assistant(assistant_id: str, payload: dict) -> dict:
    """PATCH /assistant/{id} — update an existing assistant in-place."""
    resp = requests.patch(
        f"{VAPI_BASE}/assistant/{assistant_id}",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def list_phone_numbers() -> list[dict]:
    """GET /phone-number — list all phone numbers on this account."""
    resp = requests.get(f"{VAPI_BASE}/phone-number", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def create_phone_number(assistant_id: str) -> dict:
    """
    POST /phone-number — provision a free Vapi US number and attach it to
    the given assistant immediately.
    """
    payload = {
        "provider": "vapi",
        "name": "Patient Registration Line",
        "assistantId": assistant_id,
    }
    resp = requests.post(f"{VAPI_BASE}/phone-number", headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def attach_assistant_to_phone(phone_number_id: str, assistant_id: str) -> dict:
    """PATCH /phone-number/{id} — attach an assistant to an existing number."""
    payload = {"assistantId": assistant_id}
    resp = requests.patch(
        f"{VAPI_BASE}/phone-number/{phone_number_id}",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    validate_env()

    print(f"\n🔧  Using model    : {MODEL_PROVIDER} / {MODEL_NAME}")
    print(f"🌐  Backend URL    : {PUBLIC_API_BASE_URL}")
    print(f"🔗  Webhook URL    : {PUBLIC_API_BASE_URL.rstrip('/')}/webhooks/vapi\n")

    payload = build_assistant_payload()

    # ── Step 1: Create or update the assistant ────────────────────────────
    if VAPI_ASSISTANT_ID:
        print(f"🔄  Updating existing assistant  {VAPI_ASSISTANT_ID} …")
        try:
            assistant = update_assistant(VAPI_ASSISTANT_ID, payload)
            print(f"✅  Assistant updated: {assistant['id']}")
        except requests.HTTPError as exc:
            print(f"❌  Failed to update assistant: {exc.response.text}")
            sys.exit(1)
    else:
        print("➕  Creating new assistant …")
        try:
            assistant = create_assistant(payload)
            print(f"✅  Assistant created: {assistant['id']}")
        except requests.HTTPError as exc:
            print(f"❌  Failed to create assistant: {exc.response.text}")
            sys.exit(1)

    assistant_id = assistant["id"]

    # ── Step 2: Provision / reuse a phone number ──────────────────────────
    try:
        existing_numbers = list_phone_numbers()
    except requests.HTTPError as exc:
        print(f"⚠️   Could not list phone numbers: {exc.response.text}")
        existing_numbers = []

    # Find a number already attached to this assistant, or any free Vapi number
    assigned_number = None
    for num in existing_numbers:
        if num.get("assistantId") == assistant_id:
            assigned_number = num
            break

    if assigned_number:
        print(
            f"📞  Reusing existing number  {assigned_number.get('number', assigned_number['id'])}"
            f"  (already attached to this assistant)"
        )
        phone_data = assigned_number
    else:
        # Check if there's an unattached Vapi number we can reuse
        unattached = [
            n for n in existing_numbers
            if n.get("provider") == "vapi" and not n.get("assistantId")
        ]
        if unattached:
            print(f"🔗  Attaching existing unassigned number {unattached[0].get('number')} …")
            try:
                phone_data = attach_assistant_to_phone(unattached[0]["id"], assistant_id)
            except requests.HTTPError as exc:
                print(f"⚠️   Could not attach number: {exc.response.text}")
                phone_data = unattached[0]
        else:
            print("📱  Provisioning a new free Vapi phone number …")
            try:
                phone_data = create_phone_number(assistant_id)
                print(f"✅  Phone number provisioned: {phone_data.get('number', phone_data['id'])}")
            except requests.HTTPError as exc:
                print(f"⚠️   Could not provision phone number: {exc.response.text}")
                print(
                    "    You can provision one manually in the Vapi dashboard:\n"
                    "    Phone Numbers → Add Phone Number → Free Vapi Number\n"
                    "    Then attach it to the assistant."
                )
                phone_data = {}

    # ── Step 3: Print summary and next steps ──────────────────────────────
    phone_number = phone_data.get("number", "(see Vapi dashboard)")

    print("\n" + "=" * 60)
    print("✅  PHASE 3 SETUP COMPLETE")
    print("=" * 60)
    print(f"  VAPI_ASSISTANT_ID = {assistant_id}")
    print(f"  Phone number      = {phone_number}")
    print("=" * 60)
    print("\n📋  Next steps:")
    print(f"  1. Add this to backend/.env:")
    print(f"       VAPI_ASSISTANT_ID={assistant_id}")
    print(f"  2. Call {phone_number} to test the assistant.")
    print(f"  3. Check uvicorn logs — the assistant should make a")
    print(f"     GET /patients request to your backend when it collects a phone number.")
    if "localhost" in PUBLIC_API_BASE_URL:
        print(f"\n  ⚠️  Remember: your backend is on localhost.")
        print(f"     Start ngrok and re-run this script with the ngrok URL")
        print(f"     for real calls to reach your backend.")
    print()


if __name__ == "__main__":
    main()
