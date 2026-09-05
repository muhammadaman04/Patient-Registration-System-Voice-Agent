"""
db/supabase_client.py
~~~~~~~~~~~~~~~~~~~~~
Thin wrapper that initialises and exposes a single Supabase client instance
(service-role key) for use across the application.

Only the backend uses this client. The frontend dashboard NEVER touches
Supabase directly — it always goes through the REST API.
"""

from supabase import Client, create_client

from app.core.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    """Return the singleton Supabase client, creating it on first call."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client
