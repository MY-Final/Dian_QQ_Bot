"""Bot 实例 API 路由模块。

提供 Bot 实例的 CRUD 接口：
- 创建/删除实例
- 启动/停止/重启实例
- 获取实例列表和详情
- 获取实例日志
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.core.exceptions import BotError
from app.database import get_session_maker
from app.managers.napcat import NapCatManager
from app.models.db_models import BotInstanceDB
from app.models.instance import (
    InstanceCreate,
    InstanceResponse,
    InstanceStatus,
    ProtocolType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/instances", tags=["Bot Instances"])

napcat_manager = NapCatManager()


def success_response(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
    """生成成功响应。

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        Dict: 统一格式的成功响应
    """
    # 处理 datetime 序列化
    if data is not None:
        data = convert_datetime_to_str(data)
    return {"success": True, "message": message, "data": data}


def convert_datetime_to_str(obj: Any) -> Any:
    """递归转换 datetime 对象为 ISO 格式字符串。

    Args:
        obj: 需要转换的对象

    Returns:
        Any: 转换后的对象
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_datetime_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_str(item) for item in obj]
    return obj


def error_response(message: str, code: int = 400) -> Dict[str, Any]:
    """生成错误响应。

    Args:
        message: 错误消息
        code: 错误代码

    Returns:
        Dict: 统一格式的错误响应
    """
    return {"success": False, "message": message, "code": code, "data": None}


@router.post(
    "/",
    summary="创建 Bot 实例",
    description="创建一个新的 NapCat Bot 实例",
)
async def create_instance(data: InstanceCreate) -> JSONResponse:
    """创建新的 NapCat Bot 实例。

    Args:
        data: 实例创建数据

    Returns:
        JSONResponse: 包含创建结果的统一格式响应

    """
    logger.info(f"API: 正在创建实例: name={data.name}, qq={data.qq_number}")

    try:
        instance = await napcat_manager.create(
            name=data.name,
            qq_number=data.qq_number,
            protocol=data.protocol.value,
            description=data.description,
            port_web_ui=data.port_web_ui,
            port_http=data.port_http,
            port_ws=data.port_ws,
            napcat_uid=data.napcat_uid,
            napcat_gid=data.napcat_gid,
        )
        logger.info(f"API: 实例创建成功: id={instance.id}")
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=success_response(
                data=instance.model_dump(), message="实例创建成功"
            ),
        )

    except BotError as e:
        logger.error(f"API: 创建实例失败: {e.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(message=e.message),
        )
    except Exception as e:
        logger.error(f"API: 创建实例时发生未知错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"服务器内部错误: {e}"),
        )


@router.get(
    "/",
    summary="列出所有实例",
    description="获取所有 Bot 实例列表",
)
async def list_instances() -> JSONResponse:
    """列出所有 Bot 实例。

    Returns:
        JSONResponse: 包含实例列表的统一格式响应

    """
    logger.info("API: 正在列出所有实例")

    try:
        # 从数据库查询所有实例
        async with get_session_maker()() as session:
            result = await session.execute(select(BotInstanceDB))
            db_instances = result.scalars().all()

            # 转换为响应模型
            instances = []
            for db_instance in db_instances:
                instances.append(
                    {
                        "id": db_instance.id,
                        "name": db_instance.name,
                        "qq_number": db_instance.qq_number,
                        "protocol": db_instance.protocol,
                        "status": db_instance.status,
                        "container_name": db_instance.container_name,
                        "port": db_instance.port,
                        "volume_path": db_instance.volume_path,
                        "description": db_instance.description,
                        "created_at": db_instance.created_at.isoformat()
                        if db_instance.created_at
                        else None,
                        "updated_at": db_instance.updated_at.isoformat()
                        if db_instance.updated_at
                        else None,
                    }
                )

            logger.info(f"API: 找到 {len(instances)} 个实例")
            return JSONResponse(
                content=success_response(
                    data=instances, message=f"找到 {len(instances)} 个实例"
                )
            )

    except Exception as e:
        logger.error(f"API: 列出实例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"获取实例列表失败: {e}"),
        )


