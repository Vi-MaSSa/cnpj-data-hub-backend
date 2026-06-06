from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CNPJ Data Hub API"
    app_env: str = "development"
    app_debug: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str
    redis_url: str
    redis_queue_name: str = "default"

    data_local_path: str = "/app/data"
    exports_local_path: str = "/app/exports"

    active_dataset_version: str | None = None

    export_max_rows: int = 50000
    export_expires_hours: int = 24

    download_timeout_seconds: int = 120
    download_max_retries: int = 3

    log_level: str = "INFO"

    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()