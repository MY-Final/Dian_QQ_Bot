"""系统 API 路由模块。

提供系统级别的接口，包括：
- Docker 状态检查
- 数据库状态检查
- 健康检查
- 系统初始化状态检查
"""

import logging
from typing import Any
from urllib.parse import quote_plus

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.db_config_manager import DatabaseConfig as AppConfig
from app.database import get_engine
from app.models.instance import DatabaseConfig, SystemInitializeRequest
from app.utils.docker_utils import check_docker_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["系统管理"])


def success_response(data: Any = None, message: str = "操作成功") -> dict[str, Any]:
    """生成成功响应。

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        dict[str, Any]: 统一格式响应
    """
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: int = 400) -> dict[str, Any]:
    """生成错误响应。

    Args:
        message: 错误消息
        code: 错误码

    Returns:
        dict[str, Any]: 统一格式错误响应
    """
    return {"success": False, "message": message, "code": code, "data": None}


async def _is_initialized(database_url: str) -> bool:
    """检查数据库中的初始化状态。

    Args:
        database_url: 数据库连接 URL

    Returns:
        bool: 是否已初始化
    """
    temp_engine = create_async_engine(database_url, echo=False, future=True)
    try:
        async with temp_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT value FROM system_settings WHERE key = 'initialized'")
            )
            row = result.first()
            return row is not None and row[0] == "true"
    finally:
        await temp_engine.dispose()


@router.get(
    "/init",
    summary="检查系统初始化状态",
    description="检查系统是否已完成初始化配置",
)
async def check_init() -> JSONResponse:
    """检查系统初始化状态。

    Returns:
        JSONResponse: 初始化状态信息

    Raises:
        RuntimeError: 数据库状态检查失败时抛出
    """
    logger.info("检查系统初始化状态")

    app_config = AppConfig.load()
    if app_config is None:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={"initialized": False},
                message="系统未初始化",
            ),
        )

    try:
        is_initialized = await _is_initialized(app_config.database_url)
    except Exception:
        logger.warning("初始化状态检查失败", exc_info=True)
        is_initialized = False

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=success_response(
            data={"initialized": is_initialized},
            message="系统已初始化" if is_initialized else "系统未初始化",
        ),
    )


@router.post(
    "/test-database",
    summary="测试数据库连接",
    description="测试指定的数据库配置是否可连接",
)
async def test_database(config: DatabaseConfig) -> JSONResponse:
    """测试数据库连接。

    Args:
        config: 数据库配置信息

    Returns:
        JSONResponse: 连接测试结果

    Raises:
        RuntimeError: 数据库连接失败时抛出
    """
    logger.info("测试数据库连接：%s:%s/%s", config.host, config.port, config.database)

    encoded_username = quote_plus(config.username)
    encoded_password = quote_plus(config.password)
    database_url = (
        f"postgresql+asyncpg://{encoded_username}:{encoded_password}@"
        f"{config.host}:{config.port}/{config.database}"
    )
    temp_engine = create_async_engine(database_url, echo=False, future=True, pool_pre_ping=True)

    try:
        async with temp_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(data={"connected": True}, message="数据库连接成功"),
        )
    except Exception as exc:
        logger.error("数据库连接测试失败：%s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response("数据库连接失败，请检查配置", status.HTTP_400_BAD_REQUEST),
        )
    finally:
        await temp_engine.dispose()


@router.post(
    "/initialize",
    summary="系统初始化",
    description="该接口已废弃，请使用 /setup 下的初始化流程接口",
)
async def initialize_system(_request: SystemInitializeRequest) -> JSONResponse:
    """系统初始化入口（废弃）。

    Args:
        _request: 初始化请求体（保留兼容）

    Returns:
        JSONResponse: 错误提示
    """
    logger.warning("调用了已废弃的 /system/initialize 接口")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response(
            message="请使用 /api/v1/setup/status、/initialize-db、/create-admin 完成初始化",
            code=status.HTTP_400_BAD_REQUEST,
        ),
    )


@router.get(
    "/docker",
    summary="Docker 状态检查",
    description="检查 Docker 守护进程是否运行，支持 Windows 和 Linux",
)
async def docker_status() -> JSONResponse:
    """检查 Docker 守护进程状态。

    Returns:
        JSONResponse: Docker 状态信息
    """
    logger.info("检查 Docker 状态")

    result = check_docker_status()
    running = bool(result.get("running", False))
    message = str(result.get("message", "Docker 状态未知"))
    http_status = status.HTTP_200_OK if running else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content=(
            success_response(data=result, message=message)
            if running
            else error_response(message, http_status)
        ),
    )


@router.get(
    "/database",
    summary="数据库状态检查",
    description="检查 PostgreSQL 数据库连接是否正常",
)
async def database_status() -> JSONResponse:
    """检查数据库连接状态。

    Returns:
        JSONResponse: 数据库状态信息

    Raises:
        RuntimeError: 数据库连接失败时抛出
    """
    logger.info("检查数据库状态")

    try:
        async with get_engine().connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=success_response(
                    data={
                        "connected": True,
                        "database": "PostgreSQL",
                        "version": version,
                        "message": "数据库连接正常",
                    },
                    message="数据库连接正常",
                ),
            )
    except Exception as exc:
        logger.error("数据库连接失败: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response("数据库连接失败", status.HTTP_503_SERVICE_UNAVAILABLE),
        )


@router.get(
    "/ping",
    summary="健康检查",
    description="简单的服务健康检查",
)
async def ping() -> JSONResponse:
    """健康检查接口。

    Returns:
        JSONResponse: 服务状态
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=success_response(
            data={"status": "ok", "message": "点点在看着你呢～ 💕"},
            message="服务运行正常",
        ),
    )
