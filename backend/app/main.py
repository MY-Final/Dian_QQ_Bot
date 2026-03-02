"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import instances
from app.core.config import settings
from app.database import close_db, init_db

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
    """Application lifespan handler.

    Args:
        app: FastAPI application instance

    """
    logger.info("Starting Dian QQ Bot...")
    logger.info(f"App: {settings.app_name}, Debug: {settings.debug}")

    await init_db()
    logger.info("Database initialized")

    yield

    logger.info("Shutting down Dian QQ Bot...")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.app_name,
    description="QQ Bot 管理平台 - 献给我的点点 🐱❤️",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSONResponse: Error response

    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {exc}"},
    )


app.include_router(instances.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        dict: Welcome message

    """
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "message": "点点在看着你呢～ 💕",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        dict: Health status

    """
    return {"status": "ok", "message": "服务运行正常"}
