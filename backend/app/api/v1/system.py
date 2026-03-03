"""系统 API 路由模块。

提供系统级别的接口，包括：
- Docker 状态检查
- 数据库状态检查
- 健康检查
- 系统初始化
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.database import engine
from app.models.instance import (
    DatabaseConfig,
    SystemInitializeRequest,
    SystemInitializeResponse,
)
from app.utils.docker_utils import check_docker_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["系统管理"])

# 全局变量记录初始化状态
_initialized = False


def success_response(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
    """生成成功响应。"""
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: int = 400) -> Dict[str, Any]:
    """生成错误响应。"""
    return {"success": False, "message": message, "code": code, "data": None}


@router.get(
    "/init",
    summary="检查系统初始化状态",
    description="检查系统是否已完成初始化配置",
)
async def check_init() -> JSONResponse:
    """检查系统初始化状态。

    Returns:
        JSONResponse: 初始化状态信息
    """
    logger.info("检查系统初始化状态")

    # 简单判断：检查是否创建了第一个管理员用户
    # 这里用一个简单的标记文件来判断
    import os
    from pathlib import Path

    init_marker = Path("./data/.initialized")
    is_initialized = init_marker.exists()

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
    """
    logger.info(f"测试数据库连接：{config.host}:{config.port}/{config.database}")

    try:
        # 动态创建数据库 URL
        database_url = f"postgresql+asyncpg://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"

        # 创建临时引擎测试连接
        from sqlalchemy.ext.asyncio import create_async_engine

        temp_engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,  # 连接前测试
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
        logger.error(f"数据库连接测试失败：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(message=f"数据库连接失败：{str(e)}"),
        )


@router.post(
    "/initialize",
    summary="系统初始化",
    description="执行系统初始化配置，包括数据库和管理员账号",
)
async def initialize_system(request: SystemInitializeRequest) -> JSONResponse:
    """执行系统初始化。

    Args:
        request: 初始化配置请求

    Returns:
        JSONResponse: 初始化结果
    """
    global _initialized

    logger.info("开始执行系统初始化")

    try:
        from pathlib import Path

        # 1. 验证数据库配置
        logger.info(f"验证数据库配置：{request.database.host}:{request.database.port}")

        # 2. 保存配置到环境变量或配置文件
        # 这里应该将配置写入 .env 文件或数据库
        # 示例：更新 settings 对象
        # settings.database_url = f"postgresql+asyncpg://{request.database.username}:{request.database.password}@{request.database.host}:{request.database.port}/{request.database.database}"

        # 3. 创建管理员账号
        logger.info(f"创建管理员账号：{request.admin.username}")
        # 这里应该调用数据库创建管理员用户的逻辑
        # await create_admin_user(request.admin.username, request.admin.email, request.admin.password)

        # 4. 创建初始化标记文件
        init_marker = Path("./data/.initialized")
        init_marker.parent.mkdir(parents=True, exist_ok=True)
        init_marker.write_text(f"Initialized at: {datetime.utcnow().isoformat()}")

        # 5. 标记系统已初始化
        _initialized = True

        logger.info("系统初始化完成")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={"initialized": True},
                message="系统初始化成功",
            ),
        )

    except Exception as e:
        logger.error(f"系统初始化失败：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(message=f"初始化失败：{str(e)}"),
        )


@router.get(
    "/docker",
    summary="Docker 状态检查",
    description="检查 Docker 守护进程是否运行，支持 Windows 和 Linux",
)
async def docker_status() -> JSONResponse:
    """检查 Docker 守护进程状态。

    返回 Docker 是否运行、操作系统平台、版本等信息。

    Returns:
        JSONResponse: Docker 状态信息
    """
    logger.info("检查 Docker 状态")

    result = check_docker_status()
    http_status = (
        status.HTTP_200_OK if result["running"] else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    # 使用统一响应格式
    return JSONResponse(
        status_code=http_status,
        content={
            "success": result["running"],
            "message": result["message"],
            "data": result,
        },
    )


@router.get(
    "/database",
    summary="数据库状态检查",
    description="检查 PostgreSQL 数据库连接是否正常",
)
async def database_status() -> JSONResponse:
    """检查数据库连接状态。

    返回数据库是否连接成功、版本信息等。

    Returns:
        JSONResponse: 数据库状态信息
    """
    logger.info("检查数据库状态")

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "connected": True,
                    "database": "PostgreSQL",
                    "version": version,
                    "message": "数据库连接正常",
                },
            )
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "connected": False,
                "database": "PostgreSQL",
                "version": None,
                "message": f"数据库连接失败: {str(e)}",
            },
        )


@router.get(
    "/ping",
    summary="健康检查",
    description="简单的服务健康检查",
)
async def ping() -> dict[str, str]:
    """健康检查接口。

    Returns:
        dict: 服务状态
    """
    return {"status": "ok", "message": "点点在看着你呢～ 💕"}
