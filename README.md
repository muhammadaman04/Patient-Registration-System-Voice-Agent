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
