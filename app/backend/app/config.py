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
    # "anthropic" and "openai" call the provider from the backend, so API keys
    # stay server-side and never reach the browser.
    ai_provider: str = "mock"

    # Anthropic configuration
    anthropic_api_key: str = ""
    ai_model: str = "claude-opus-5-5"

    # OpenAI configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    # Live web research for roadmaps and the career chatbot (OpenAI web_search
    # tool). Used for roadmap generation and for messages about courses,
    # programs, certificates, or learning resources. Each search is billed by
    # OpenAI, so it is off unless enabled.
    openai_web_search: bool = False
    # Optional comma-separated allowlist (subdomains included). Empty means the
    # open web, with official SFSU and other reputable providers preferred.
    openai_web_search_domains: str = ""
    # Sites never accepted as resource sources (subdomains included): forums,
    # video and Q&A sites, and unofficial catalog mirrors. Comma-separated.
    openai_web_search_blocked_domains: str = "courseleaf.com,reddit.com,youtube.com,quora.com"
    # Before a researched link is shown, the server checks that it opens over
    # valid HTTPS (no page content is kept). Missing pages, TLS/connection
    # errors, timeouts, and broken redirects are dropped.
    resource_link_check: bool = True
    resource_link_check_timeout: float = 5.0
    # Upper bound on searches in one request (OpenAI max_tool_calls).
    openai_max_web_searches: int = 3
    # "low" | "medium" | "high": how much page text each search adds (cost).
    openai_web_search_context: str = "low"
    # Reasoning effort for the career assistant ("minimal" | "low" | "medium" |
    # "high"). Reasoning tokens count toward the output limits below.
    openai_reasoning_effort: str = "low"
    # Output-token caps (reasoning included); longer answers are cut off by
    # OpenAI and rejected with a clear error.
    openai_max_output_tokens_chat: int = 3000
    openai_max_output_tokens_roadmap: int = 10000

    # Per-student limits on billed AI calls (checked before calling the provider).
    ai_roadmap_generations_per_day: int = 5
    ai_chat_messages_per_hour: int = 30

    ai_timeout_seconds: float = 120.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
