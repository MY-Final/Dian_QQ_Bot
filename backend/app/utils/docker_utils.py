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
import uuid
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_docker_client():
    """获取 Docker 客户端。

    根据当前操作系统自动选择合适的连接方式。
    - Windows: 使用 named pipe (npipe)
    - Linux: 使用 Unix socket (/var/run/docker.sock)

    Returns:
        docker.DockerClient: Docker 客户端实例

    Raises:
        DockerConnectionError: 连接失败时抛出
    """
    import docker
    from app.core.exceptions import DockerConnectionError

    try:
        return docker.from_env()
    except Exception as e:
        logger.error(f"连接 Docker 失败: {e}", exc_info=True)
        raise DockerConnectionError(
            "无法连接到 Docker 守护进程，请确保 Docker Desktop 已启动"
        )


def check_docker_status() -> dict:
    """检查 Docker 守护进程状态。

    支持 Windows 和 Linux 平台。

    Returns:
        dict: Docker 状态信息，包含:
            - running: bool, Docker 是否运行
            - platform: str, 操作系统平台
            - version: str, Docker 版本
            - message: str, 状态消息
    """
    import docker

    try:
        client = docker.from_env()
        info = client.info()
        return {
            "running": True,
            "platform": platform.system().lower(),
            "version": info.get("ServerVersion", "unknown"),
            "message": "Docker 运行正常",
        }
    except docker.errors.DockerException as e:
        logger.warning(f"Docker 不可用: {e}")
        return {
            "running": False,
            "platform": platform.system().lower(),
            "version": None,
            "message": f"Docker 未运行: {str(e)}",
        }
    except Exception as e:
        logger.warning(f"检查 Docker 状态时发生未知错误: {e}")
        return {
            "running": False,
            "platform": platform.system().lower(),
            "version": None,
            "message": f"检查 Docker 状态失败: {str(e)}",
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


def get_docker_volume_bind(volume_path: Path) -> dict:
    """获取 Docker 卷挂载绑定配置。

    根据操作系统自动处理路径格式：
    - Windows: 转换为 Docker 兼容格式
    - Linux: 直接使用路径

    Args:
        volume_path: 主机上的卷路径

    Returns:
        dict: Docker 卷绑定配置
    """
    import os
    import sys
    
    # 获取绝对路径
    host_path = str(volume_path.resolve())
    
    # Windows 特殊处理
    if sys.platform == 'win32':
        # 将反斜杠转换为正斜杠
        host_path = host_path.replace('\\', '/')
        
        # 处理盘符 (C: -> /c)
        if len(host_path) > 1 and host_path[1] == ':':
            drive = host_path[0].lower()
            host_path = f"/{drive}{host_path[2:]}"
    
    return {host_path: {"bind": "/app/config", "mode": "rw"}}


async def allocate_port() -> int:
    """从配置的端口范围中分配可用端口。

    Returns:
        int: 可用端口号

    Raises:
        PortAllocationError: 端口范围内没有可用端口

    Note:
        这是一个简单实现。生产环境应该在数据库中跟踪已分配的端口以避免冲突。
    """
    import random

    port_range = range(settings.port_range_start, settings.port_range_end + 1)
    available_ports = list(port_range)

    if not available_ports:
        from app.core.exceptions import PortAllocationError

        raise PortAllocationError(0)

    selected_port = random.choice(available_ports)
    logger.debug(f"为新实例分配端口: {selected_port}")

    return selected_port


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