@router.get(
    "/{instance_id}",
    summary="获取实例详情",
    description="获取指定 Bot 实例的详细信息",
)
async def get_instance(instance_id: str) -> JSONResponse:
    """获取 Bot 实例详情。

    Args:
        instance_id: 实例 ID

    Returns:
        JSONResponse: 包含实例详情的统一格式响应

    """
    logger.info(f"API: 正在获取实例: id={instance_id}")

    try:
        # 从数据库查询实例
        async with get_session_maker()() as session:
            db_instance = await session.get(BotInstanceDB, instance_id)

            if db_instance is None:
                logger.error(f"API: 实例未找到: {instance_id}")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=error_response(message=f"实例 {instance_id} 未找到"),
                )

            # 获取容器实时状态
            try:
                status_value = await napcat_manager.get_status(instance_id)
                logger.info(f"API: 实例 {instance_id} 状态: {status_value}")
                status_str = status_value.value
            except Exception:
                # 如果获取状态失败，使用数据库中的状态
                status_str = db_instance.status

            # 转换为响应数据
            instance_data = {
                "id": db_instance.id,
                "name": db_instance.name,
                "qq_number": db_instance.qq_number,
                "protocol": db_instance.protocol,
                "status": status_str,
                "container_name": db_instance.container_name,
                "port": db_instance.port,
                "volume_path": db_instance.volume_path,
                "description": db_instance.description,
                "created_at": db_instance.created_at.isoformat()
                if db_instance.created_at
                else None,
                "updated_at": db_instance.updated_at.isoformat()
                if db_instance.updated_at
                else None,
            }

            return JSONResponse(
                content=success_response(data=instance_data, message="获取实例详情成功")
            )

    except Exception as e:
        logger.error(f"API: 获取实例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"获取实例详情失败: {e}"),
        )


@router.post(
    "/{instance_id}/start",
    summary="启动实例",
    description="启动指定的 Bot 实例",
)
async def start_instance(instance_id: str) -> JSONResponse:
    """启动 Bot 实例。

    Args:
        instance_id: 实例 ID

    Returns:
        JSONResponse: 包含启动结果的统一格式响应

    """
    logger.info(f"API: 正在启动实例：id={instance_id}")

    try:
        # 从数据库获取实例信息
        async with get_session_maker()() as session:
            db_instance = await session.get(BotInstanceDB, instance_id)

            if db_instance is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=error_response(message=f"实例 {instance_id} 未找到"),
                )

            # 启动容器
            await napcat_manager.start(instance_id)

            # 更新数据库状态
            db_instance.status = InstanceStatus.RUNNING.value
            db_instance.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(db_instance)

            # 返回完整实例数据
            instance_data = {
                "id": db_instance.id,
                "name": db_instance.name,
                "qq_number": db_instance.qq_number,
                "protocol": db_instance.protocol,
                "status": db_instance.status,
                "container_name": db_instance.container_name,
                "port": db_instance.port,
                "volume_path": db_instance.volume_path,
                "description": db_instance.description,
                "created_at": db_instance.created_at.isoformat()
                if db_instance.created_at
                else None,
                "updated_at": db_instance.updated_at.isoformat()
                if db_instance.updated_at
                else None,
            }

            logger.info(f"API: 实例已启动：id={instance_id}")

            return JSONResponse(
                content=success_response(data=instance_data, message="实例启动成功")
            )

    except BotError as e:
        logger.error(f"API: 启动实例失败：{e.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(message=e.message),
        )
    except Exception as e:
        logger.error(f"API: 启动实例时发生未知错误：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"启动实例失败：{e}"),
        )


@router.post(
    "/{instance_id}/stop",
    summary="停止实例",
    description="停止指定的 Bot 实例",
)
async def stop_instance(instance_id: str) -> JSONResponse:
    """停止 Bot 实例。

    Args:
        instance_id: 实例 ID

    Returns:
        JSONResponse: 包含停止结果的统一格式响应

    """
    logger.info(f"API: 正在停止实例：id={instance_id}")

    try:
        # 从数据库获取实例信息
        async with get_session_maker()() as session:
            db_instance = await session.get(BotInstanceDB, instance_id)

            if db_instance is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=error_response(message=f"实例 {instance_id} 未找到"),
                )

            # 停止容器
            await napcat_manager.stop(instance_id)

            # 更新数据库状态
            db_instance.status = InstanceStatus.STOPPED.value
            db_instance.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(db_instance)

            # 返回完整实例数据
            instance_data = {
                "id": db_instance.id,
                "name": db_instance.name,
                "qq_number": db_instance.qq_number,
                "protocol": db_instance.protocol,
                "status": db_instance.status,
                "container_name": db_instance.container_name,
                "port": db_instance.port,
                "volume_path": db_instance.volume_path,
                "description": db_instance.description,
                "created_at": db_instance.created_at.isoformat()
                if db_instance.created_at
                else None,
                "updated_at": db_instance.updated_at.isoformat()
                if db_instance.updated_at
                else None,
            }

            logger.info(f"API: 实例已停止：id={instance_id}")

            return JSONResponse(
                content=success_response(data=instance_data, message="实例停止成功")
            )

    except BotError as e:
        logger.error(f"API: 停止实例失败：{e.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(message=e.message),
        )
    except Exception as e:
        logger.error(f"API: 停止实例时发生未知错误：{e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"停止实例失败：{e}"),
        )


