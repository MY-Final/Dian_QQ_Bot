"""Bot 异常模块。

定义项目使用的所有自定义异常类型。
"""

from typing import Optional


class BotError(Exception):
    """Bot 错误的基类。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BotNotFoundError(BotError):
    """当 Bot 实例未找到时抛出。"""

    def __init__(self, instance_id: str) -> None:
        super().__init__(f"Bot 实例 '{instance_id}' 未找到")
        self.instance_id = instance_id


class BotAlreadyExistsError(BotError):
    """当 Bot 实例已存在时抛出。"""

    def __init__(self, instance_id: str) -> None:
        super().__init__(f"Bot 实例 '{instance_id}' 已存在")
        self.instance_id = instance_id


class BotStartError(BotError):
    """当 Bot 启动失败时抛出。"""

    def __init__(self, instance_id: str, exit_code: Optional[int] = None) -> None:
        message = f"启动 Bot 实例 '{instance_id}' 失败"
        if exit_code is not None:
            message += f" (退出码: {exit_code})"
        super().__init__(message)
        self.instance_id = instance_id
        self.exit_code = exit_code


class BotStopError(BotError):
    """当 Bot 停止失败时抛出。"""

    def __init__(self, instance_id: str, exit_code: Optional[int] = None) -> None:
        message = f"停止 Bot 实例 '{instance_id}' 失败"
        if exit_code is not None:
            message += f" (退出码: {exit_code})"
        super().__init__(message)
        self.instance_id = instance_id
        self.exit_code = exit_code


class BotDeleteError(BotError):
    """当 Bot 删除失败时抛出。"""

    def __init__(self, instance_id: str) -> None:
        super().__init__(f"删除 Bot 实例 '{instance_id}' 失败")
        self.instance_id = instance_id


class DockerConnectionError(BotError):
    """当 Docker 守护进程连接失败时抛出。"""

    def __init__(self, message: str = "无法连接到 Docker 守护进程") -> None:
        super().__init__(message)


class PortAllocationError(BotError):
    """当端口分配失败时抛出。"""

    def __init__(self, port: int) -> None:
        super().__init__(f"分配端口 {port} 失败")
        self.port = port


class SetupError(BotError):
    """系统初始化流程异常基类。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DatabaseConnectionError(SetupError):
    """数据库连接失败异常。"""

    def __init__(self) -> None:
        super().__init__("数据库连接失败，请检查配置后重试")


class DatabaseInitializationError(SetupError):
    """数据库初始化失败异常。"""

    def __init__(self) -> None:
        super().__init__("数据库表创建失败，请稍后重试")


class AdminCreationError(SetupError):
    """管理员创建失败异常。"""

    def __init__(self, message: str = "创建管理员失败，请稍后重试") -> None:
        super().__init__(message)


class AuthError(BotError):
    """认证流程异常基类。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidCredentialsError(AuthError):
    """用户凭证无效异常。"""

    def __init__(self) -> None:
        super().__init__("用户名或密码错误")


class UserAlreadyExistsError(AuthError):
    """用户已存在异常。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class TokenValidationError(AuthError):
    """Token 校验失败异常。"""

    def __init__(self) -> None:
        super().__init__("Token 无效或已过期")


class AuthUserNotFoundError(AuthError):
    """认证用户不存在异常。"""

    def __init__(self) -> None:
        super().__init__("用户不存在")
