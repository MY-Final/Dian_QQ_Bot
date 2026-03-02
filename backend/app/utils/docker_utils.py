"""Docker utility functions module."""

import logging
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_instance_id() -> str:
    """Generate a short unique instance ID.

    Returns:
        str: 8-character unique ID

    """
    return uuid.uuid4().hex[:8]


def generate_container_name(protocol: str, instance_id: str) -> str:
    """Generate Docker container name.

    Args:
        protocol: Bot protocol (e.g., 'napcat')
        instance_id: Instance unique ID

    Returns:
        str: Container name in format 'dian-{protocol}-{instance_id}'

    """
    return f"{settings.container_prefix}-{protocol}-{instance_id}"


def generate_volume_path(instance_id: str, protocol: str) -> Path:
    """Generate volume mount path for instance.

    Args:
        instance_id: Instance unique ID
        protocol: Bot protocol

    Returns:
        Path: Volume path in format './data/instances/{instance_id}/{protocol}/'

    """
    volume_path = settings.instances_dir / instance_id / protocol
    volume_path.mkdir(parents=True, exist_ok=True)
    return volume_path


async def allocate_port() -> int:
    """Allocate an available port from the configured range.

    Returns:
        int: Available port number

    Raises:
        PortAllocationError: If no ports available in range

    Note:
        This is a simple implementation. In production, should track
        allocated ports in database to avoid conflicts.

    """
    import random

    port_range = range(settings.port_range_start, settings.port_range_end + 1)
    available_ports = list(port_range)

    if not available_ports:
        from app.core.exceptions import PortAllocationError

        raise PortAllocationError(0)

    selected_port = random.choice(available_ports)
    logger.debug(f"Allocated port {selected_port} for new instance")

    return selected_port


def format_container_env(
    qq_number: str,
    instance_id: str,
    protocol: str,
) -> dict[str, str]:
    """Format environment variables for container.

    Args:
        qq_number: QQ number
        instance_id: Instance ID
        protocol: Bot protocol

    Returns:
        dict: Environment variables

    """
    return {
        "QQ_NUMBER": qq_number,
        "INSTANCE_ID": instance_id,
        "PROTOCOL": protocol,
    }
