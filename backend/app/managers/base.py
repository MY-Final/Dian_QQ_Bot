"""Bot 管理器基类模块。

定义 Bot 管理器的抽象接口，所有具体实现必须继承此类。
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.instance import InstanceResponse, InstanceStatus


class BaseBotManager(ABC):
    """Abstract base class for Bot managers."""

    @abstractmethod
    async def create(
        self,
        name: str,
        qq_number: str,
        protocol: str,
        description: Optional[str] = None,
    ) -> InstanceResponse:
        """Create a new Bot instance.

        Args:
            name: Instance name
            qq_number: QQ number
            protocol: Bot protocol
            description: Optional description

        Returns:
            InstanceResponse: Created instance details

        Raises:
            BotAlreadyExistsError: If instance already exists
            BotError: If creation fails

        """
        pass

    @abstractmethod
    async def start(self, instance_id: str) -> InstanceResponse:
        """Start a Bot instance.

        Args:
            instance_id: Instance ID

        Returns:
            InstanceResponse: Updated instance details

        Raises:
            BotNotFoundError: If instance not found
            BotStartError: If start fails

        """
        pass

    @abstractmethod
    async def stop(self, instance_id: str) -> InstanceResponse:
        """Stop a Bot instance.

        Args:
            instance_id: Instance ID

        Returns:
            InstanceResponse: Updated instance details

        Raises:
            BotNotFoundError: If instance not found
            BotStopError: If stop fails

        """
        pass

    @abstractmethod
    async def restart(self, instance_id: str) -> InstanceResponse:
        """Restart a Bot instance.

        Args:
            instance_id: Instance ID

        Returns:
            InstanceResponse: Updated instance details

        Raises:
            BotNotFoundError: If instance not found
            BotError: If restart fails

        """
        pass

    @abstractmethod
    async def delete(self, instance_id: str) -> None:
        """Delete a Bot instance.

        Args:
            instance_id: Instance ID

        Raises:
            BotNotFoundError: If instance not found
            BotDeleteError: If deletion fails

        """
        pass

    @abstractmethod
    async def get_status(self, instance_id: str) -> InstanceStatus:
        """Get Bot instance status.

        Args:
            instance_id: Instance ID

        Returns:
            InstanceStatus: Current status

        Raises:
            BotNotFoundError: If instance not found

        """
        pass

    @abstractmethod
    async def get_logs(self, instance_id: str, tail: int = 100) -> str:
        """Get Bot instance logs.

        Args:
            instance_id: Instance ID
            tail: Number of lines to fetch

        Returns:
            str: Container logs

        Raises:
            BotNotFoundError: If instance not found

        """
        pass

    @abstractmethod
    async def list_instances(self) -> list[InstanceResponse]:
        """List all Bot instances.

        Returns:
            list[InstanceResponse]: List of all instances

        """
        pass
