"""系统设置数据模型模块。

提供系统配置表结构定义，用于存储系统级别的配置信息。
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SystemSetting(Base):
    """系统设置模型类。

    用于存储系统级别的键值对配置信息。

    Attributes:
        key: 配置键名（主键）
        value: 配置值
        description: 配置描述
        updated_at: 更新时间
    """

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<SystemSetting(key={self.key}, value={self.value})>"
