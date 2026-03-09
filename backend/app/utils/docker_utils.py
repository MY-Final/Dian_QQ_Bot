"""Docker 工具函数模块。

提供 Docker 相关的通用功能，包括：
- Docker 客户端初始化
- Docker 状态检查（支持 Windows 和 Linux）
- 实例 ID 生成
- 容器名称生成
- 卷路径生成
- 端口分配
- 环境变量格式化
"""

import logging
import platform
import socket
import uuid
from pathlib import Path

import docker

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_docker_client() -> docker.DockerClient:
    """获取 Docker 客户端。

    根据当前操作系统自动选择合适的连接方式。
    - Windows: 使用 named pipe (npipe)
    - Linux: 使用 Unix socket (/var/run/docker.sock)

    Returns:
        docker.DockerClient: Docker 客户端实例

    Raises:
        DockerConnectionError: 连接失败时抛出
    """
    from app.core.exceptions import DockerConnectionError

    try:
        return docker.from_env()
    except Exception as e:
        logger.error(f"连接 Docker 失败: {e}", exc_info=True)
        raise DockerConnectionError("无法连接到 Docker 守护进程，请确保 Docker Desktop 已启动")


def check_docker_status() -> dict[str, object]:
    """检查 Docker 守护进程状态。

    支持 Windows 和 Linux 平台。

    Returns:
        dict[str, object]: Docker 状态信息，包含:
            - running: bool, Docker 是否运行
            - platform: str, 操作系统平台
            - version: str, Docker 版本
            - message: str, 状态消息
    """
    from docker.errors import DockerException

    try:
        client = docker.from_env()
        info = client.info()
        return {
            "running": True,
            "platform": platform.system().lower(),
            "version": info.get("ServerVersion", "unknown"),
            "message": "Docker 运行正常",
        }
    except DockerException as exc:
        logger.warning("Docker 不可用: %s", exc)
        return {
            "running": False,
            "platform": platform.system().lower(),
            "version": None,
            "message": f"Docker 未运行: {str(exc)}",
        }
    except Exception as exc:
        logger.warning("检查 Docker 状态时发生未知错误: %s", exc)
        return {
            "running": False,
            "platform": platform.system().lower(),
            "version": None,
            "message": f"检查 Docker 状态失败: {str(exc)}",
        }


def generate_instance_id() -> str:
    """生成短唯一实例 ID。

    Returns:
        str: 8位唯一 ID
    """
    return uuid.uuid4().hex[:8]


def generate_container_name(protocol: str, instance_id: str) -> str:
    """生成 Docker 容器名称。

    Args:
        protocol: 机器人协议 (如 'napcat')
        instance_id: 实例唯一 ID

    Returns:
        str: 容器名称，格式为 'dian-{protocol}-{instance_id}'
    """
    return f"{settings.container_prefix}-{protocol}-{instance_id}"


def generate_volume_path(instance_id: str, protocol: str) -> Path:
    """生成实例的卷挂载路径。

    Args:
        instance_id: 实例唯一 ID
        protocol: 机器人协议

    Returns:
        Path: 卷路径，格式为 './data/instances/{instance_id}/{protocol}/'
    """
    volume_path = settings.instances_dir / instance_id / protocol
    volume_path.mkdir(parents=True, exist_ok=True)
    return volume_path.resolve()


def get_docker_volume_bind(volume_path: Path) -> dict[str, dict[str, str]]:
    """获取 Docker 卷挂载绑定配置。

    根据操作系统自动处理路径格式：
    - Windows: 转换为 Docker 兼容格式
    - Linux: 直接使用路径

    Args:
        volume_path: 主机上的卷路径

    Returns:
        dict[str, dict[str, str]]: Docker 卷绑定配置
    """
    import sys

    # 获取绝对路径
    host_path = str(volume_path.resolve())

    # Windows 特殊处理
    if sys.platform == "win32":
        # 将反斜杠转换为正斜杠
        host_path = host_path.replace("\\", "/")

        # 处理盘符 (C: -> /c)
        if len(host_path) > 1 and host_path[1] == ":":
            drive = host_path[0].lower()
            host_path = f"/{drive}{host_path[2:]}"

    return {host_path: {"bind": "/app/config", "mode": "rw"}}


