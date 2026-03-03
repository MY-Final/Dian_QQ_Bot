"""Bot 实例数据库模型模块。

包含 SQLAlchemy ORM 模型，用于数据库持久化。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """数据库模型基类。"""

    pass


class BotInstanceDB(Base):
    """Bot 实例数据库模型。"""

    __tablename__ = "bot_instances"

    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    qq_number: Mapped[str] = mapped_column(String(15), nullable=False)
    protocol: Mapped[str] = mapped_column(String(20), nullable=False, default="napcat")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    container_name: Mapped[str] = mapped_column(String(100), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)  # HTTP 端口
    port_web_ui: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Web UI 端口
    port_ws: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # WebSocket 端口
    volume_path: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<BotInstanceDB(id={self.id}, name={self.name}, status={self.status})>"
