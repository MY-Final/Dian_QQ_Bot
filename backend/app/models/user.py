"""用户数据模型模块。

提供用户表结构定义，用于存储系统管理员账号信息。
"""

import uuid
import uuid as uuid_pkg
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """用户模型类。

    用于存储系统用户的账号信息，包括管理员和普通用户。

    Attributes:
        id: 用户唯一标识符（UUID）
        username: 用户名（唯一）
        password_hash: 密码哈希值
        email: 用户邮箱
        role: 用户角色（admin/user）
        created_at: 创建时间
        last_login: 最后登录时间
    """

    __tablename__ = "users"

    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")  # admin / user
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
