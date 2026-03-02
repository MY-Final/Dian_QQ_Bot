"""系统 API 路由模块。

提供系统级别的接口，包括：
- Docker 状态检查
- 数据库状态检查
- 健康检查
"""

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import engine
from app.utils.docker_utils import check_docker_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["系统管理"])


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

    return JSONResponse(
        status_code=http_status,
        content=result,
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
