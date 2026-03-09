"""Bot 实例业务服务模块。

封装实例管理的核心业务逻辑，路由层只负责参数接收和响应转换。
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum

from sqlalchemy import select

from app.core.exceptions import BotError, BotNotFoundError
from app.database import get_session_maker
from app.managers.napcat import NapCatManager
from app.models.db_models import BotInstanceDB
from app.models.instance import InstanceCreate, InstanceStatus
from app.services.image_service import ImageService

logger = logging.getLogger(__name__)


class InstanceService:
    """Bot 实例业务服务。"""

    _instance_locks: dict[str, asyncio.Lock] = {}

    def __init__(self, manager: NapCatManager, image_service: ImageService | None = None) -> None:
        """初始化服务。

        Args:
            manager: NapCat 管理器实例
            image_service: 镜像服务实例
        """
        self._manager = manager
        self._image_service = image_service or ImageService()

    @classmethod
    def _get_instance_lock(cls, instance_id: str) -> asyncio.Lock:
        """获取实例级互斥锁。

        Args:
            instance_id: 实例 ID

        Returns:
            asyncio.Lock: 实例级锁
        """
        existing_lock = cls._instance_locks.get(instance_id)
        if existing_lock is not None:
            return existing_lock

        new_lock = asyncio.Lock()
        cls._instance_locks[instance_id] = new_lock
        return new_lock

    async def create_instance(self, data: InstanceCreate) -> dict[str, object]:
        """创建实例。

        Args:
            data: 实例创建参数

        Returns:
            dict[str, object]: 创建后的实例数据

        Raises:
            BotError: 创建失败时抛出
        """
        resolved_image_repo = data.image_repo
        if data.image_registry and data.image_repo:
            resolved_image_repo = f"{data.image_registry.rstrip('/')}/{data.image_repo.lstrip('/')}"

        if resolved_image_repo and data.image_tag:
            image_ref = f"{resolved_image_repo}:{data.image_tag}"
            await self._image_service.ensure_image_available(image_ref=image_ref, allow_pull=False)

        instance = await self._manager.create(
            name=data.name,
            qq_number=data.qq_number,
            protocol=data.protocol.value,
            description=data.description,
            port_web_ui=data.port_web_ui,
            port_http=data.port_http,
            port_ws=data.port_ws,
            napcat_uid=data.napcat_uid,
            napcat_gid=data.napcat_gid,
            image_repo=resolved_image_repo,
            image_tag=data.image_tag,
        )
        logger.info("实例创建成功: instance_id=%s, name=%s", instance.id, data.name)
        return self._serialize_instance_model(instance.model_dump())

    async def list_instances(self) -> list[dict[str, object]]:
        """获取实例列表。

        Returns:
            list[dict[str, object]]: 实例列表

        Raises:
            BotError: 查询失败时抛出
        """
        try:
            async with get_session_maker()() as session:
                result = await session.execute(select(BotInstanceDB))
                db_instances = result.scalars().all()

                serialized_instances: list[dict[str, object]] = []
                has_status_change = False
                for db_instance in db_instances:
                    runtime_status_value = db_instance.status
                    try:
                        runtime_status = await self._manager.get_status(db_instance.id)
                        runtime_status_value = runtime_status.value
                    except BotError:
                        runtime_status_value = InstanceStatus.ERROR.value

                    if db_instance.status != runtime_status_value:
                        db_instance.status = runtime_status_value
                        db_instance.updated_at = datetime.utcnow()
                        has_status_change = True

                    serialized_instance = self._serialize_db_instance(db_instance)
                    serialized_instance["status"] = runtime_status_value
                    serialized_instances.append(serialized_instance)

                if has_status_change:
                    await session.commit()

                return serialized_instances
        except Exception as exc:
            logger.error("查询实例列表失败", exc_info=True)
            raise BotError("获取实例列表失败，请稍后重试") from exc

    async def get_instance(self, instance_id: str) -> dict[str, object]:
        """获取实例详情。

        Args:
            instance_id: 实例 ID

        Returns:
            dict[str, object]: 实例详情

        Raises:
            BotNotFoundError: 实例不存在时抛出
            BotError: 查询失败时抛出
        """
        try:
            async with get_session_maker()() as session:
                db_instance = await session.get(BotInstanceDB, instance_id)
                if db_instance is None:
                    raise BotNotFoundError(instance_id)

                try:
                    runtime_status = await self._manager.get_status(instance_id)
                    status_value = runtime_status.value
                except BotError:
                    status_value = db_instance.status

                instance_data = self._serialize_db_instance(db_instance)
                instance_data["status"] = status_value
                return instance_data
        except BotNotFoundError:
            raise
        except Exception as exc:
            logger.error("查询实例详情失败: instance_id=%s", instance_id, exc_info=True)
            raise BotError("获取实例详情失败，请稍后重试") from exc

    async def start_instance(self, instance_id: str) -> dict[str, object]:
        """启动实例。

        Args:
            instance_id: 实例 ID

        Returns:
            dict[str, object]: 启动后的实例数据

        Raises:
            BotNotFoundError: 实例不存在时抛出
            BotError: 启动失败时抛出
        """
        async with self._get_instance_lock(instance_id):
            await self._manager.start(instance_id)
            logger.info("实例启动成功: instance_id=%s", instance_id)
            return await self._update_status_and_get(instance_id, InstanceStatus.RUNNING)

    async def stop_instance(self, instance_id: str) -> dict[str, object]:
        """停止实例。

        Args:
            instance_id: 实例 ID

        Returns:
            dict[str, object]: 停止后的实例数据

        Raises:
            BotNotFoundError: 实例不存在时抛出
            BotError: 停止失败时抛出
        """
        async with self._get_instance_lock(instance_id):
            await self._manager.stop(instance_id)
            logger.info("实例停止成功: instance_id=%s", instance_id)
            return await self._update_status_and_get(instance_id, InstanceStatus.STOPPED)

    async def restart_instance(self, instance_id: str) -> dict[str, object]:
        """重启实例。

        Args:
            instance_id: 实例 ID

        Returns:
            dict[str, object]: 重启后的实例数据

        Raises:
            BotNotFoundError: 实例不存在时抛出
            BotError: 重启失败时抛出
        """
        async with self._get_instance_lock(instance_id):
            await self._manager.stop(instance_id)
            await self._manager.start(instance_id)
            logger.info("实例重启成功: instance_id=%s", instance_id)
            return await self._update_status_and_get(instance_id, InstanceStatus.RUNNING)

    async def delete_instance(self, instance_id: str) -> None:
        """删除实例。

        Args:
            instance_id: 实例 ID

        Raises:
            BotNotFoundError: 实例不存在时抛出
            BotError: 删除失败时抛出
        """
        try:
            async with self._get_instance_lock(instance_id):
                async with get_session_maker()() as session:
                    db_instance = await session.get(BotInstanceDB, instance_id)
                    if db_instance is None:
                        raise BotNotFoundError(instance_id)

                    await self._manager.delete(instance_id)
                    await session.delete(db_instance)
                    await session.commit()
                    logger.info("实例删除成功: instance_id=%s", instance_id)
        except BotNotFoundError:
            raise
        except BotError:
            raise
        except Exception as exc:
            logger.error("删除实例失败: instance_id=%s", instance_id, exc_info=True)
            raise BotError("删除实例失败，请稍后重试") from exc

    async def get_instance_logs(
        self, instance_id: str, tail: int, cursor: int
    ) -> dict[str, object]:
        """获取实例日志。

        Args:
            instance_id: 实例 ID
            tail: 日志行数
            cursor: 日志游标（行偏移）

        Returns:
            dict[str, object]: 日志数据和游标信息

        Raises:
            BotNotFoundError: 实例不存在时抛出
            BotError: 日志获取失败时抛出
        """
        logs_text = await self._manager.get_logs(instance_id, tail)
        log_lines = logs_text.splitlines()

        safe_cursor = max(cursor, 0)
        if safe_cursor > len(log_lines):
            safe_cursor = len(log_lines)

        incremental_lines = log_lines[safe_cursor:]
        return {
            "logs": "\n".join(incremental_lines),
            "instance_id": instance_id,
            "tail": tail,
            "cursor": safe_cursor,
            "next_cursor": len(log_lines),
            "full_line_count": len(log_lines),
            "has_more": len(log_lines) > safe_cursor,
        }

    async def update_instance_image(
        self,
        instance_id: str,
        image_registry: str | None,
        image_repo: str,
        image_tag: str,
        auto_pull: bool,
    ) -> dict[str, object]:
        """更新实例镜像版本信息。

        Args:
            instance_id: 实例 ID
            image_registry: 镜像仓库地址
            image_repo: 镜像仓库
            image_tag: 镜像版本
            auto_pull: 是否允许自动拉取

        Returns:
            dict[str, object]: 更新后的实例数据

        Raises:
            BotNotFoundError: 实例不存在时抛出
            BotError: 更新失败时抛出
        """
        resolved_repo = image_repo
        if image_registry:
            resolved_repo = f"{image_registry.rstrip('/')}/{image_repo.lstrip('/')}"
        image_ref = f"{resolved_repo}:{image_tag}"

        await self._image_service.ensure_image_available(image_ref=image_ref, allow_pull=auto_pull)

        try:
            async with self._get_instance_lock(instance_id):
                async with get_session_maker()() as session:
                    db_instance = await session.get(BotInstanceDB, instance_id)
                    if db_instance is None:
                        raise BotNotFoundError(instance_id)

                    db_instance.image_repo = resolved_repo
                    db_instance.image_tag = image_tag
                    db_instance.image_digest = None
                    db_instance.updated_at = datetime.utcnow()
                    await session.commit()
                    await session.refresh(db_instance)
                    return self._serialize_db_instance(db_instance)
        except BotNotFoundError:
            raise
        except BotError:
            raise
        except Exception as exc:
            logger.error("更新实例镜像失败: instance_id=%s", instance_id, exc_info=True)
            raise BotError("更新实例镜像失败，请稍后重试") from exc

    async def recreate_instance_with_image(
        self,
        instance_id: str,
        auto_pull: bool,
    ) -> dict[str, object]:
        """使用实例配置镜像重建容器。

        Args:
            instance_id: 实例 ID
            auto_pull: 是否允许自动拉取镜像

        Returns:
            dict[str, object]: 重建后的实例数据

        Raises:
            BotNotFoundError: 实例不存在时抛出
            BotError: 重建失败时抛出
        """
        try:
            async with self._get_instance_lock(instance_id):
                async with get_session_maker()() as session:
                    db_instance = await session.get(BotInstanceDB, instance_id)
                    if db_instance is None:
                        raise BotNotFoundError(instance_id)

                image_ref = f"{db_instance.image_repo}:{db_instance.image_tag}"
                await self._image_service.ensure_image_available(
                    image_ref=image_ref, allow_pull=auto_pull
                )
                await self._manager.recreate_with_image(
                    instance_id=instance_id, image_ref=image_ref
                )
                logger.info("实例按镜像重建成功: instance_id=%s, image=%s", instance_id, image_ref)
                return await self.get_instance(instance_id)
        except BotNotFoundError:
            raise
        except BotError:
            raise
        except Exception as exc:
            logger.error("实例重建失败: instance_id=%s", instance_id, exc_info=True)
            raise BotError("实例重建失败，请稍后重试") from exc

    async def _update_status_and_get(
        self,
        instance_id: str,
        instance_status: InstanceStatus,
    ) -> dict[str, object]:
        """更新实例状态并返回实例数据。

        Args:
            instance_id: 实例 ID
            instance_status: 实例状态

        Returns:
            dict[str, object]: 实例数据

        Raises:
            BotNotFoundError: 实例不存在时抛出
            BotError: 更新失败时抛出
        """
        try:
            async with get_session_maker()() as session:
                db_instance = await session.get(BotInstanceDB, instance_id)
                if db_instance is None:
                    raise BotNotFoundError(instance_id)

                db_instance.status = instance_status.value
                db_instance.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(db_instance)

                return self._serialize_db_instance(db_instance)
        except BotNotFoundError:
            raise
        except Exception as exc:
            logger.error("更新实例状态失败: instance_id=%s", instance_id, exc_info=True)
            raise BotError("实例状态更新失败，请稍后重试") from exc

    @staticmethod
    def _serialize_db_instance(db_instance: BotInstanceDB) -> dict[str, object]:
        """序列化数据库实例。

        Args:
            db_instance: 数据库实例

        Returns:
            dict[str, object]: 可响应的数据
        """
        return {
            "id": db_instance.id,
            "name": db_instance.name,
            "qq_number": db_instance.qq_number,
            "protocol": db_instance.protocol,
            "status": db_instance.status,
            "container_name": db_instance.container_name,
            "port": db_instance.port,
            "port_web_ui": db_instance.port_web_ui,
            "port_ws": db_instance.port_ws,
            "volume_path": db_instance.volume_path,
            "description": db_instance.description,
            "image_repo": db_instance.image_repo,
            "image_tag": db_instance.image_tag,
            "image_digest": db_instance.image_digest,
            "created_at": db_instance.created_at.isoformat() if db_instance.created_at else None,
            "updated_at": db_instance.updated_at.isoformat() if db_instance.updated_at else None,
        }

    @staticmethod
    def _serialize_instance_model(data: dict[str, object]) -> dict[str, object]:
        """序列化 Pydantic 实例模型数据。

        Args:
            data: model_dump 后的数据

        Returns:
            dict[str, object]: 可响应的数据
        """
        serialized: dict[str, object] = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, Enum):
                serialized[key] = value.value
            else:
                serialized[key] = value
        return serialized
