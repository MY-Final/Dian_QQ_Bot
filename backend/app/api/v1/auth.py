"""认证 API 路由模块。

提供用户认证相关的接口：
- 用户登录
- 用户注册
- 刷新 token
- 获取当前用户信息
"""

import logging

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthUserNotFoundError,
    InvalidCredentialsError,
    TokenValidationError,
    UserAlreadyExistsError,
)
from app.database import get_db
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["用户认证"])


def get_auth_service() -> AuthService:
    """获取认证服务实例。

    Returns:
        AuthService: 认证业务服务
    """
    return AuthService()


def success_response(data: dict[str, object] | None = None, message: str = "操作成功") -> dict[str, object]:
    """生成成功响应。

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        dict[str, object]: 统一格式的成功响应
    """
    result: dict[str, object] = {"success": True, "message": message, "data": data}
    return result


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
    service: AuthService = Depends(get_auth_service),
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
        login_payload = await service.login(db, request.username, request.password)
        logger.info("用户登录成功：username=%s", request.username)

        # Create response with explicit object type
        response_data: dict[str, object] = {
            "access_token": login_payload["access_token"],
            "refresh_token": login_payload["refresh_token"],
            "token_type": login_payload["token_type"],
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data=response_data,
                message="登录成功",
            ),
        )
    except InvalidCredentialsError as exc:
        logger.warning("登录失败：username=%s", request.username)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response(exc.message, status.HTTP_401_UNAUTHORIZED),
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
    service: AuthService = Depends(get_auth_service),
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
        registered_user = await service.register(
            db=db,
            username=request.username,
            email=str(request.email),
            password=request.password,
        )

        logger.info("用户注册成功：username=%s", request.username)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=success_response(
                data=registered_user,
                message="注册成功",
            ),
        )
    except UserAlreadyExistsError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )

    except Exception:
        logger.error("注册失败", exc_info=True)
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response("注册失败，请稍后重试", status.HTTP_500_INTERNAL_SERVER_ERROR),
        )


@router.post("/refresh", summary="刷新 Token")
async def refresh_token(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> JSONResponse:
    """刷新访问令牌。

    Args:
        request: 刷新令牌请求体

    Returns:
        JSONResponse: 包含新 token 的响应

    Raises:
        RuntimeError: Token 处理失败时抛出
    """
    try:
        access_token_data = service.refresh_access_token(request.refresh_token)

        # Convert to dict[str, object] for type compatibility
        response_data: dict[str, object] = {
            k: v for k, v in access_token_data.items()
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data=response_data,
                message="Token 刷新成功",
            ),
        )
    except TokenValidationError as exc:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response(exc.message, status.HTTP_401_UNAUTHORIZED),
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
    service: AuthService = Depends(get_auth_service),
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
    try:
        user_profile = await service.get_current_user_profile(db, authorization)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data=user_profile,
                message="获取用户信息成功",
            ),
        )
    except TokenValidationError as exc:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response(exc.message, status.HTTP_401_UNAUTHORIZED),
        )
    except AuthUserNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message, status.HTTP_404_NOT_FOUND),
        )
    except Exception:
        logger.error("获取用户信息失败", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response("获取用户信息失败，请稍后重试", status.HTTP_500_INTERNAL_SERVER_ERROR),
        )
