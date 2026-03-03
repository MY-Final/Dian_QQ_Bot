"""系统初始化 API 路由模块。

提供系统初始化相关的接口，包括：
- 检查初始化状态
- 测试数据库连接
- 初始化数据库表
- 创建管理员账号
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import insert, literal_column, table, column, String, DateTime, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.database import Base, get_db, set_db_config
from app.models.user import User
from app.models.settings import SystemSetting
from app.utils.security import hash_password
from app.core.db_config_manager import DatabaseConfig as AppConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/setup", tags=["系统初始化"])


def success_response(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
    """生成成功响应。"""
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: int = 400) -> Dict[str, Any]:
    """生成错误响应。"""
    return {"success": False, "message": message, "code": code, "data": None}


class DatabaseConfig(BaseModel):
    """数据库配置请求模型。"""

    host: str = Field(..., description="数据库主机地址")
    port: int = Field(default=5432, ge=1, le=65535, description="数据库端口")
    database: str = Field(..., description="数据库名称")
    username: str = Field(..., description="数据库用户名")
    password: str = Field(..., description="数据库密码")


class AdminCreateRequest(BaseModel):
    """管理员创建请求模型。"""

    username: str = Field(..., min_length=3, max_length=50, description="管理员用户名")
    email: str = Field(..., description="管理员邮箱")
    password: str = Field(..., min_length=8, description="登录密码")
    confirm_password: str = Field(..., description="确认密码")


class CreateAdminRequest(BaseModel):
    """创建管理员请求模型。"""

    admin: AdminCreateRequest = Field(..., description="管理员信息")
    database: DatabaseConfig = Field(..., description="数据库配置")


@router.get("/status", summary="检查系统初始化状态")
async def get_setup_status(
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> JSONResponse:
    """检查系统初始化状态。

    优先级：
    1. 如果提供了参数，使用提供的配置（用于 Setup 向导中）
    2. 否则使用已保存的配置（db_config.json）

    Args:
        host: 数据库主机（可选）
        port: 数据库端口（可选）
        database: 数据库名称（可选）
        username: 数据库用户名（可选）
        password: 数据库密码（可选）

    Returns:
        JSONResponse: 初始化状态信息
    """
    logger.info(f"检查系统初始化状态")

    try:
        # 如果提供了参数，使用提供的配置
        if all([host, port, database, username, password]):
            database_url = (
                f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
            )
            logger.info(f"使用提供的配置：{host}:{port}/{database}")
        else:
            # 使用已保存的配置
            saved_config = AppConfig.load()

            if not saved_config:
                # 没有保存的配置，返回未初始化
                logger.info("数据库配置文件不存在，系统未初始化")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=success_response(
                        data={"initialized": False},
                        message="系统未初始化",
                    ),
                )

            database_url = saved_config.database_url
            logger.info(
                f"使用已保存的配置：{saved_config.host}:{saved_config.port}/{saved_config.database}"
            )

        # 创建临时引擎
        temp_engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
        )

        # 检查是否已初始化
        async with temp_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT value FROM system_settings WHERE key = 'initialized'")
            )
            row = result.first()
            is_initialized = row is not None and row[0] == "true"

        # 关闭引擎
        await temp_engine.dispose()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={"initialized": is_initialized},
                message="系统已初始化" if is_initialized else "系统未初始化",
            ),
        )
    except Exception as e:
        # 如果查询失败，说明表还没创建，返回未初始化
        logger.warning(f"检查初始化状态失败（可能表未创建）: {e}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={"initialized": False},
                message="系统未初始化",
            ),
        )


@router.post("/test-db-connection", summary="测试数据库连接")
async def test_db_connection(config: DatabaseConfig) -> JSONResponse:
    """测试 PostgreSQL 数据库连接。

    Args:
        config: 数据库配置信息

    Returns:
        JSONResponse: 连接测试结果
    """
    logger.info(f"测试数据库连接：{config.host}:{config.port}/{config.database}")

    try:
        # 构建数据库 URL
        database_url = f"postgresql+asyncpg://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"

        # 创建临时引擎测试连接
        temp_engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )

        # 尝试连接
        async with temp_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        # 关闭引擎
        await temp_engine.dispose()

        logger.info(
            f"数据库连接测试成功：{config.host}:{config.port}/{config.database}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={"connected": True},
                message="数据库连接成功",
            ),
        )

    except Exception as e:
        logger.error(f"数据库连接测试失败：{e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(message=f"数据库连接失败：{str(e)}"),
        )


@router.post("/initialize-db", summary="初始化数据库表")
async def initialize_db(
    config: DatabaseConfig, db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """初始化数据库表结构。

    Args:
        config: 数据库配置信息

    Returns:
        JSONResponse: 初始化结果
    """
    logger.info("开始初始化数据库表")

    try:
        # 构建数据库 URL
        database_url = f"postgresql+asyncpg://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"

        # 创建临时引擎
        temp_engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
        )

        # 创建所有表
        async with temp_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 关闭引擎
        await temp_engine.dispose()

        logger.info("数据库表初始化成功")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={"initialized": True},
                message="数据库表创建成功",
            ),
        )

    except Exception as e:
        logger.error(f"数据库表初始化失败：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"数据库表创建失败：{str(e)}"),
        )


@router.post("/create-admin", summary="创建管理员账号")
async def create_admin(
    request: CreateAdminRequest,
) -> JSONResponse:
    """创建系统管理员账号。

    Args:
        request: 创建管理员请求

    Returns:
        JSONResponse: 创建结果
    """
    logger.info(f"创建管理员账号：{request.admin.username}")

    try:
        # 使用用户提供的数据库配置创建临时引擎
        database_url = f"postgresql+asyncpg://{request.database.username}:{request.database.password}@{request.database.host}:{request.database.port}/{request.database.database}"

        temp_engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
        )

        # 创建会话并插入数据
        async with temp_engine.begin() as conn:
            # 创建 users 表的临时表对象
            users_table = table(
                "users",
                column("id", String),
                column("username", String),
                column("email", String),
                column("password_hash", String),
                column("role", String),
                column("created_at", DateTime),
            )

            # 生成 UUID
            user_id = str(uuid.uuid4())

            # 哈希密码
            password_hash = hash_password(request.admin.password)

            # 检查用户是否已存在
            result = await conn.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": request.admin.username},
            )
            existing_user = result.first()

            if existing_user:
                # 更新现有用户
                await conn.execute(
                    text("""
                        UPDATE users SET 
                            email = :email,
                            password_hash = :password_hash,
                            role = :role,
                            last_login = NULL
                        WHERE username = :username
                    """),
                    {
                        "username": request.admin.username,
                        "email": request.admin.email,
                        "password_hash": password_hash,
                        "role": "admin",
                    },
                )
            else:
                # 插入用户数据（使用 literal_column 进行 UUID 类型转换）
                await conn.execute(
                    insert(users_table).values(
                        id=literal_column(f"'{user_id}'::uuid"),
                        username=request.admin.username,
                        email=request.admin.email,
                        password_hash=password_hash,
                        role="admin",
                        created_at=datetime.utcnow(),
                    )
                )

            # 插入初始化标记
            settings_table = table(
                "system_settings",
                column("key", String),
                column("value", String),
                column("description", String),
                column("updated_at", DateTime),
            )

            await conn.execute(
                insert(settings_table).values(
                    key="initialized",
                    value="true",
                    description="系统初始化完成标志",
                    updated_at=datetime.utcnow(),
                )
            )

            # 关闭引擎
            await temp_engine.dispose()

        # 保存数据库配置到本地文件
        app_db_config = AppConfig(
            host=request.database.host,
            port=request.database.port,
            database=request.database.database,
            username=request.database.username,
            password=request.database.password,
        )
        app_db_config.save()

        # 重新初始化全局数据库配置
        set_db_config(app_db_config)

        logger.info(f"管理员账号创建成功：{request.admin.username}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={"initialized": True, "username": request.admin.username},
                message="管理员创建成功，系统初始化完成",
            ),
        )

    except Exception as e:
        logger.error(f"创建管理员失败：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"创建管理员失败：{str(e)}"),
        )
