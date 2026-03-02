"""Bot exceptions module."""

from typing import Optional


class BotError(Exception):
    """Base exception for Bot errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BotNotFoundError(BotError):
    """Raised when Bot instance is not found."""

    def __init__(self, instance_id: str) -> None:
        super().__init__(f"Bot instance '{instance_id}' not found")
        self.instance_id = instance_id


class BotAlreadyExistsError(BotError):
    """Raised when Bot instance already exists."""

    def __init__(self, instance_id: str) -> None:
        super().__init__(f"Bot instance '{instance_id}' already exists")
        self.instance_id = instance_id


class BotStartError(BotError):
    """Raised when Bot fails to start."""

    def __init__(self, instance_id: str, exit_code: Optional[int] = None) -> None:
        message = f"Failed to start Bot instance '{instance_id}'"
        if exit_code is not None:
            message += f" (exit code: {exit_code})"
        super().__init__(message)
        self.instance_id = instance_id
        self.exit_code = exit_code


class BotStopError(BotError):
    """Raised when Bot fails to stop."""

    def __init__(self, instance_id: str, exit_code: Optional[int] = None) -> None:
        message = f"Failed to stop Bot instance '{instance_id}'"
        if exit_code is not None:
            message += f" (exit code: {exit_code})"
        super().__init__(message)
        self.instance_id = instance_id
        self.exit_code = exit_code


class BotDeleteError(BotError):
    """Raised when Bot fails to delete."""

    def __init__(self, instance_id: str) -> None:
        super().__init__(f"Failed to delete Bot instance '{instance_id}'")
        self.instance_id = instance_id


class DockerConnectionError(BotError):
    """Raised when Docker daemon connection fails."""

    def __init__(self, message: str = "Failed to connect to Docker daemon") -> None:
        super().__init__(message)


class PortAllocationError(BotError):
    """Raised when port allocation fails."""

    def __init__(self, port: int) -> None:
        super().__init__(f"Failed to allocate port {port}")
        self.port = port
