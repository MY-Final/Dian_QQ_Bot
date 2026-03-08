"""API 依赖模块。"""

import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.jwt import verify_token


def _extract_bearer_token(authorization: str | None) -> str:
    """从 Authorization 头提取 Bearer Token。

    Args:
        authorization: Authorization 请求头

    Returns:
        str: token 字符串

    Raises:
        HTTPException: Token 缺失或格式错误时抛出
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证头，请先登录",
        )

    auth_parts = authorization.strip().split(" ", 1)
    if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证头格式",
        )

    token = auth_parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 不能为空",
        )

    return token


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前认证用户。

    Args:
        authorization: Authorization 请求头
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 认证失败时抛出
    """
    token = _extract_bearer_token(authorization)

    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        ) from exc

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被删除",
        )

    return user


async def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """要求当前用户具有管理员权限。

    Args:
        current_user: 当前用户

    Returns:
        User: 当前管理员用户

    Raises:
        HTTPException: 权限不足时抛出
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可执行该操作",
        )

    return current_user
