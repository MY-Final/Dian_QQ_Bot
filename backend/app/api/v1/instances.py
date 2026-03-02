"""Bot 实例 API 路由模块。

提供 Bot 实例的 CRUD 接口：
- 创建/删除实例
- 启动/停止/重启实例
- 获取实例列表和详情
- 获取实例日志
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.exceptions import BotError
from app.managers.napcat import NapCatManager
from app.models.instance import InstanceCreate, InstanceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/instances", tags=["Bot Instances"])

napcat_manager = NapCatManager()


@router.post(
    "/",
    response_model=InstanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建 Bot 实例",
    description="创建一个新的 NapCat Bot 实例",
)
async def create_instance(data: InstanceCreate) -> InstanceResponse:
    """创建新的 NapCat Bot 实例。

    Args:
        data: 实例创建数据

    Returns:
        InstanceResponse: 创建的实例详情

    Raises:
        HTTPException: 如果创建失败

    """
    logger.info(f"API: 正在创建实例: name={data.name}, qq={data.qq_number}")

    try:
        instance = await napcat_manager.create(
            name=data.name,
            qq_number=data.qq_number,
            protocol=data.protocol.value,
            description=data.description,
        )
        logger.info(f"API: 实例创建成功: id={instance.id}")
        return instance

    except BotError as e:
        logger.error(f"API: 创建实例失败: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: 创建实例时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {e}",
        ) from e


@router.get(
    "/",
    response_model=List[InstanceResponse],
    summary="列出所有实例",
    description="获取所有 Bot 实例列表",
)
async def list_instances() -> List[InstanceResponse]:
    """列出所有 Bot 实例。

    Returns:
        List[InstanceResponse]: 所有实例列表

    """
    logger.info("API: 正在列出所有实例")

    try:
        instances = await napcat_manager.list_instances()
        logger.info(f"API: 找到 {len(instances)} 个实例")
        return instances

    except Exception as e:
        logger.error(f"API: 列出实例失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实例列表失败: {e}",
        ) from e


@router.get(
    "/{instance_id}",
    response_model=InstanceResponse,
    summary="获取实例详情",
    description="获取指定 Bot 实例的详细信息",
)
async def get_instance(instance_id: str) -> InstanceResponse:
    """获取 Bot 实例详情。

    Args:
        instance_id: 实例 ID

    Returns:
        InstanceResponse: 实例详情

    Raises:
        HTTPException: 如果实例未找到

    """
    logger.info(f"API: 正在获取实例: id={instance_id}")

    try:
        status_value = await napcat_manager.get_status(instance_id)
        logger.info(f"API: 实例 {instance_id} 状态: {status_value}")

        return InstanceResponse(
            id=instance_id,
            name="temp",
            qq_number="0",
            protocol=napcat_manager.__class__.__name__,
            status=status_value,
            container_name=f"dian-napcat-{instance_id}",
            port=30000,
            volume_path=f"./data/instances/{instance_id}/napcat/",
            description=None,
        )

    except BotError as e:
        logger.error(f"API: 实例未找到: {instance_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: 获取实例失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实例详情失败: {e}",
        ) from e


@router.post(
    "/{instance_id}/start",
    response_model=InstanceResponse,
    summary="启动实例",
    description="启动指定的 Bot 实例",
)
async def start_instance(instance_id: str) -> InstanceResponse:
    """启动 Bot 实例。

    Args:
        instance_id: 实例 ID

    Returns:
        InstanceResponse: 更新后的实例详情

    Raises:
        HTTPException: 如果实例未找到或启动失败

    """
    logger.info(f"API: 正在启动实例: id={instance_id}")

    try:
        instance = await napcat_manager.start(instance_id)
        logger.info(f"API: 实例已启动: id={instance_id}")
        return instance

    except BotError as e:
        logger.error(f"API: 启动实例失败: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: 启动实例时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动实例失败: {e}",
        ) from e


@router.post(
    "/{instance_id}/stop",
    response_model=InstanceResponse,
    summary="停止实例",
    description="停止指定的 Bot 实例",
)
async def stop_instance(instance_id: str) -> InstanceResponse:
    """停止 Bot 实例。

    Args:
        instance_id: 实例 ID

    Returns:
        InstanceResponse: 更新后的实例详情

    Raises:
        HTTPException: 如果实例未找到或停止失败

    """
    logger.info(f"API: 正在停止实例: id={instance_id}")

    try:
        instance = await napcat_manager.stop(instance_id)
        logger.info(f"API: 实例已停止: id={instance_id}")
        return instance

    except BotError as e:
        logger.error(f"API: 停止实例失败: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: 停止实例时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止实例失败: {e}",
        ) from e


@router.post(
    "/{instance_id}/restart",
    response_model=InstanceResponse,
    summary="重启实例",
    description="重启指定的 Bot 实例",
)
async def restart_instance(instance_id: str) -> InstanceResponse:
    """重启 Bot 实例。

    Args:
        instance_id: 实例 ID

    Returns:
        InstanceResponse: 更新后的实例详情

    Raises:
        HTTPException: 如果实例未找到或重启失败

    """
    logger.info(f"API: 正在重启实例: id={instance_id}")

    try:
        instance = await napcat_manager.restart(instance_id)
        logger.info(f"API: 实例已重启: id={instance_id}")
        return instance

    except BotError as e:
        logger.error(f"API: 重启实例失败: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: 重启实例时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重启实例失败: {e}",
        ) from e


@router.delete(
    "/{instance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除实例",
    description="删除指定的 Bot 实例",
)
async def delete_instance(instance_id: str) -> None:
    """删除 Bot 实例。

    Args:
        instance_id: 实例 ID

    Raises:
        HTTPException: 如果实例未找到或删除失败

    """
    logger.info(f"API: 正在删除实例: id={instance_id}")

    try:
        await napcat_manager.delete(instance_id)
        logger.info(f"API: 实例已删除: id={instance_id}")

    except BotError as e:
        logger.error(f"API: 删除实例失败: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: 删除实例时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除实例失败: {e}",
        ) from e


@router.get(
    "/{instance_id}/logs",
    summary="获取实例日志",
    description="获取指定 Bot 实例的容器日志",
)
async def get_instance_logs(instance_id: str, tail: int = 100) -> JSONResponse:
    """获取 Bot 实例日志。

    Args:
        instance_id: 实例 ID
        tail: 获取的日志行数

    Returns:
        JSONResponse: 日志内容

    Raises:
        HTTPException: 如果实例未找到

    """
    logger.info(f"API: 正在获取实例日志: id={instance_id}")

    try:
        logs = await napcat_manager.get_logs(instance_id, tail)
        return JSONResponse(content={"logs": logs})

    except BotError as e:
        logger.error(f"API: 获取日志失败: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: 获取日志时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日志失败: {e}",
        ) from e
