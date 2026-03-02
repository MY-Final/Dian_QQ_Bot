"""Bot instance API routes."""

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
    """Create a new NapCat Bot instance.

    Args:
        data: Instance creation data

    Returns:
        InstanceResponse: Created instance details

    Raises:
        HTTPException: If creation fails

    """
    logger.info(f"API: Creating instance: name={data.name}, qq={data.qq_number}")

    try:
        instance = await napcat_manager.create(
            name=data.name,
            qq_number=data.qq_number,
            protocol=data.protocol.value,
            description=data.description,
        )
        logger.info(f"API: Instance created successfully: id={instance.id}")
        return instance

    except BotError as e:
        logger.error(f"API: Failed to create instance: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: Unexpected error creating instance: {e}", exc_info=True)
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
    """List all Bot instances.

    Returns:
        List[InstanceResponse]: List of all instances

    """
    logger.info("API: Listing all instances")

    try:
        instances = await napcat_manager.list_instances()
        logger.info(f"API: Found {len(instances)} instances")
        return instances

    except Exception as e:
        logger.error(f"API: Error listing instances: {e}", exc_info=True)
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
    """Get Bot instance details.

    Args:
        instance_id: Instance ID

    Returns:
        InstanceResponse: Instance details

    Raises:
        HTTPException: If instance not found

    """
    logger.info(f"API: Getting instance: id={instance_id}")

    try:
        status_value = await napcat_manager.get_status(instance_id)
        logger.info(f"API: Instance {instance_id} status: {status_value}")

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
        logger.error(f"API: Instance not found: {instance_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: Error getting instance: {e}", exc_info=True)
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
    """Start a Bot instance.

    Args:
        instance_id: Instance ID

    Returns:
        InstanceResponse: Updated instance details

    Raises:
        HTTPException: If instance not found or start fails

    """
    logger.info(f"API: Starting instance: id={instance_id}")

    try:
        instance = await napcat_manager.start(instance_id)
        logger.info(f"API: Instance started: id={instance_id}")
        return instance

    except BotError as e:
        logger.error(f"API: Failed to start instance: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: Unexpected error starting instance: {e}", exc_info=True)
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
    """Stop a Bot instance.

    Args:
        instance_id: Instance ID

    Returns:
        InstanceResponse: Updated instance details

    Raises:
        HTTPException: If instance not found or stop fails

    """
    logger.info(f"API: Stopping instance: id={instance_id}")

    try:
        instance = await napcat_manager.stop(instance_id)
        logger.info(f"API: Instance stopped: id={instance_id}")
        return instance

    except BotError as e:
        logger.error(f"API: Failed to stop instance: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: Unexpected error stopping instance: {e}", exc_info=True)
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
    """Restart a Bot instance.

    Args:
        instance_id: Instance ID

    Returns:
        InstanceResponse: Updated instance details

    Raises:
        HTTPException: If instance not found or restart fails

    """
    logger.info(f"API: Restarting instance: id={instance_id}")

    try:
        instance = await napcat_manager.restart(instance_id)
        logger.info(f"API: Instance restarted: id={instance_id}")
        return instance

    except BotError as e:
        logger.error(f"API: Failed to restart instance: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: Unexpected error restarting instance: {e}", exc_info=True)
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
    """Delete a Bot instance.

    Args:
        instance_id: Instance ID

    Raises:
        HTTPException: If instance not found or deletion fails

    """
    logger.info(f"API: Deleting instance: id={instance_id}")

    try:
        await napcat_manager.delete(instance_id)
        logger.info(f"API: Instance deleted: id={instance_id}")

    except BotError as e:
        logger.error(f"API: Failed to delete instance: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: Unexpected error deleting instance: {e}", exc_info=True)
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
    """Get Bot instance logs.

    Args:
        instance_id: Instance ID
        tail: Number of lines to fetch

    Returns:
        JSONResponse: Logs content

    Raises:
        HTTPException: If instance not found

    """
    logger.info(f"API: Getting logs for instance: id={instance_id}")

    try:
        logs = await napcat_manager.get_logs(instance_id, tail)
        return JSONResponse(content={"logs": logs})

    except BotError as e:
        logger.error(f"API: Failed to get logs: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e
    except Exception as e:
        logger.error(f"API: Unexpected error getting logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日志失败: {e}",
        ) from e
