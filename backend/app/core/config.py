"""Application configuration module."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_name: str = Field(default="Dian QQ Bot", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # Paths
    data_dir: Path = Field(default=Path("./data"), env="DATA_DIR")
    instances_dir: Path = Field(default=Path("./data/instances"), env="INSTANCES_DIR")
    logs_dir: Path = Field(default=Path("./logs"), env="LOGS_DIR")

    # Docker
    docker_socket: Path = Field(
        default=Path("npipe:////./pipe/docker_engine"), env="DOCKER_SOCKET"
    )
    container_prefix: str = Field(default="dian", env="CONTAINER_PREFIX")
    napcat_image: str = Field(
        default="mlikiowa/napcat-docker:latest", env="NAPCAT_IMAGE"
    )

    # Port range for Bot instances (Windows compatible)
    port_range_start: int = Field(default=30000, env="PORT_RANGE_START")
    port_range_end: int = Field(default=40000, env="PORT_RANGE_END")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/bot.db", env="DATABASE_URL"
    )

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.instances_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
