"""认证 API 路由模块。

提供用户认证相关的接口：
- 用户登录
- 用户注册
- 刷新 token
- 获取当前用户信息
"""

import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.utils.jwt import create_access_token, create_refresh_token, verify_token
from app.utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["用户认证"])


def success_response(data: dict[str, object] | None = None, message: str = "操作成功") -> dict[str, object]:
    """生成成功响应。

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        dict[str, object]: 统一格式的成功响应
    """
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: int = 400) -> dict[str, object]:
    """生成错误响应。

    Args:
        message: 错误消息
        code: 错误代码

    Returns:
        dict[str, object]: 统一格式的错误响应
    """
    return {"success": False, "message": message, "code": code, "data": None}


class LoginRequest(BaseModel):
    """登录请求模型。"""

    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class RegisterRequest(BaseModel):
    """注册请求模型。"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型。"""

    refresh_token: str = Field(..., min_length=1, description="刷新令牌")


@router.post("/login", summary="用户登录")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """用户登录接口。

    Args:
        request: 登录请求体
        db: 数据库会话

    Returns:
        JSONResponse: 包含 token 的响应

    Raises:
        RuntimeError: 数据库操作失败时抛出
    """
    logger.info("用户登录尝试：username=%s", request.username)

    try:
        result = await db.execute(select(User).where(User.username == request.username))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("用户不存在：%s", request.username)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("用户名或密码错误", status.HTTP_401_UNAUTHORIZED),
            )

        if not verify_password(request.password, user.password_hash):
            logger.warning("密码错误：username=%s", request.username)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("用户名或密码错误", status.HTTP_401_UNAUTHORIZED),
            )

        user.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(user)

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

        logger.info("用户登录成功：username=%s, role=%s", request.username, user.role)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "user": {
                        "id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                    },
                },
                message="登录成功",
            ),
        )

    except Exception:
        logger.error("登录失败", exc_info=True)
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response("登录失败，请稍后重试", status.HTTP_500_INTERNAL_SERVER_ERROR),
        )


@router.post("/register", summary="用户注册")
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """用户注册接口。

    Args:
        request: 注册请求体
        db: 数据库会话

    Returns:
        JSONResponse: 注册结果

    Raises:
        RuntimeError: 数据库操作失败时抛出
    """
    logger.info("用户注册尝试：username=%s, email=%s", request.username, request.email)

    try:
        existing_user_result = await db.execute(select(User).where(User.username == request.username))
        existing_user = existing_user_result.scalar_one_or_none()
        if existing_user:
            logger.warning("用户名已存在：%s", request.username)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response("用户名已存在", status.HTTP_400_BAD_REQUEST),
            )

        existing_email_result = await db.execute(select(User).where(User.email == str(request.email)))
        existing_email = existing_email_result.scalar_one_or_none()
        if existing_email:
            logger.warning("邮箱已存在：%s", request.email)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response("邮箱已被使用", status.HTTP_400_BAD_REQUEST),
            )

        user = User(
            id=uuid.uuid4(),
            username=request.username,
            email=str(request.email),
            password_hash=hash_password(request.password),
            role="user",
            created_at=datetime.utcnow(),
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info("用户注册成功：username=%s", request.username)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=success_response(
                data={
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
                message="注册成功",
            ),
        )

    except Exception:
        logger.error("注册失败", exc_info=True)
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response("注册失败，请稍后重试", status.HTTP_500_INTERNAL_SERVER_ERROR),
        )


@router.post("/refresh", summary="刷新 Token")
async def refresh_token(request: RefreshTokenRequest) -> JSONResponse:
    """刷新访问令牌。

    Args:
        request: 刷新令牌请求体

    Returns:
        JSONResponse: 包含新 token 的响应

    Raises:
        RuntimeError: Token 处理失败时抛出
    """
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("refresh_token 无效或已过期", status.HTTP_401_UNAUTHORIZED),
            )

        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("refresh_token 无效或已过期", status.HTTP_401_UNAUTHORIZED),
            )

        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=settings.access_token_expire_hours),
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                },
                message="Token 刷新成功",
            ),
        )

    except Exception:
        logger.error("刷新 token 失败", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response("刷新 token 失败，请稍后重试", status.HTTP_500_INTERNAL_SERVER_ERROR),
        )


@router.get("/me", summary="获取当前用户信息")
async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """获取当前登录用户信息。

    Args:
        authorization: Bearer Token（格式：Bearer <token>）
        db: 数据库会话

    Returns:
        JSONResponse: 当前用户信息

    Raises:
        RuntimeError: 数据库查询失败时抛出
    """
    if authorization is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response("缺少认证头", status.HTTP_401_UNAUTHORIZED),
        )

    auth_parts = authorization.strip().split(" ", 1)
    if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer":
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response("无效的认证头格式", status.HTTP_401_UNAUTHORIZED),
        )

    token = auth_parts[1].strip()
    if not token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response("Token 不能为空", status.HTTP_401_UNAUTHORIZED),
        )

    try:
        payload = verify_token(token, token_type="access")
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("Token 无效或已过期", status.HTTP_401_UNAUTHORIZED),
            )

        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("Token 无效或已过期", status.HTTP_401_UNAUTHORIZED),
            )

        user_uuid = uuid.UUID(user_id)
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response("用户不存在", status.HTTP_404_NOT_FOUND),
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                },
                message="获取用户信息成功",
            ),
        )

    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response("Token 无效或已过期", status.HTTP_401_UNAUTHORIZED),
        )
    except Exception:
        logger.error("获取用户信息失败", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response("获取用户信息失败，请稍后重试", status.HTTP_500_INTERNAL_SERVER_ERROR),
        )
