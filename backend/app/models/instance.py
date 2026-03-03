"""Bot 实例数据模型模块。

包含 Pydantic 模型，用于 API 请求/响应验证。
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProtocolType(str, Enum):
    """Bot 协议类型枚举。"""

    NAPCAT = "napcat"
    LLONEBOT = "llonebot"
    CUSTOM = "custom"


class InstanceStatus(str, Enum):
    """Bot 实例状态枚举。"""

    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class InstanceCreate(BaseModel):
    """创建 Bot 实例的请求模型。"""

    name: str = Field(..., min_length=1, max_length=100, description="实例名称")
    qq_number: str = Field(..., min_length=5, max_length=15, description="QQ 号码")
    protocol: ProtocolType = Field(default=ProtocolType.NAPCAT, description="Bot 协议")
    description: Optional[str] = Field(None, max_length=500, description="可选描述")
    # 端口配置
    port_web_ui: Optional[int] = Field(
        None, ge=1024, le=65535, description="Web UI 端口（可选）"
    )
    port_http: Optional[int] = Field(
        None, ge=1024, le=65535, description="HTTP API 端口（可选，不指定则自动分配）"
    )
    port_ws: Optional[int] = Field(
        None,
        ge=1024,
        le=65535,
        description="WebSocket 端口（可选，不指定则使用 HTTP+1）",
    )
    # NapCat 环境变量配置
    napcat_uid: Optional[int] = Field(None, ge=0, description="NAPCAT_UID 用户ID")
    napcat_gid: Optional[int] = Field(None, ge=0, description="NAPCAT_GID 组ID")


class InstanceResponse(BaseModel):
    """Bot 实例的响应模型。"""

    class Config:
        # 即使字段为 None 也要包含在响应中
        extra = "ignore"

    id: str = Field(..., description="实例唯一 ID")
    name: str = Field(..., description="实例名称")
    qq_number: str = Field(..., description="QQ 号码")
    protocol: ProtocolType = Field(..., description="Bot 协议")
    status: InstanceStatus = Field(..., description="实例状态")
    container_name: str = Field(..., description="Docker 容器名称")
    port: int = Field(..., description="HTTP 端口")
    port_web_ui: Optional[int] = Field(default=None, description="Web UI 端口")
    port_ws: Optional[int] = Field(default=None, description="WebSocket 端口")
    volume_path: str = Field(..., description="卷挂载路径")
    description: Optional[str] = Field(default=None, description="可选描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")


class InstanceStart(BaseModel):
    """启动 Bot 实例的请求模型。"""

    instance_id: str = Field(..., description="要启动的实例 ID")


class InstanceStop(BaseModel):
    """停止 Bot 实例的请求模型。"""

    instance_id: str = Field(..., description="要停止的实例 ID")


class InstanceLogs(BaseModel):
    """Bot 实例日志模型。"""

    instance_id: str = Field(..., description="实例 ID")
    logs: str = Field(..., description="容器日志")
    tail: int = Field(default=100, description="获取的日志行数")


# ============ 系统初始化相关模型 ============


class DatabaseConfig(BaseModel):
    """数据库配置模型。"""

    host: str = Field(..., description="数据库主机地址")
    port: int = Field(..., ge=1, le=65535, description="数据库端口")
    database: str = Field(..., description="数据库名称")
    username: str = Field(..., description="数据库用户名")
    password: str = Field(..., description="数据库密码")


class AdminConfig(BaseModel):
    """管理员配置模型。"""

    username: str = Field(..., min_length=3, max_length=50, description="管理员用户名")
    email: str = Field(..., description="管理员邮箱")
    password: str = Field(..., min_length=6, description="登录密码")


class SystemInitializeRequest(BaseModel):
    """系统初始化请求模型。"""

    database: DatabaseConfig = Field(..., description="数据库配置")
    admin: AdminConfig = Field(..., description="管理员配置")


class SystemInitializeResponse(BaseModel):
    """系统初始化响应模型。"""

    initialized: bool = Field(..., description="是否已初始化")
    message: str = Field(..., description="提示信息")
