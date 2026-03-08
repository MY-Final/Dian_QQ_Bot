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
    app_name: str = Field(default="Dian QQ Bot", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")

    # 服务器配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # CORS 配置
    cors_allowed_origins: str = Field(
        default=(
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:6173,http://127.0.0.1:6173"
        ),
        env="CORS_ALLOWED_ORIGINS",
    )

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

    # 数据库配置（应用自身使用的数据库，存储 Bot 实例等数据）
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="dian_bot", env="DB_NAME")
    db_user: str = Field(default="postgres", env="DB_USER")
    db_password: str = Field(default="postgres", env="DB_PASSWORD")

    @property
    def database_url(self) -> str:
        """构建数据库连接 URL（应用自身使用的数据库）。"""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # JWT 配置
    jwt_secret_key: str = Field(
        default="change-this-to-a-strong-secret-before-production",
        env="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_hours: int = Field(default=24, env="ACCESS_TOKEN_EXPIRE_HOURS")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略额外的配置项

    def __init__(self, **kwargs) -> None:
        """初始化配置并确保必要目录存在。"""
        super().__init__(**kwargs)
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
