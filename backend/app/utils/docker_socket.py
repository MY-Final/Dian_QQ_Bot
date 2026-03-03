"""Docker Socket 工具模块。

自动检测和处理不同平台的 Docker Socket 路径。
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_docker_socket_path() -> str:
    """获取 Docker Socket 路径。
    
    根据操作系统自动返回合适的 Docker Socket 路径：
    - Linux: unix:///var/run/docker.sock
    - Windows: npipe:////./pipe/docker_engine
    - macOS: unix:///var/run/docker.sock
    
    Returns:
        str: Docker Socket URL
    """
    # 检查环境变量（优先级最高）
    docker_host = os.environ.get('DOCKER_HOST')
    if docker_host:
        logger.info(f"使用环境变量 DOCKER_HOST: {docker_host}")
        return docker_host
    
    # 根据平台返回默认值
    if sys.platform == 'win32':
        # Windows 使用 named pipe
        socket_path = "npipe:////./pipe/docker_engine"
        logger.info(f"Windows 平台，使用 named pipe: {socket_path}")
        return socket_path
    else:
        # Linux/macOS 使用 Unix socket
        socket_path = "unix:///var/run/docker.sock"
        logger.info(f"Unix 平台，使用 socket: {socket_path}")
        return socket_path


def is_docker_socket_available() -> bool:
    """检查 Docker Socket 是否可用。
    
    Returns:
        bool: Docker Socket 是否可用
    """
    import docker
    
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception as e:
        logger.warning(f"Docker Socket 不可用：{e}")
        return False


def get_platform_info() -> dict:
    """获取平台信息。
    
    Returns:
        dict: 平台信息字典
    """
    import platform
    
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "platform": sys.platform,
    }
