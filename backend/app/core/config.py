"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Server
    env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: str = "http://localhost:19006,http://localhost:8081"
    
    # Database
    database_url: str = "sqlite:///./data/quran_notes.db"
    
    # Storage
    upload_dir: str = "./data/uploads"
    max_upload_mb: int = 60

    # Storage backend selection
    # - local: store uploads under upload_dir on disk
    # - r2: Cloudflare R2 (S3-compatible)
    storage_backend: str = "local"

    # S3-compatible storage (used for R2 and other S3 APIs)
    s3_endpoint_url: str = ""
    s3_bucket: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_region: str = "auto"
    s3_prefix: str = ""  # optional prefix, e.g. "quran-notes"

    # Local temp dir for downloaded remote files during processing
    tmp_dir: str = "./data/tmp"

    # Processing reliability
    # Prevent duplicate concurrent processing of the same session.
    processing_lease_minutes: int = 10

    # In-process stuck-session recovery
    sweeper_enabled: bool = True
    sweeper_interval_seconds: int = 300
    stuck_threshold_minutes: int = 45
    stuck_max_age_minutes: int = 120
    
    # OpenAI
    openai_api_key: str = "changeme"
    openai_model_translate: str = "gpt-4o-mini"
    openai_model_summarize: str = "gpt-4o-mini"
    openai_model_transcribe: str = "whisper-1"
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def max_upload_bytes(self) -> int:
        """Convert max upload MB to bytes."""
        return self.max_upload_mb * 1024 * 1024


# Global settings instance
settings = Settings()

