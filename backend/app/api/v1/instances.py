"""Bot 实例 API 路由模块。

提供 Bot 实例的 CRUD 接口：
- 创建/删除实例
- 启动/停止/重启实例
- 获取实例列表和详情
- 获取实例日志
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.v1.dependencies import get_current_user
from app.core.exceptions import BotError, BotNotFoundError
from app.managers.napcat import NapCatManager
from app.models.instance import InstanceCreate, InstanceImageUpdate
from app.models.user import User
from app.services.image_service import ImageService
from app.services.instance_service import InstanceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/instances", tags=["Bot Instances"])


def get_instance_service() -> InstanceService:
    """获取实例服务。

    Returns:
        InstanceService: 实例服务对象
    """
    manager = NapCatManager()
    image_service = ImageService()
    return InstanceService(manager=manager, image_service=image_service)


def success_response(data: Any = None, message: str = "操作成功") -> dict[str, Any]:
    """生成成功响应。

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        dict[str, Any]: 统一格式成功响应
    """
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: int = 400) -> dict[str, Any]:
    """生成错误响应。

    Args:
        message: 错误消息
        code: 错误代码

    Returns:
        dict[str, Any]: 统一格式错误响应
    """
    return {"success": False, "message": message, "code": code, "data": None}


@router.post(
    "/",
    summary="创建 Bot 实例",
    description="创建一个新的 NapCat Bot 实例",
)
async def create_instance(
    data: InstanceCreate,
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """创建新的 NapCat Bot 实例。

    Args:
        data: 实例创建数据
        service: 实例业务服务

    Returns:
        JSONResponse: 包含创建结果的统一格式响应

    Raises:
        BotError: 创建失败时抛出
    """
    logger.info("API: 正在创建实例: name=%s, qq=%s", data.name, data.qq_number)

    try:
        instance_data = await service.create_instance(data)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=success_response(data=instance_data, message="实例创建成功"),
        )
    except BotError as exc:
        logger.error("API: 创建实例失败: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.get(
    "/",
    summary="列出所有实例",
    description="获取所有 Bot 实例列表",
)
async def list_instances(
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """列出所有 Bot 实例。

    Args:
        service: 实例业务服务

    Returns:
        JSONResponse: 包含实例列表的统一格式响应

    Raises:
        BotError: 查询失败时抛出
    """
    try:
        instances = await service.list_instances()
        return JSONResponse(
            content=success_response(data=instances, message=f"找到 {len(instances)} 个实例")
        )
    except BotError as exc:
        logger.error("API: 列出实例失败: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR),
        )


@router.get(
    "/{instance_id}",
    summary="获取实例详情",
    description="获取指定 Bot 实例的详细信息",
)
async def get_instance(
    instance_id: str,
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """获取 Bot 实例详情。

    Args:
        instance_id: 实例 ID
        service: 实例业务服务

    Returns:
        JSONResponse: 包含实例详情的统一格式响应

    Raises:
        BotNotFoundError: 实例不存在时抛出
        BotError: 查询失败时抛出
    """
    try:
        instance_data = await service.get_instance(instance_id)
        return JSONResponse(content=success_response(data=instance_data, message="获取实例详情成功"))
    except BotNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message, status.HTTP_404_NOT_FOUND),
        )
    except BotError as exc:
        logger.error("API: 获取实例失败: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR),
        )


@router.post(
    "/{instance_id}/start",
    summary="启动实例",
    description="启动指定的 Bot 实例",
)
async def start_instance(
    instance_id: str,
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """启动 Bot 实例。

    Args:
        instance_id: 实例 ID
        service: 实例业务服务

    Returns:
        JSONResponse: 包含启动结果的统一格式响应

    Raises:
        BotNotFoundError: 实例不存在时抛出
        BotError: 启动失败时抛出
    """
    try:
        instance_data = await service.start_instance(instance_id)
        return JSONResponse(content=success_response(data=instance_data, message="实例启动成功"))
    except BotNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message, status.HTTP_404_NOT_FOUND),
        )
    except BotError as exc:
        logger.error("API: 启动实例失败: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.post(
    "/{instance_id}/stop",
    summary="停止实例",
    description="停止指定的 Bot 实例",
)
async def stop_instance(
    instance_id: str,
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """停止 Bot 实例。

    Args:
        instance_id: 实例 ID
        service: 实例业务服务

    Returns:
        JSONResponse: 包含停止结果的统一格式响应

    Raises:
        BotNotFoundError: 实例不存在时抛出
        BotError: 停止失败时抛出
    """
    try:
        instance_data = await service.stop_instance(instance_id)
        return JSONResponse(content=success_response(data=instance_data, message="实例停止成功"))
    except BotNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message, status.HTTP_404_NOT_FOUND),
        )
    except BotError as exc:
        logger.error("API: 停止实例失败: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.post(
    "/{instance_id}/restart",
    summary="重启实例",
    description="重启指定的 Bot 实例",
)
async def restart_instance(
    instance_id: str,
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """重启 Bot 实例。

    Args:
        instance_id: 实例 ID
        service: 实例业务服务

    Returns:
        JSONResponse: 包含重启结果的统一格式响应

    Raises:
        BotNotFoundError: 实例不存在时抛出
        BotError: 重启失败时抛出
    """
    try:
        instance_data = await service.restart_instance(instance_id)
        return JSONResponse(content=success_response(data=instance_data, message="实例重启成功"))
    except BotNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message, status.HTTP_404_NOT_FOUND),
        )
    except BotError as exc:
        logger.error("API: 重启实例失败: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.delete(
    "/{instance_id}",
    summary="删除实例",
    description="删除指定的 Bot 实例",
)
async def delete_instance(
    instance_id: str,
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """删除 Bot 实例。

    Args:
        instance_id: 实例 ID
        service: 实例业务服务

    Returns:
        JSONResponse: 包含删除结果的统一格式响应

    Raises:
        BotNotFoundError: 实例不存在时抛出
        BotError: 删除失败时抛出
    """
    try:
        await service.delete_instance(instance_id)
        return JSONResponse(
            content=success_response(data={"id": instance_id}, message="实例删除成功")
        )
    except BotNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message, status.HTTP_404_NOT_FOUND),
        )
    except BotError as exc:
        logger.error("API: 删除实例失败: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.patch(
    "/{instance_id}/image",
    summary="更新实例镜像",
    description="更新实例镜像仓库与版本",
)
async def update_instance_image(
    instance_id: str,
    payload: InstanceImageUpdate,
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """更新实例镜像信息。"""
    try:
        updated_instance = await service.update_instance_image(
            instance_id=instance_id,
            image_registry=payload.image_registry,
            image_repo=payload.image_repo,
            image_tag=payload.image_tag,
            auto_pull=payload.auto_pull,
        )
        return JSONResponse(content=success_response(data=updated_instance, message="镜像更新成功"))
    except BotNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message, status.HTTP_404_NOT_FOUND),
        )
    except BotError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.post(
    "/{instance_id}/recreate",
    summary="按镜像重建实例",
    description="使用当前实例镜像版本重新创建容器",
)
async def recreate_instance(
    instance_id: str,
    auto_pull: bool = False,
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """按实例镜像重建容器。"""
    try:
        recreated_instance = await service.recreate_instance_with_image(
            instance_id=instance_id,
            auto_pull=auto_pull,
        )
        return JSONResponse(content=success_response(data=recreated_instance, message="实例重建成功"))
    except BotNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message, status.HTTP_404_NOT_FOUND),
        )
    except BotError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.get(
    "/{instance_id}/logs",
    summary="获取实例日志",
    description="获取指定 Bot 实例的容器日志",
)
async def get_instance_logs(
    instance_id: str,
    tail: int = 100,
    cursor: int = 0,
    service: InstanceService = Depends(get_instance_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """获取 Bot 实例日志。

    Args:
        instance_id: 实例 ID
        tail: 获取的日志行数
        cursor: 日志游标（行偏移）
        service: 实例业务服务

    Returns:
        JSONResponse: 包含日志内容的统一格式响应

    Raises:
        BotNotFoundError: 实例不存在时抛出
        BotError: 日志获取失败时抛出
    """
    try:
        logs_data = await service.get_instance_logs(instance_id, tail, cursor)
        return JSONResponse(
            content=success_response(
                data=logs_data,
                message="日志获取成功",
            )
        )
    except BotNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message, status.HTTP_404_NOT_FOUND),
        )
    except BotError as exc:
        logger.error("API: 获取日志失败: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )
