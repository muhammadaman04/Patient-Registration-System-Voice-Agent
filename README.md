# Patient Registration Voice AI

A fully automated, conversational AI phone agent that handles patient intake and registration, seamlessly synced to a production database and web dashboard. 

## Submission Details

* **Repository URL:** https://github.com/muhammadaman04/Patient-Registration-System-Voice-Agent
* **Phone Number to Call:** `+15169909169`
* **API Base URL (Backend):** `https://patient-voice-backend-edf2f824c35b.herokuapp.com`
* **Live Web Dashboard:** `https://patient-registration-system-voice-a.vercel.app`

### Notes for Testing:
1. Call the phone number and wait for the AI to greet you.
2. Provide your Name, Date of Birth, Sex, Phone Number, and Address naturally.
3. The AI will validate the information dynamically (e.g., rejecting future dates of birth or invalid zip codes).
4. The AI will read the information back to you for explicit confirmation.
5. Once you confirm, the AI will save the data to the database and end the call.
6. Open the **Live Web Dashboard** to see your newly registered patient record instantly appear!
7. *Bonus:* If you call back and provide the exact same phone number, the AI will recognize you as an existing patient and ask if you want to update your record instead of creating a new one.

---

## Technical Architecture

This monorepo contains a complete end-to-end system:

### 1. Voice Agent (Vapi + GPT OSS)
Instead of building a fragile, hand-rolled state machine, the conversational logic is driven dynamically using **Vapi** and the **openai/gpt-oss-120b** model. The AI is securely provided with JSON Schema tool definitions that dictate exactly what information must be collected before the backend can be called. 

### 2. Backend (FastAPI + Python)
A high-performance REST API built with **FastAPI**. It handles complex validation using **Pydantic** and securely communicates with the database. It exposes strict `GET`, `POST`, `PUT`, and `DELETE` endpoints. The voice agent communicates directly with these endpoints via webhooks. Hosted on **Heroku**.

### 3. Database (Supabase / PostgreSQL)
A robust **PostgreSQL** database hosted on **Supabase**. The schema includes constraints (e.g., phone number length, valid dates) and triggers. Records are soft-deleted to maintain data integrity. 

### 4. Frontend Dashboard (Next.js + React)
A modern, glassmorphism-styled web dashboard built with **Next.js** and **React**. It fetches live data from the FastAPI backend, allowing administrators to view and manage registered patients in real-time. Hosted on **Vercel**.

## Local Development

If you wish to run the project locally:

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
*(Requires a `.env` file with `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`)*

### Frontend
```bash
cd frontend
npm install
npm run dev
```
*(Requires a `.env.local` file with `NEXT_PUBLIC_API_BASE_URL`)*

---

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (has full DB access) |
| `VAPI_API_KEY` | Vapi API key for creating/updating the assistant |
| `VAPI_ASSISTANT_ID` | ID of the existing Vapi assistant (populated after first run of setup script) |
| `VAPI_SERVER_SECRET` | Secret header value Vapi sends on webhook calls — verified in `/webhooks/vapi` |
| `PUBLIC_API_BASE_URL` | Publicly reachable base URL of this backend (e.g. Heroku URL or ngrok tunnel) |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the FastAPI backend (e.g. Heroku URL) |

---

## Tech Stack Justification

| Component | Choice | Reason |
|---|---|---|
| **Telephony & LLM orchestration** | Vapi | Eliminates the need for a hand-rolled WebSocket audio pipeline, STT, and TTS stack. Vapi owns the real-time audio layer entirely, reducing the highest-risk part of the build to zero custom code. |
| **LLM** | GPT-OSS 120B via Vapi | High-capability open model available directly through Vapi's provider keys. No additional API integration required. |
| **Backend** | FastAPI + Python | Async-native, excellent Pydantic integration for strict input validation, clean OpenAPI docs auto-generated, and fast development velocity. |
| **Database** | Supabase (PostgreSQL) | Managed Postgres with a generous free tier, built-in REST client, and SQL migrations. Soft-delete support out of the box via `deleted_at` column. |
| **Frontend** | Next.js + React | App Router enables server/client component split; straightforward deployment on Vercel; TypeScript for type safety. |
| **Hosting** | Heroku (backend) + Vercel (frontend) | Both have zero-config deploys from GitHub, free/low-cost tiers, and reliable uptime for review purposes. |

---

## Known Limitations & Trade-offs

- **No call recording / transcript storage:** Call transcripts and audio are available in the Vapi dashboard but are not persisted to our own database. A production system would log transcripts to a `call_logs` table for audit purposes.

- **No automated retry on `create_patient`:** The `backoffPlan` field was omitted from the `create_patient` apiRequest tool due to uncertain schema validation during development. If the POST fails transiently, the agent will relay the error to the caller and ask them to confirm again rather than silently retrying.

- **Single-language support:** The voice agent operates in English only. The `preferred_language` field is collected and stored, but the agent does not dynamically switch the conversation language.

- **No authentication on the REST API:** The `/patients` endpoints are protected only by CORS and the Supabase service key on the backend. A production deployment would add JWT-based auth or API key gating to prevent unauthorized access.

- **No automated tests run in CI:** Tests exist in `backend/tests/` but there is no GitHub Actions workflow to run them automatically on each push.
