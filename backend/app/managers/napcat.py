"""NapCat Bot 管理器实现模块。

提供 NapCat Docker 容器的完整生命周期管理。
"""

import logging
from datetime import datetime
from typing import Optional

import docker
from docker.errors import DockerException, NotFound

from app.core.config import settings
from app.core.exceptions import (
    BotAlreadyExistsError,
    BotDeleteError,
    BotError,
    BotNotFoundError,
    BotStartError,
    BotStopError,
    DockerConnectionError,
)
from app.database import save_instance, update_instance
from app.managers.base import BaseBotManager
from app.models.db_models import BotInstanceDB
from app.models.instance import (
    InstanceCreate,
    InstanceResponse,
    InstanceStatus,
    ProtocolType,
)
from app.utils.docker_utils import (
    allocate_port,
    format_container_env,
    generate_container_name,
    generate_instance_id,
    generate_volume_path,
    get_docker_volume_bind,
)

logger = logging.getLogger(__name__)


class NapCatManager(BaseBotManager):
    """NapCat Docker Bot 管理器。"""

    def __init__(self) -> None:
        """初始化 NapCat 管理器。"""
        self._client: Optional[docker.DockerClient] = None

    @property
    def client(self) -> docker.DockerClient:
        """获取 Docker 客户端（延迟初始化）。

        Returns:
            docker.DockerClient: Docker 客户端实例

        Raises:
            DockerConnectionError: 连接失败时抛出

        """
        if self._client is None:
            try:
                self._client = docker.from_env()
            except DockerException as e:
                logger.error(f"连接 Docker 失败: {e}", exc_info=True)
                raise DockerConnectionError(
                    "无法连接到 Docker 守护进程，请确保 Docker Desktop 已启动"
                ) from e
        return self._client

    def _db_to_response(self, db_instance: BotInstanceDB) -> InstanceResponse:
        """将数据库模型转换为响应模式。

        Args:
            db_instance: 数据库实例

        Returns:
            InstanceResponse: 响应模式

        """
        logger.info(
            f"Converting DB to response: id={db_instance.id}, port_web_ui={db_instance.port_web_ui}, port_ws={db_instance.port_ws}"
        )

        return InstanceResponse(
            id=db_instance.id,
            name=db_instance.name,
            qq_number=db_instance.qq_number,
            protocol=ProtocolType(db_instance.protocol),
            status=InstanceStatus(db_instance.status),
            container_name=db_instance.container_name,
            port=db_instance.port,
            port_web_ui=db_instance.port_web_ui,
            port_ws=db_instance.port_ws,
            volume_path=db_instance.volume_path,
            description=db_instance.description,
            created_at=db_instance.created_at,
            updated_at=db_instance.updated_at,
        )

    async def create(
        self,
        name: str,
        qq_number: str,
        protocol: str = "napcat",
        description: Optional[str] = None,
        port_web_ui: Optional[int] = None,
        port_http: Optional[int] = None,
        port_ws: Optional[int] = None,
        napcat_uid: Optional[int] = None,
        napcat_gid: Optional[int] = None,
    ) -> InstanceResponse:
        """创建新的 NapCat Bot 实例。

        Args:
            name: 实例名称
            qq_number: QQ 号码
            protocol: Bot 协议（默认: napcat）
            description: 可选描述
            port_web_ui: Web UI 端口（可选）
            port_http: HTTP API 端口（可选，不指定则自动分配）
            port_ws: WebSocket 端口（可选，不指定则使用 HTTP+1）
            napcat_uid: NAPCAT_UID 用户ID（可选）
            napcat_gid: NAPCAT_GID 组ID（可选）

        Returns:
            InstanceResponse: 创建的实例详情

        Raises:
            BotAlreadyExistsError: 如果实例已存在
            BotError: 如果创建失败

        """
        instance_id = generate_instance_id()
        container_name = generate_container_name(protocol, instance_id)

        # 端口分配逻辑
        # HTTP 端口为主端口，如果没指定则自动分配
        http_port = port_http if port_http is not None else await allocate_port()
        # WebSocket 端口如果没指定则使用 HTTP+1
        ws_port = port_ws if port_ws is not None else http_port + 1
        # Web UI 端口（可选）
        web_ui_port = port_web_ui

        volume_path = generate_volume_path(instance_id, protocol)

        # 构建环境变量
        env = format_container_env(qq_number, instance_id, protocol)
        if napcat_uid is not None:
            env["NAPCAT_UID"] = str(napcat_uid)
        if napcat_gid is not None:
            env["NAPCAT_GID"] = str(napcat_gid)

        logger.info(
            f"正在创建 NapCat 实例: name={name}, qq={qq_number}, "
            f"instance_id={instance_id}, container={container_name}, "
            f"http_port={http_port}, ws_port={ws_port}"
            f"{', web_ui_port=' + str(web_ui_port) if web_ui_port else ''}"
        )

        # 构建端口映射
        ports_mapping = {
            "3000/tcp": http_port,  # HTTP API
            "3001/tcp": ws_port,  # WebSocket
        }
        if web_ui_port:
            ports_mapping["6099/tcp"] = web_ui_port  # Web UI (如果指定)

        now = datetime.utcnow()

        db_instance = BotInstanceDB(
            id=instance_id,
            name=name,
            qq_number=qq_number,
            protocol=protocol,
            status=InstanceStatus.CREATED.value,
            container_name=container_name,
            port=http_port,  # 主端口存储 HTTP 端口
            port_web_ui=web_ui_port if web_ui_port else None,
            port_ws=ws_port if ws_port else None,
            volume_path=str(volume_path),
            description=description,
            created_at=now,
            updated_at=now,
        )

        # 先写入 DB，确保持久化存在
        db_instance = await save_instance(db_instance)

        # 同步创建容器，确保结果可追踪
        try:
            container = self.client.containers.run(
                image=settings.napcat_image,
                name=container_name,
                ports=ports_mapping,
                volumes=get_docker_volume_bind(volume_path),
                environment=env,
                detach=True,
                remove=False,
            )
            logger.info(f"容器创建成功: {container_name}")

            # 更新 DB 为 RUNNING，并记录实际信息
            db_instance.status = InstanceStatus.RUNNING.value
            db_instance.updated_at = datetime.utcnow()
            db_instance = await update_instance(db_instance)

        except DockerException as e:
            logger.error(f"创建容器失败: {e}", exc_info=True)
            db_instance.status = InstanceStatus.ERROR.value
            db_instance.description = f"创建容器失败: {e}"
            await update_instance(db_instance)
            raise BotError(f"创建容器失败: {e}") from e

        logger.info(f"NapCat 实例创建完成: instance_id={instance_id}")

        return self._db_to_response(db_instance)

    async def start(self, instance_id: str) -> InstanceResponse:
        """启动 NapCat Bot 实例。

        Args:
            instance_id: 实例 ID

        Returns:
            InstanceResponse: 更新后的实例详情

        Raises:
            BotNotFoundError: 如果实例未找到
            BotStartError: 如果启动失败

        """
        logger.info(f"正在启动 NapCat 实例: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            container.start()
            logger.info(f"NapCat 实例已启动: instance_id={instance_id}")

        except NotFound:
            logger.error(f"容器未找到: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"启动容器失败: {e}", exc_info=True)
            raise BotStartError(instance_id) from e

        now = datetime.utcnow()
        db_instance = BotInstanceDB(
            id=instance_id,
            name="temp",
            qq_number="0",
            protocol="napcat",
            status=InstanceStatus.RUNNING.value,
            container_name=container_name,
            port=30000,
            volume_path="",
            created_at=now,
            updated_at=now,
        )

        return self._db_to_response(db_instance)

    async def stop(self, instance_id: str) -> InstanceResponse:
        """停止 NapCat Bot 实例。

        Args:
            instance_id: 实例 ID

        Returns:
            InstanceResponse: 更新后的实例详情

        Raises:
            BotNotFoundError: 如果实例未找到
            BotStopError: 如果停止失败

        """
        logger.info(f"正在停止 NapCat 实例: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=10)
            logger.info(f"NapCat 实例已停止: instance_id={instance_id}")

        except NotFound:
            logger.error(f"容器未找到: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"停止容器失败: {e}", exc_info=True)
            raise BotStopError(instance_id) from e

        now = datetime.utcnow()
        db_instance = BotInstanceDB(
            id=instance_id,
            name="temp",
            qq_number="0",
            protocol="napcat",
            status=InstanceStatus.STOPPED.value,
            container_name=container_name,
            port=30000,
            volume_path="",
            created_at=now,
            updated_at=now,
        )

        return self._db_to_response(db_instance)

    async def restart(self, instance_id: str) -> InstanceResponse:
        """重启 NapCat Bot 实例。

        Args:
            instance_id: 实例 ID

        Returns:
            InstanceResponse: 更新后的实例详情

        Raises:
            BotNotFoundError: 如果实例未找到
            BotError: 如果重启失败

        """
        logger.info(f"正在重启 NapCat 实例: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            container.restart(timeout=10)
            logger.info(f"NapCat 实例已重启: instance_id={instance_id}")

        except NotFound:
            logger.error(f"容器未找到: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"重启容器失败: {e}", exc_info=True)
            raise BotError(f"重启容器失败: {e}") from e

        now = datetime.utcnow()
        db_instance = BotInstanceDB(
            id=instance_id,
            name="temp",
            qq_number="0",
            protocol="napcat",
            status=InstanceStatus.RUNNING.value,
            container_name=container_name,
            port=30000,
            volume_path="",
            created_at=now,
            updated_at=now,
        )

        return self._db_to_response(db_instance)

    async def delete(self, instance_id: str) -> None:
        """删除 NapCat Bot 实例。

        Args:
            instance_id: 实例 ID

        Raises:
            BotNotFoundError: 如果实例未找到
            BotDeleteError: 如果删除失败

        """
        logger.info(f"正在删除 NapCat 实例: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=5)
            container.remove()
            logger.info(f"容器已移除: {container_name}")

        except NotFound:
            logger.warning(f"容器未找到（可能已被删除）: {container_name}")
        except DockerException as e:
            logger.error(f"删除容器失败: {e}", exc_info=True)
            raise BotDeleteError(instance_id) from e

        logger.info(f"NapCat 实例已删除: instance_id={instance_id}")

    async def get_status(self, instance_id: str) -> InstanceStatus:
        """获取 NapCat Bot 实例状态。

        Args:
            instance_id: 实例 ID

        Returns:
            InstanceStatus: 当前状态

        Raises:
            BotNotFoundError: 如果实例未找到

        """
        logger.debug(f"正在获取实例状态: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            state = container.attrs.get("State", {})
            docker_status = state.get("Status", "unknown")

            if docker_status == "running":
                return InstanceStatus.RUNNING
            elif docker_status == "exited":
                return InstanceStatus.STOPPED
            else:
                return InstanceStatus.ERROR

        except NotFound:
            logger.error(f"容器未找到: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"获取容器状态失败: {e}", exc_info=True)
            return InstanceStatus.ERROR

    async def get_logs(self, instance_id: str, tail: int = 100) -> str:
        """获取 NapCat Bot 实例日志。

        Args:
            instance_id: 实例 ID
            tail: 获取的日志行数

        Returns:
            str: 容器日志

        Raises:
            BotNotFoundError: 如果实例未找到

        """
        logger.debug(f"正在获取实例日志: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=tail, timestamps=True).decode("utf-8")
            return logs

        except NotFound:
            logger.error(f"容器未找到: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"获取容器日志失败: {e}", exc_info=True)
            return f"获取日志失败: {e}"

    async def list_instances(self) -> list[InstanceResponse]:
        """列出所有 NapCat Bot 实例。

        Returns:
            list[InstanceResponse]: 所有实例列表

        """
        logger.debug("正在列出所有 NapCat 实例")

        instances = []
        try:
            containers = self.client.containers.list(all=True)
            logger.info(f"找到 {len(containers)} 个容器")
        except DockerException as e:
            logger.error(f"列出容器失败: {e}", exc_info=True)
            return instances

        return instances