@router.post(
    "/{instance_id}/restart",
    summary="重启实例",
    description="重启指定的 Bot 实例",
)
async def restart_instance(instance_id: str) -> JSONResponse:
    """重启 Bot 实例。

    Args:
        instance_id: 实例 ID

    Returns:
        JSONResponse: 包含重启结果的统一格式响应

    """
    logger.info(f"API: 正在重启实例: id={instance_id}")

    try:
        # 从数据库获取实例信息
        async with get_session_maker()() as session:
            db_instance = await session.get(BotInstanceDB, instance_id)

            if db_instance is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=error_response(message=f"实例 {instance_id} 未找到"),
                )

            # 重启容器（先停止再启动）
            await napcat_manager.stop(instance_id)
            await napcat_manager.start(instance_id)

            # 更新数据库状态
            db_instance.status = InstanceStatus.RUNNING.value
            db_instance.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(db_instance)

            # 返回完整实例数据
            instance_data = {
                "id": db_instance.id,
                "name": db_instance.name,
                "qq_number": db_instance.qq_number,
                "protocol": db_instance.protocol,
                "status": db_instance.status,
                "container_name": db_instance.container_name,
                "port": db_instance.port,
                "volume_path": db_instance.volume_path,
                "description": db_instance.description,
                "created_at": db_instance.created_at.isoformat()
                if db_instance.created_at
                else None,
                "updated_at": db_instance.updated_at.isoformat()
                if db_instance.updated_at
                else None,
            }

            logger.info(f"API: 实例已重启：id={instance_id}")

            return JSONResponse(
                content=success_response(data=instance_data, message="实例重启成功")
            )

    except BotError as e:
        logger.error(f"API: 重启实例失败: {e.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(message=e.message),
        )
    except Exception as e:
        logger.error(f"API: 重启实例时发生未知错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"重启实例失败: {e}"),
        )


@router.delete(
    "/{instance_id}",
    summary="删除实例",
    description="删除指定的 Bot 实例",
)
async def delete_instance(instance_id: str) -> JSONResponse:
    """删除 Bot 实例。

    Args:
        instance_id: 实例 ID

    Returns:
        JSONResponse: 包含删除结果的统一格式响应

    """
    logger.info(f"API: 正在删除实例: id={instance_id}")

    try:
        # 从数据库获取实例信息
        async with get_session_maker()() as session:
            db_instance = await session.get(BotInstanceDB, instance_id)

            if db_instance is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=error_response(message=f"实例 {instance_id} 未找到"),
                )

            # 删除容器
            await napcat_manager.delete(instance_id)

            # 从数据库删除
            await session.delete(db_instance)
            await session.commit()

            logger.info(f"API: 实例已删除: id={instance_id}")

            return JSONResponse(
                content=success_response(
                    data={"id": instance_id}, message="实例删除成功"
                )
            )

    except BotError as e:
        logger.error(f"API: 删除实例失败: {e.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(message=e.message),
        )
    except Exception as e:
        logger.error(f"API: 删除实例时发生未知错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"删除实例失败: {e}"),
        )


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
        JSONResponse: 包含日志内容的统一格式响应

    """
    logger.info(f"API: 正在获取实例日志: id={instance_id}")

    try:
        logs = await napcat_manager.get_logs(instance_id, tail)

        return JSONResponse(
            content=success_response(
                data={"logs": logs, "instance_id": instance_id, "tail": tail},
                message="日志获取成功",
            )
        )

    except BotError as e:
        logger.error(f"API: 获取日志失败: {e.message}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(message=e.message),
        )
    except Exception as e:
        logger.error(f"API: 获取日志时发生未知错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(message=f"获取日志失败: {e}"),
        )
