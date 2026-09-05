"""
core/config.py
~~~~~~~~~~~~~~
Loads all environment variables from .env and exposes them as a validated
Settings object. Every other module in the app imports from here — never
reads os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env file."""

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # Vapi
    vapi_api_key: str = ""
    vapi_assistant_id: str = ""
    vapi_server_secret: str

    # Public-facing API base URL (used by setup_vapi_assistant.py)
    public_api_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
