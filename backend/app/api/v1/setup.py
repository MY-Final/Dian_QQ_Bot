"""系统初始化 API 路由模块。"""

import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.exceptions import (
    AdminCreationError,
    DatabaseConnectionError,
    DatabaseInitializationError,
    SetupError,
)
from app.services.setup_service import SetupService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/setup", tags=["系统初始化"])


def success_response(data: object = None, message: str = "操作成功") -> dict[str, object]:
    """生成成功响应。

    Args:
        data: 响应数据
        message: 成功提示

    Returns:
        dict[str, object]: 统一响应
    """
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: int = 400) -> dict[str, object]:
    """生成错误响应。

    Args:
        message: 错误提示
        code: 错误码

    Returns:
        dict[str, object]: 统一响应
    """
    return {"success": False, "message": message, "code": code, "data": None}


def get_setup_service() -> SetupService:
    """获取初始化服务。

    Returns:
        SetupService: 初始化业务服务
    """
    return SetupService()


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
    service: SetupService = Depends(get_setup_service),
) -> JSONResponse:
    """检查系统初始化状态。

    Args:
        host: 数据库主机（可选）
        port: 数据库端口（可选）
        database: 数据库名称（可选）
        username: 数据库用户名（可选）
        password: 数据库密码（可选）
        service: 初始化业务服务

    Returns:
        JSONResponse: 初始化状态信息

    Raises:
        SetupError: 初始化状态检查失败时抛出
    """
    try:
        setup_status = await service.get_setup_status(host, port, database, username, password)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={"initialized": setup_status.initialized},
                message="系统已初始化" if setup_status.initialized else "系统未初始化",
            ),
        )
    except SetupError as exc:
        logger.error("检查初始化状态失败: %s", exc.message, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR),
        )


@router.post("/test-db-connection", summary="测试数据库连接")
async def test_db_connection(
    config: DatabaseConfig,
    service: SetupService = Depends(get_setup_service),
) -> JSONResponse:
    """测试 PostgreSQL 数据库连接。

    Args:
        config: 数据库配置信息
        service: 初始化业务服务

    Returns:
        JSONResponse: 连接测试结果

    Raises:
        DatabaseConnectionError: 连接失败时抛出
    """
    logger.info("测试数据库连接：%s:%s/%s", config.host, config.port, config.database)
    try:
        await service.test_database_connection(
            host=config.host,
            port=config.port,
            database=config.database,
            username=config.username,
            password=config.password,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(data={"connected": True}, message="数据库连接成功"),
        )
    except DatabaseConnectionError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.post("/initialize-db", summary="初始化数据库表")
async def initialize_db(
    config: DatabaseConfig,
    service: SetupService = Depends(get_setup_service),
) -> JSONResponse:
    """初始化数据库表结构。

    Args:
        config: 数据库配置信息
        service: 初始化业务服务

    Returns:
        JSONResponse: 初始化结果

    Raises:
        DatabaseInitializationError: 初始化失败时抛出
    """
    logger.info("开始初始化数据库表")
    try:
        await service.initialize_database(
            host=config.host,
            port=config.port,
            database=config.database,
            username=config.username,
            password=config.password,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(data={"initialized": True}, message="数据库表创建成功"),
        )
    except DatabaseInitializationError as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR),
        )


@router.post("/create-admin", summary="创建管理员账号")
async def create_admin(
    request: CreateAdminRequest,
    service: SetupService = Depends(get_setup_service),
) -> JSONResponse:
    """创建系统管理员账号。

    Args:
        request: 创建管理员请求
        service: 初始化业务服务

    Returns:
        JSONResponse: 创建结果

    Raises:
        AdminCreationError: 管理员创建失败时抛出
        SetupError: 配置保存失败时抛出
    """
    logger.info("创建管理员账号：%s", request.admin.username)
    try:
        await service.create_admin(
            admin_username=request.admin.username,
            admin_email=request.admin.email,
            admin_password=request.admin.password,
            confirm_password=request.admin.confirm_password,
            host=request.database.host,
            port=request.database.port,
            database=request.database.database,
            username=request.database.username,
            password=request.database.password,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(
                data={"initialized": True, "username": request.admin.username},
                message="管理员创建成功，系统初始化完成",
            ),
        )
    except AdminCreationError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )
    except SetupError as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR),
        )
