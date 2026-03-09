"""数据库配置管理模块。

用于保存和加载 Setup 向导中配置的数据库连接信息。
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = Path("./data/db_config.json")


class DatabaseConfig:
    """数据库配置类。"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "dian_bot",
        username: str = "postgres",
        password: str = "postgres",
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password

    @property
    def database_url(self) -> str:
        """构建数据库连接 URL。"""
        return (
            f"postgresql+asyncpg://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    def save(self) -> bool:
        """保存配置到文件。

        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

            config_data = {
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "username": self.username,
                "password": self.password,
            }

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"数据库配置已保存到：{CONFIG_FILE}")
            return True
        except Exception as e:
            logger.error(f"保存数据库配置失败：{e}")
            return False

    @classmethod
    def load(cls) -> Optional["DatabaseConfig"]:
        """从文件加载配置。

        Returns:
            Optional[DatabaseConfig]: 配置对象，如果不存在则返回 None
        """
        if not CONFIG_FILE.exists():
            logger.info("数据库配置文件不存在")
            return None

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            config = cls(
                host=config_data.get("host", "localhost"),
                port=config_data.get("port", 5432),
                database=config_data.get("database", "dian_bot"),
                username=config_data.get("username", "postgres"),
                password=config_data.get("password", "postgres"),
            )

            logger.info(f"数据库配置已加载：{config.host}:{config.port}/{config.database}")
            return config
        except Exception as e:
            logger.error(f"加载数据库配置失败：{e}")
            return None

    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置数据库。

        Returns:
            bool: 是否已配置
        """
        return CONFIG_FILE.exists()
