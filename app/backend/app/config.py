from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./careergps.db"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    allowed_origins: str = "http://localhost:5173"
    # Also allowed, so teammates can run the frontend locally (on any Vite port)
    # against the deployed API. Safe because auth uses bearer tokens, not cookies.
    # Set to an empty string to turn it off.
    allowed_origin_regex: str = r"http://(localhost|127\.0\.0\.1)(:\d+)?"

    # Where the React app lives; used to build shareable portfolio links (R17.1).
    frontend_url: str = "http://localhost:5173"
    # Public URL of this API; used to build URLs for locally stored uploads.
    public_api_url: str = "http://localhost:8000"

    # File storage for project images and 3D models (R8, R15).
    # "local" writes to UPLOAD_DIR and serves it at /uploads (dev only — Render's
    # disk is wiped on every deploy). "supabase" uses Supabase Storage.
    storage_backend: str = "local"
    upload_dir: str = "uploads"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_bucket: str = "careergps-media"
    max_image_mb: int = 10
    max_model_mb: int = 50

    # AI career guidance (R10–R14). "mock" returns rule-based guidance with no
    # external calls, so the feature works in dev without an API key.
    # "anthropic" calls Claude through the backend so the key never reaches the browser.
    ai_provider: str = "mock"
    anthropic_api_key: str = ""
    ai_model: str = "claude-opus-5-5"
    ai_timeout_seconds: float = 120.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