def _is_host_port_available(port: int) -> bool:
    """检查主机端口是否可用。

    Args:
        port: 端口号

    Returns:
        bool: 端口是否可用
    """
    socket_handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        socket_handle.bind(("0.0.0.0", port))
        return True
    except OSError:
        return False
    finally:
        socket_handle.close()


def _get_docker_mapped_ports() -> set[int]:
    """获取 Docker 已映射的主机端口。

    Returns:
        set[int]: 已被 Docker 占用的端口集合
    """
    from docker.errors import DockerException

    ports: set[int] = set()
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        for container in containers:
            container_ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            for bindings in container_ports.values():
                if bindings is None:
                    continue
                for binding in bindings:
                    host_port = binding.get("HostPort")
                    if host_port and host_port.isdigit():
                        ports.add(int(host_port))
    except DockerException as exc:
        logger.warning("读取 Docker 端口映射失败：%s", exc)

    return ports


async def _get_database_allocated_ports() -> set[int]:
    """获取数据库中已分配的端口。

    Returns:
        set[int]: 已分配端口集合
    """
    from sqlalchemy import select

    from app.database import get_session_maker
    from app.models.db_models import BotInstanceDB

    allocated_ports: set[int] = set()
    try:
        async with get_session_maker()() as session:
            result = await session.execute(
                select(BotInstanceDB.port, BotInstanceDB.port_web_ui, BotInstanceDB.port_ws)
            )
            for main_port, web_ui_port, ws_port in result.all():
                allocated_ports.add(main_port)
                if web_ui_port is not None:
                    allocated_ports.add(web_ui_port)
                if ws_port is not None:
                    allocated_ports.add(ws_port)
    except Exception:
        logger.warning("读取数据库端口分配失败", exc_info=True)

    return allocated_ports


async def allocate_port(
    preferred_port: int | None = None,
    excluded_ports: set[int] | None = None,
) -> int:
    """分配可用端口。

    Args:
        preferred_port: 优先使用的端口（可选）
        excluded_ports: 额外排除的端口集合

    Returns:
        int: 可用端口号

    Raises:
        PortAllocationError: 端口不可用时抛出
    """
    from app.core.exceptions import PortAllocationError

    occupied_ports = _get_docker_mapped_ports()
    occupied_ports.update(await _get_database_allocated_ports())
    if excluded_ports:
        occupied_ports.update(excluded_ports)

    if preferred_port is not None:
        if preferred_port in occupied_ports or not _is_host_port_available(preferred_port):
            logger.error("指定端口不可用：%s", preferred_port)
            raise PortAllocationError(preferred_port)
        logger.debug("使用指定端口: %s", preferred_port)
        return preferred_port

    port_range = range(settings.port_range_start, settings.port_range_end + 1)
    for port in port_range:
        if port in occupied_ports:
            continue
        if not _is_host_port_available(port):
            continue
        logger.debug("为新实例分配端口: %s", port)
        return port

    logger.error("端口范围 %s-%s 内无可用端口", settings.port_range_start, settings.port_range_end)
    raise PortAllocationError(0)


def format_container_env(
    qq_number: str,
    instance_id: str,
    protocol: str,
) -> dict[str, str]:
    """格式化容器环境变量。

    Args:
        qq_number: QQ 号码
        instance_id: 实例 ID
        protocol: 机器人协议

    Returns:
        dict: 环境变量字典
    """
    return {
        "QQ_NUMBER": qq_number,
        "INSTANCE_ID": instance_id,
        "PROTOCOL": protocol,
    }
