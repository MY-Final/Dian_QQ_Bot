"""应用配置模块。

使用 Pydantic Settings 进行配置管理，支持从环境变量读取配置。
"""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类。

    所有配置都支持从环境变量读取，也可以通过 .env 文件配置。
    """

    # 应用配置
    app_name: str = Field(default="Dian QQ Bot", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")

    # 服务器配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # 路径配置
    data_dir: Path = Field(default=Path("./data"), env="DATA_DIR")
    instances_dir: Path = Field(default=Path("./data/instances"), env="INSTANCES_DIR")
    logs_dir: Path = Field(default=Path("./logs"), env="LOGS_DIR")

    # Docker 配置
    docker_socket: Path = Field(
        default=Path("npipe:////./pipe/docker_engine"), env="DOCKER_SOCKET"
    )
    container_prefix: str = Field(default="dian", env="CONTAINER_PREFIX")
    napcat_image: str = Field(
        default="mlikiowa/napcat-docker:latest", env="NAPCAT_IMAGE"
    )

    # 端口范围配置（适用于 Bot 实例）
    port_range_start: int = Field(default=30000, env="PORT_RANGE_START")
    port_range_end: int = Field(default=40000, env="PORT_RANGE_END")

    # 数据库配置
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/bot.db", env="DATABASE_URL"
    )

    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs) -> None:
        """初始化配置并确保必要目录存在。"""
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保必要的目录存在。"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.instances_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# 全局配置单例
settings = Settings()
