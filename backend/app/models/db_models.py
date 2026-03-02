"""Database models for Bot instances."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BotInstanceDB(Base):
    """Database model for Bot instances."""

    __tablename__ = "bot_instances"

    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    qq_number: Mapped[str] = mapped_column(String(15), nullable=False)
    protocol: Mapped[str] = mapped_column(String(20), nullable=False, default="napcat")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    container_name: Mapped[str] = mapped_column(String(100), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
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
