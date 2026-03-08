"""FastAPI 应用入口模块。

应用主入口，配置中间件、路由和生命周期管理。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import instances
from app.api.v1 import system
from app.api.v1 import setup  # 新增：系统初始化路由
from app.api.v1 import auth  # 新增：认证路由
from app.core.config import settings
from app.database import close_db, init_db

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期处理器。

    在应用启动时初始化数据库，
    在应用关闭时关闭数据库连接。

    Args:
        app: FastAPI 应用实例
    """
    logger.info("启动 Dian QQ Bot...")
    logger.info(f"应用: {settings.app_name}, 调试模式: {settings.debug}")

    await init_db()
    logger.info("数据库初始化完成")

    yield

    logger.info("关闭 Dian QQ Bot...")
    await close_db()
    logger.info("数据库连接已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description="QQ Bot 管理平台 - 献给我的点点 🐱❤️",
    version="0.1.0",
    lifespan=lifespan,
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理器。

    捕获所有未处理的异常并返回友好的错误信息。

    Args:
        request: FastAPI 请求对象
        exc: 异常对象

    Returns:
        JSONResponse: 错误响应
    """
    logger.error(
        f"未处理的异常: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试。点点会陪你排查的～"},
    )


# 注册路由
app.include_router(instances.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(setup.router, prefix="/api/v1")  # 系统初始化路由
app.include_router(auth.router, prefix="/api/v1")  # 认证路由


@app.get("/")
async def root():
    """根路径接口。

    Returns:
        dict: 欢迎信息
    """
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "message": "点点在看着你呢～ 💕",
    }


@app.get("/health")
async def health_check():
    """健康检查接口。

    Returns:
        dict: 服务状态
    """
    return {"status": "ok", "message": "服务运行正常"}
