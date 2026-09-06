# Patient Registration Voice AI

A fully automated, conversational AI phone agent that handles patient intake and registration end-to-end — from answering the call and collecting information naturally, to validating data, detecting returning patients, and persisting records directly to a production database. No manual data entry required.

---

## Submission Details

| | |
|---|---|
| **Repository** | https://github.com/muhammadaman04/Patient-Registration-System-Voice-Agent |
| **Phone Number** | `+1 (516) 990-9169` |
| **API Base URL** | https://patient-voice-backend-edf2f824c35b.herokuapp.com |
| **Live Dashboard** | https://patient-registration-system-voice-a.vercel.app |
| **API Docs** | https://patient-voice-backend-edf2f824c35b.herokuapp.com/docs |

### How to Test
1. Call **`+1 (516) 990-9169`** and wait for the AI to greet you.
2. Speak naturally — provide your name, date of birth, sex, phone number, and address conversationally.
3. The AI validates as you go (e.g. rejects future dates of birth, malformed zip codes, or invalid state abbreviations).
4. After required fields, the AI offers: *"I can also collect your insurance info, emergency contact, and preferred language — would you like to provide any of those?"*
5. The AI reads everything back and asks for your explicit verbal confirmation before saving.
6. Once confirmed, the record is saved and the AI ends the call.
7. Open the **[Live Dashboard](https://patient-registration-system-voice-a.vercel.app)** — your record appears instantly.
8. **Bonus:** Call back with the same phone number. The AI detects the existing record and asks: *"It looks like we already have a record for [Name]. Would you like to update your information instead?"*

---

## Technical Architecture

This is a production-grade monorepo with a clean separation of concerns across four layers:

```
Phone Call
    │
    ▼
[Vapi] — manages real-time audio, STT, TTS, and LLM orchestration
    │
    ├─ Tool call: GET /patients?phone_number=... ──────► [FastAPI Backend]
    ├─ Tool call: POST /patients ──────────────────────► [FastAPI Backend]
    └─ Webhook: POST /webhooks/vapi (update_patient) ──► [FastAPI Backend]
                                                              │
                                                              ▼
                                                       [Supabase / PostgreSQL]
                                                              │
                                                              ▼
                                               [Next.js Dashboard — Vercel]
```

### Layer 1 — Voice Orchestration (Vapi)
Vapi manages the entire real-time audio pipeline: call handling, STT, TTS, and LLM invocation. The agent is driven by a detailed system prompt and four JSON Schema tool definitions. There is **zero custom WebSocket or audio pipeline code** — Vapi eliminates that entirely.

### Layer 2 — REST API Backend (FastAPI + Python)
A stateless, async REST API with five endpoints (`GET`, `POST`, `PUT`, `DELETE /patients` + `POST /webhooks/vapi`). All inputs are validated by Pydantic with caller-readable error messages so the agent can relay them verbatim. A global exception handler enforces a consistent `{ "data": ..., "error": ... }` envelope on every response.

### Layer 3 — Database (Supabase / PostgreSQL)
A fully constrained PostgreSQL schema with 18 fields, CHECK constraints, a soft-delete `deleted_at` column, partial indexes on `phone_number` and `last_name`, and an `updated_at` trigger. Records are never hard-deleted.

### Layer 4 — Admin Dashboard (Next.js + Vercel)
A real-time patient management dashboard. Displays all active patient records pulled live from the backend. Supports adding and soft-deleting patients directly from the UI.

---

## Tech Stack

| Layer | Technology | Role | Key Metric |
|---|---|---|---|
| **Telephony** | Vapi | Call handling, agent orchestration, tool execution | Industry-standard voice AI platform |
| **Speech-to-Text (STT)** | Soniox STT RT v5 | Transcribes caller speech to text in real time | **1.8% Word Error Rate** |
| **LLM** | GPT-OSS 120B (via Groq) | Drives conversational reasoning and tool-call decisions | 500ms latency |
| **Text-to-Speech (TTS)** | Vapi Savannah v2 | Synthesizes the AI's spoken responses | Humanness score: 92 |
| **Backend API** | FastAPI (Python 3.11) | REST API for patient CRUD, webhook handler, validation | Async, auto-generated OpenAPI docs |
| **Data Validation** | Pydantic v2 | Strict input validation with caller-readable error messages | Errors relay verbatim to caller |
| **Database** | Supabase (PostgreSQL) | Persistent patient records with constraints & soft-delete | Managed, zero-ops |
| **Backend Hosting** | Heroku (Basic Dyno) | 24/7 live backend, always warm — no cold starts | Zero downtime |
| **Frontend** | Next.js 14 + React + TypeScript | Admin dashboard for viewing & managing records | App Router, SSR-ready |
| **Frontend Hosting** | Vercel | Auto-deploy from GitHub, global CDN | Zero-config |
| **Setup Automation** | Python script (`setup_vapi_assistant.py`) | Creates/updates the Vapi assistant from code reproducibly | Full config-as-code |

---

## Cost Analysis

The voice stack was deliberately chosen for both quality and cost-efficiency:

| Component | Provider | Cost |
|---|---|---|
| Speech-to-Text | Soniox STT RT v5 | $0.004/min |
| LLM | GPT-OSS 120B via Groq | $0.01/min |
| Text-to-Speech | Vapi Savannah v2 | $0.02/min |
| **Total per call minute** | | **~$0.08/min** |

A typical 5-minute patient registration call costs approximately **$0.40 total** — well within a viable production budget for a medical practice.

**Why Soniox over Deepgram?** Soniox STT RT v5 delivers a **1.8% Word Error Rate** compared to Deepgram Nova-2's ~3.3%. For a patient registration use case — where the agent must accurately capture names, street addresses, city names, and dates of birth — this translates directly to fewer incorrect records saved. A single misheard field (e.g. "Austin" → "Awesome", or "Davis" → "Davies") could corrupt a patient record, making STT accuracy the most important quality metric in this system.

---

## Design Decisions

### 1. Vapi over a Custom WebSocket Audio Pipeline
**Decision:** Use Vapi as the telephony and orchestration layer rather than building a custom pipeline with Twilio + Pipecat/Deepgram + a self-managed TTS.

**Rationale:** A hand-rolled pipeline requires managing WebSocket streams, STT/TTS latency synchronization, and complex state machines — all high-risk, time-consuming work orthogonal to the core problem (patient registration logic). Vapi handles real-time audio, STT, LLM invocation, TTS, and tool execution as a managed service. This allowed full engineering focus to go to the data model, API design, validation logic, and conversation prompt quality.

**Trade-off:** The system is coupled to Vapi's platform. A fully custom pipeline would be more resilient to vendor outages but would take significantly longer to build and debug correctly.

---

### 2. STT Provider: Soniox STT RT v5 over Deepgram Nova-2
**Decision:** Use Soniox STT RT v5 as the speech-to-text provider.

| Metric | Soniox STT RT v5 | Deepgram Nova-2 |
|---|---|---|
| Word Error Rate | **1.8%** | ~3.3% |
| Latency | 410ms | ~300ms |
| Cost | $0.004/min | $0.0043/min |
| Accent resilience | High | Moderate |

**Rationale:** WER is the critical metric for this use case. Patients speak street addresses, city names, uncommon last names, and dates — all fields highly sensitive to transcription errors. Soniox's 1.8% WER nearly halves the error rate versus Deepgram, directly reducing the likelihood of a corrupted patient record. The slightly higher latency (410ms vs ~300ms) is imperceptible to a human caller and is an acceptable trade-off.

---

### 3. LLM: GPT-OSS 120B (Groq) for Conversational Reasoning
**Decision:** Use GPT-OSS 120B via Groq as the conversational LLM.

**Rationale:** Patient registration requires handling a highly variable conversation — callers interrupt, provide multiple fields at once, correct themselves mid-sentence, and occasionally ask clarifying questions. A 120B parameter model has significantly stronger multi-turn reasoning capabilities than smaller models, directly improving the conversational quality dimension. Groq's inference infrastructure delivers this at low latency (~500ms) and low cost ($0.01/min).

**Trade-off:** A smaller model (e.g. GPT-4o Mini) would be cheaper and potentially more predictable on strict JSON schema adherence for tool calls. The 120B model is the stronger conversationalist but slightly less constrained in output format.

---

### 4. Soft-Delete over Hard-Delete for Patient Records
**Decision:** All delete operations set `deleted_at = now()` on the row. No records are ever physically removed from the database.

**Rationale:** In a medical context, hard-deleting patient records is almost never appropriate. Soft-delete preserves the audit trail, allows recovery from accidental deletions, and mirrors how production EHR systems handle data. All queries filter on `deleted_at IS NULL` so soft-deleted records are invisible to the voice agent and the dashboard, while remaining recoverable by an administrator directly in the database.

---

### 5. Webhook Pattern for `update_patient`
**Decision:** The `update_patient` tool uses a Vapi Function tool type (webhook to `POST /webhooks/vapi`) rather than an API Request tool.

**Rationale:** Vapi's `apiRequest` tool type only supports `GET` and `POST`. A patient update is semantically a `PUT`/`PATCH` operation. Using a webhook handler lets our backend correctly route to the `update_patient` service function while maintaining proper REST semantics internally. The webhook endpoint verifies the `X-Vapi-Secret` header before processing any request, providing security for this custom entry point.

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Supabase project (free tier works)
- A Vapi account (free tier works)

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your values
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_BASE_URL
npm run dev
```

### Setting up the Vapi Assistant
```bash
cd backend
python scripts/setup_vapi_assistant.py
```
This script creates the Vapi assistant, configures all 4 tools (`lookup_patient_by_phone`, `create_patient`, `update_patient`, `endCall`), and binds the phone number. Run it once to create, or again to update after prompt changes.

---

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (full DB access) |
| `VAPI_API_KEY` | Vapi API key for creating/updating the assistant |
| `VAPI_ASSISTANT_ID` | ID of the existing assistant (auto-populated after first setup run) |
| `VAPI_SERVER_SECRET` | Secret Vapi sends as a header on webhook calls — verified before processing |
| `PUBLIC_API_BASE_URL` | Publicly reachable base URL of this backend (Heroku URL or ngrok for local dev) |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the FastAPI backend |

---

## Known Limitations & Trade-offs

- **No call transcript persistence:** Call transcripts and audio recordings are available in the Vapi dashboard but are not stored in our own database. A production system would log these to a `call_logs` table for audit and compliance purposes.

- **No automated retry on `create_patient`:** If the POST to save a patient fails transiently, the agent will relay the error to the caller and ask them to confirm again rather than silently retrying. The `backoffPlan` Vapi field was omitted during development due to uncertain schema validation constraints.

- **English only:** The agent operates in English. The `preferred_language` field is collected and stored but does not dynamically switch the conversation language.

- **No REST API authentication:** The `/patients` endpoints rely on CORS and the Supabase service key. A production deployment would add JWT-based auth or API key gating.
