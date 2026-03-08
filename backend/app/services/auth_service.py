"""认证业务服务模块。"""

import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthUserNotFoundError,
    InvalidCredentialsError,
    TokenValidationError,
    UserAlreadyExistsError,
)
from app.models.user import User
from app.utils.jwt import create_access_token, create_refresh_token, verify_token
from app.utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthService:
    """认证业务服务。"""

    async def login(
        self,
        db: AsyncSession,
        username: str,
        password: str,
    ) -> dict[str, object]:
        """用户登录。

        Args:
            db: 数据库会话
            username: 用户名
            password: 密码

        Returns:
            dict[str, object]: 登录成功数据

        Raises:
            InvalidCredentialsError: 凭证错误时抛出
        """
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        user.last_login = datetime.utcnow()
        await db.flush()

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
            },
            expires_delta=timedelta(hours=settings.access_token_expire_hours),
        )

        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=settings.refresh_token_expire_days),
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        }

    async def register(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
    ) -> dict[str, object]:
        """注册用户。

        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱
            password: 密码

        Returns:
            dict[str, object]: 注册成功用户数据

        Raises:
            UserAlreadyExistsError: 用户名或邮箱重复时抛出
        """
        existing_user_result = await db.execute(select(User).where(User.username == username))
        existing_user = existing_user_result.scalar_one_or_none()
        if existing_user is not None:
            raise UserAlreadyExistsError("用户名已存在")

        existing_email_result = await db.execute(select(User).where(User.email == email))
        existing_email = existing_email_result.scalar_one_or_none()
        if existing_email is not None:
            raise UserAlreadyExistsError("邮箱已被使用")

        user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="user",
            created_at=datetime.utcnow(),
        )

        db.add(user)
        await db.flush()

        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, str]:
        """刷新访问令牌。

        Args:
            refresh_token: 刷新令牌

        Returns:
            dict[str, str]: 新 access token 数据

        Raises:
            TokenValidationError: 刷新令牌无效时抛出
        """
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise TokenValidationError()

        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise TokenValidationError()

        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=settings.access_token_expire_hours),
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    async def get_current_user_profile(
        self,
        db: AsyncSession,
        authorization: str | None,
    ) -> dict[str, object]:
        """获取当前用户信息。

        Args:
            db: 数据库会话
            authorization: Authorization 头

        Returns:
            dict[str, object]: 用户信息

        Raises:
            TokenValidationError: Token 无效时抛出
            AuthUserNotFoundError: 用户不存在时抛出
        """
        token = self._extract_bearer_token(authorization)
        payload = verify_token(token, token_type="access")
        if not payload:
            raise TokenValidationError()

        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise TokenValidationError()

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError as exc:
            raise TokenValidationError() from exc

        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
        if user is None:
            raise AuthUserNotFoundError()

        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

    @staticmethod
    def _extract_bearer_token(authorization: str | None) -> str:
        """提取 Bearer Token。

        Args:
            authorization: Authorization 头

        Returns:
            str: token

        Raises:
            TokenValidationError: token 缺失或格式错误时抛出
        """
        if authorization is None:
            raise TokenValidationError()

        auth_parts = authorization.strip().split(" ", 1)
        if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer":
            raise TokenValidationError()

        token = auth_parts[1].strip()
        if not token:
            raise TokenValidationError()

        return token
