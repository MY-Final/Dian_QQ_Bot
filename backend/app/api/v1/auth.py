"""认证 API 路由模块。

提供用户认证相关的接口：
- 用户登录
- 用户注册
- 刷新 token
- 获取当前用户信息
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["用户认证"])


def success_response(data: dict = None, message: str = "操作成功") -> dict:
    """生成成功响应。
    
    Args:
        data: 响应数据
        message: 成功消息
        
    Returns:
        dict: 统一格式的成功响应
    """
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: int = 400) -> dict:
    """生成错误响应。
    
    Args:
        message: 错误消息
        code: 错误代码
        
    Returns:
        dict: 统一格式的错误响应
    """
    return {"success": False, "message": message, "code": code, "data": None}


class LoginRequest:
    """登录请求模型。"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


class TokenResponse:
    """Token 响应模型。"""
    
    def __init__(self, access_token: str, refresh_token: str, token_type: str = "bearer"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type


@router.post("/login", summary="用户登录")
async def login(
    request: dict,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """用户登录接口。
    
    验证用户名和密码，返回 access_token 和 refresh_token。
    
    Args:
        request: 包含 username 和 password 的请求体
        db: 数据库会话
        
    Returns:
        JSONResponse: 包含 token 的响应
        
    Raises:
        HTTPException: 用户名或密码错误时抛出
    """
    username = request.get("username")
    password = request.get("password")
    
    if not username or not password:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response("用户名和密码不能为空"),
        )
    
    logger.info(f"用户登录尝试：username={username}")
    
    try:
        # 查询用户
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"用户不存在：{username}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("用户名或密码错误"),
            )
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            logger.warning(f"密码错误：username={username}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("用户名或密码错误"),
            )
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        # 生成 token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
            },
            expires_delta=timedelta(hours=24),
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=7),
        )
        
        logger.info(f"用户登录成功：username={username}, role={user.role}")
        
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
        
    except Exception as e:
        logger.error(f"登录失败：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(f"登录失败：{str(e)}"),
        )


@router.post("/register", summary="用户注册")
async def register(
    request: dict,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """用户注册接口。
    
    创建新用户账号（默认 role 为 user）。
    
    Args:
        request: 包含 username, email, password 的请求体
        db: 数据库会话
        
    Returns:
        JSONResponse: 注册结果
        
    Raises:
        HTTPException: 用户名已存在或创建失败时抛出
    """
    username = request.get("username")
    email = request.get("email")
    password = request.get("password")
    
    # 参数验证
    if not all([username, email, password]):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response("用户名、邮箱和密码不能为空"),
        )
    
    if len(username) < 3 or len(username) > 50:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response("用户名长度必须在 3-50 个字符之间"),
        )
    
    if len(password) < 6:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response("密码长度不能少于 6 个字符"),
        )
    
    logger.info(f"用户注册尝试：username={username}, email={email}")
    
    try:
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == username)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"用户名已存在：{username}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response("用户名已存在"),
            )
        
        # 检查邮箱是否已存在
        result = await db.execute(
            select(User).where(User.email == email)
        )
        existing_email = result.scalar_one_or_none()
        
        if existing_email:
            logger.warning(f"邮箱已存在：{email}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response("邮箱已被使用"),
            )
        
        # 创建新用户
        import uuid
        from datetime import datetime
        
        user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="user",  # 默认普通用户
            created_at=datetime.utcnow(),
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"用户注册成功：username={username}")
        
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
        
    except Exception as e:
        await db.rollback()
        logger.error(f"注册失败：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(f"注册失败：{str(e)}"),
        )


@router.post("/refresh", summary="刷新 Token")
async def refresh_token(
    request: dict,
) -> JSONResponse:
    """刷新访问令牌。
    
    使用 refresh_token 获取新的 access_token。
    
    Args:
        request: 包含 refresh_token 的请求体
        
    Returns:
        JSONResponse: 包含新 token 的响应
    """
    refresh_token = request.get("refresh_token")
    
    if not refresh_token:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response("refresh_token 不能为空"),
        )
    
    try:
        # 验证 refresh_token
        payload = verify_token(refresh_token, token_type="refresh")
        
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("refresh_token 无效或已过期"),
            )
        
        user_id = payload.get("sub")
        
        # 生成新的 access_token
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=24),
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
        
    except Exception as e:
        logger.error(f"刷新 token 失败：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(f"刷新 token 失败：{str(e)}"),
        )


@router.get("/me", summary="获取当前用户信息")
async def get_current_user(
    authorization: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """获取当前登录用户信息。
    
    Args:
        authorization: Bearer Token（格式：Bearer <token>）
        db: 数据库会话
        
    Returns:
        JSONResponse: 当前用户信息
    """
    # 解析 token
    if not authorization.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response("无效的认证头格式"),
        )
    
    token = authorization.replace("Bearer ", "", 1)
    
    try:
        # 验证 token
        payload = verify_token(token, token_type="access")
        
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response("Token 无效或已过期"),
            )
        
        user_id = payload.get("sub")
        
        # 查询用户
        import uuid
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response("用户不存在"),
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
        
    except Exception as e:
        logger.error(f"获取用户信息失败：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(f"获取用户信息失败：{str(e)}"),
        )
