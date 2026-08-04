from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "NetWatch AI"
    secret_key: str = "dev-secret-change-in-production"
    database_url: str = "sqlite+aiosqlite:///./netwatch.db"
    access_token_expire_minutes: int = 1440

    gns3_host: str = "127.0.0.1"
    gns3_port: int = 3080
    gns3_user: str = "admin"
    gns3_password: str = "admin"
    gns3_project_id: str = ""

    poll_interval_seconds: int = 30
    topology_sync_interval_seconds: int = 60
    device_stale_minutes: int = 5
    ping_timeout_seconds: int = 2
    snmp_community: str = "public"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"

    fernet_key: str = ""

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
