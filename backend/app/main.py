"""
main.py
~~~~~~~
FastAPI application entry point.

Mounts:
  - /patients   →  api/routes/patients.py
  - /webhooks   →  api/routes/vapi_webhook.py
  - GET /health →  inline health-check (used by Heroku / uptime monitors)

Global exception handlers convert internal exceptions into the standard
{ "data": null, "error": { "code": "...", "message": "...", "field": "..." } }
envelope so every error response has a consistent shape.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import patients, vapi_webhook
from app.core.exceptions import PatientNotFoundError, PatientServiceError

app = FastAPI(
    title="Patient Registration Voice Agent API",
    description=(
        "FastAPI backend for the voice-AI patient registration system. "
        "Exposes a REST API consumed by the Next.js dashboard and by Vapi tool calls."
    ),
    version="0.2.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the Next.js dashboard (any origin in dev; tighten for prod)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(PatientNotFoundError)
async def patient_not_found_handler(request: Request, exc: PatientNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "data": None,
            "error": {
                "code": "NOT_FOUND",
                "message": str(exc),
                "field": None,
            },
        },
    )


@app.exception_handler(PatientServiceError)
async def patient_service_error_handler(request: Request, exc: PatientServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "error": {
                "code": "DATABASE_ERROR",
                "message": str(exc),
                "field": None,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Convert Pydantic validation failures into our envelope.

    The error message is already written in caller-readable language (see
    schemas/patient.py validators), so it can be relayed verbatim by the
    voice agent.
    """
    errors = exc.errors()
    first = errors[0] if errors else {}

    # Build a human-readable field name (skip "body" / "query" prefixes)
    loc = [str(l) for l in first.get("loc", []) if l not in ("body", "query")]
    field = loc[-1] if loc else None

    # Pydantic v2 prefixes custom ValueError messages with "Value error, "
    raw_msg = first.get("msg", "Validation error.")
    message = raw_msg.replace("Value error, ", "")

    return JSONResponse(
        status_code=422,
        content={
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "field": field,
            },
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "field": None,
            },
        },
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(patients.router)
app.include_router(vapi_webhook.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["meta"])
async def health():
    """Returns 200 OK as long as the process is running."""
    return {"status": "ok"}
