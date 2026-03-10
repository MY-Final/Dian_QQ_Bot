"""应用配置模块。

使用 Pydantic Settings 进行配置管理，支持从环境变量读取配置。
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类。

    所有配置都支持从环境变量读取，也可以通过 .env 文件配置。
    """

    # 应用配置
    app_name: str = Field(default="Dian QQ Bot")
    debug: bool = Field(default=False)

    # 服务器配置
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # CORS 配置
    cors_allowed_origins: str = Field(
        default=(
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:6173,http://127.0.0.1:6173"
        )
    )

    # 路径配置
    data_dir: Path = Field(default=Path("./data"))
    instances_dir: Path = Field(default=Path("./data/instances"))
    logs_dir: Path = Field(default=Path("./logs"))

    # Docker 配置
    docker_socket: Path = Field(default=Path("npipe:////./pipe/docker_engine"))
    container_prefix: str = Field(default="dian")
    napcat_image: str = Field(default="mlikiowa/napcat-docker:latest")

    # 端口范围配置（适用于 Bot 实例）
    port_range_start: int = Field(default=30000)
    port_range_end: int = Field(default=40000)

    # 数据库配置（应用自身使用的数据库，存储 Bot 实例等数据）
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="dian_bot")
    db_user: str = Field(default="postgres")
    db_password: str = Field(default="Mima123456.@")

    @property
    def database_url(self) -> str:
        """构建数据库连接 URL（应用自身使用的数据库）。"""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # 日志配置
    log_level: str = Field(default="INFO")

    # JWT 配置
    jwt_secret_key: str = Field(
        default="change-this-to-a-strong-secret-before-production"
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_hours: int = Field(default=24)
    refresh_token_expire_days: int = Field(default=7)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def __init__(self, **kwargs: object) -> None:
        """初始化配置并确保必要目录存在。"""
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保必要的目录存在。"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.instances_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @property
    def cors_origins(self) -> list[str]:
        """获取 CORS 允许的来源列表。

        Returns:
            list[str]: 允许跨域访问的来源
        """
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


# 全局配置单例
settings = Settings()
