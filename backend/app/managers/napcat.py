"""NapCat Bot Manager implementation."""

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
)

logger = logging.getLogger(__name__)


class NapCatManager(BaseBotManager):
    """NapCat Docker Bot Manager."""

    def __init__(self) -> None:
        """Initialize NapCat manager."""
        self._client: Optional[docker.DockerClient] = None

    @property
    def client(self) -> docker.DockerClient:
        """Get Docker client with lazy initialization.

        Returns:
            docker.DockerClient: Docker client instance

        Raises:
            DockerConnectionError: If connection fails

        """
        if self._client is None:
            try:
                self._client = docker.from_env()
            except DockerException as e:
                logger.error(f"Failed to connect to Docker: {e}", exc_info=True)
                raise DockerConnectionError(
                    "无法连接到 Docker 守护进程，请确保 Docker Desktop 已启动"
                ) from e
        return self._client

    def _db_to_response(self, db_instance: BotInstanceDB) -> InstanceResponse:
        """Convert database model to response schema.

        Args:
            db_instance: Database instance

        Returns:
            InstanceResponse: Response schema

        """
        return InstanceResponse(
            id=db_instance.id,
            name=db_instance.name,
            qq_number=db_instance.qq_number,
            protocol=ProtocolType(db_instance.protocol),
            status=InstanceStatus(db_instance.status),
            container_name=db_instance.container_name,
            port=db_instance.port,
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
    ) -> InstanceResponse:
        """Create a new NapCat Bot instance.

        Args:
            name: Instance name
            qq_number: QQ number
            protocol: Bot protocol (default: napcat)
            description: Optional description

        Returns:
            InstanceResponse: Created instance details

        Raises:
            BotAlreadyExistsError: If instance already exists
            BotError: If creation fails

        """
        instance_id = generate_instance_id()
        container_name = generate_container_name(protocol, instance_id)
        port = await allocate_port()
        volume_path = str(generate_volume_path(instance_id, protocol))
        env = format_container_env(qq_number, instance_id, protocol)

        logger.info(
            f"Creating NapCat instance: name={name}, qq={qq_number}, "
            f"instance_id={instance_id}, container={container_name}, port={port}"
        )

        try:
            container = self.client.containers.run(
                image=settings.napcat_image,
                name=container_name,
                ports={"3000/tcp": port},
                volumes={volume_path: {"bind": "/app/config", "mode": "rw"}},
                environment=env,
                detach=False,
                remove=False,
            )
            logger.debug(f"Container {container_name} created (not started)")

        except DockerException as e:
            logger.error(f"Failed to create container: {e}", exc_info=True)
            raise BotError(f"创建容器失败: {e}") from e

        now = datetime.utcnow()
        db_instance = BotInstanceDB(
            id=instance_id,
            name=name,
            qq_number=qq_number,
            protocol=protocol,
            status=InstanceStatus.CREATED.value,
            container_name=container_name,
            port=port,
            volume_path=volume_path,
            description=description,
            created_at=now,
            updated_at=now,
        )

        logger.info(f"NapCat instance created successfully: instance_id={instance_id}")

        return self._db_to_response(db_instance)

    async def start(self, instance_id: str) -> InstanceResponse:
        """Start a NapCat Bot instance.

        Args:
            instance_id: Instance ID

        Returns:
            InstanceResponse: Updated instance details

        Raises:
            BotNotFoundError: If instance not found
            BotStartError: If start fails

        """
        logger.info(f"Starting NapCat instance: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            container.start()
            logger.info(f"NapCat instance started: instance_id={instance_id}")

        except NotFound:
            logger.error(f"Container not found: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"Failed to start container: {e}", exc_info=True)
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
        """Stop a NapCat Bot instance.

        Args:
            instance_id: Instance ID

        Returns:
            InstanceResponse: Updated instance details

        Raises:
            BotNotFoundError: If instance not found
            BotStopError: If stop fails

        """
        logger.info(f"Stopping NapCat instance: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=10)
            logger.info(f"NapCat instance stopped: instance_id={instance_id}")

        except NotFound:
            logger.error(f"Container not found: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"Failed to stop container: {e}", exc_info=True)
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
        """Restart a NapCat Bot instance.

        Args:
            instance_id: Instance ID

        Returns:
            InstanceResponse: Updated instance details

        Raises:
            BotNotFoundError: If instance not found
            BotError: If restart fails

        """
        logger.info(f"Restarting NapCat instance: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            container.restart(timeout=10)
            logger.info(f"NapCat instance restarted: instance_id={instance_id}")

        except NotFound:
            logger.error(f"Container not found: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"Failed to restart container: {e}", exc_info=True)
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
        """Delete a NapCat Bot instance.

        Args:
            instance_id: Instance ID

        Raises:
            BotNotFoundError: If instance not found
            BotDeleteError: If deletion fails

        """
        logger.info(f"Deleting NapCat instance: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=5)
            container.remove()
            logger.info(f"Container removed: {container_name}")

        except NotFound:
            logger.warning(
                f"Container not found (may already be deleted): {container_name}"
            )
        except DockerException as e:
            logger.error(f"Failed to delete container: {e}", exc_info=True)
            raise BotDeleteError(instance_id) from e

        logger.info(f"NapCat instance deleted: instance_id={instance_id}")

    async def get_status(self, instance_id: str) -> InstanceStatus:
        """Get NapCat Bot instance status.

        Args:
            instance_id: Instance ID

        Returns:
            InstanceStatus: Current status

        Raises:
            BotNotFoundError: If instance not found

        """
        logger.debug(f"Getting status for instance: instance_id={instance_id}")

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
            logger.error(f"Container not found: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"Failed to get container status: {e}", exc_info=True)
            return InstanceStatus.ERROR

    async def get_logs(self, instance_id: str, tail: int = 100) -> str:
        """Get NapCat Bot instance logs.

        Args:
            instance_id: Instance ID
            tail: Number of lines to fetch

        Returns:
            str: Container logs

        Raises:
            BotNotFoundError: If instance not found

        """
        logger.debug(f"Fetching logs for instance: instance_id={instance_id}")

        container_name = generate_container_name("napcat", instance_id)

        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=tail, timestamps=True).decode("utf-8")
            return logs

        except NotFound:
            logger.error(f"Container not found: {container_name}")
            raise BotNotFoundError(instance_id) from None
        except DockerException as e:
            logger.error(f"Failed to get container logs: {e}", exc_info=True)
            return f"Error fetching logs: {e}"

    async def list_instances(self) -> list[InstanceResponse]:
        """List all NapCat Bot instances.

        Returns:
            list[InstanceResponse]: List of all instances

        """
        logger.debug("Listing all NapCat instances")

        instances = []
        try:
            containers = self.client.containers.list(all=True)
            logger.info(f"Found {len(containers)} containers")
        except DockerException as e:
            logger.error(f"Failed to list containers: {e}", exc_info=True)
            return instances

        return instances
