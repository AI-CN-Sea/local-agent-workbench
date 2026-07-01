from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Local Agent Workbench"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./local_agent_workbench.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    upload_storage_root: str = "projects"
    max_upload_bytes: int = 20 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
