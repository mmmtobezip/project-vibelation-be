from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = ""
    storage_root: str = "./.storage"
    cors_origins: str = ""
    oidc_issuer: str = ""
    oidc_audience: str = ""
    agent_base_url: str = ""
    agent_mode: str = "mock"
    max_file_bytes: int = 5 * 1024 * 1024
    max_files_per_request: int = 5
    max_md_bytes: int = 1024 * 1024
    max_html_bytes: int = 2_000_000
    idempotency_ttl_seconds: int = 86400
    job_deadline_seconds: int = 1200
    worker_concurrency: int = 2
    log_level: str = "info"
    dev_auth: bool = True
    seed_demo_history: bool = True


settings = Settings()
