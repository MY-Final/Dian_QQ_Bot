"""Bot instance models module."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProtocolType(str, Enum):
    """Bot protocol types."""

    NAPCAT = "napcat"
    LLONEBOT = "llonebot"
    CUSTOM = "custom"


class InstanceStatus(str, Enum):
    """Bot instance status."""

    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class InstanceCreate(BaseModel):
    """Schema for creating a Bot instance."""

    name: str = Field(..., min_length=1, max_length=100, description="Instance name")
    qq_number: str = Field(..., min_length=5, max_length=15, description="QQ number")
    protocol: ProtocolType = Field(
        default=ProtocolType.NAPCAT, description="Bot protocol"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Optional description"
    )


class InstanceResponse(BaseModel):
    """Schema for Bot instance response."""

    id: str = Field(..., description="Instance unique ID")
    name: str = Field(..., description="Instance name")
    qq_number: str = Field(..., description="QQ number")
    protocol: ProtocolType = Field(..., description="Bot protocol")
    status: InstanceStatus = Field(..., description="Instance status")
    container_name: str = Field(..., description="Docker container name")
    port: int = Field(..., description="Exposed port")
    volume_path: str = Field(..., description="Volume mount path")
    description: Optional[str] = Field(None, description="Optional description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class InstanceStart(BaseModel):
    """Schema for starting a Bot instance."""

    instance_id: str = Field(..., description="Instance ID to start")


class InstanceStop(BaseModel):
    """Schema for stopping a Bot instance."""

    instance_id: str = Field(..., description="Instance ID to stop")


class InstanceLogs(BaseModel):
    """Schema for Bot instance logs."""

    instance_id: str = Field(..., description="Instance ID")
    logs: str = Field(..., description="Container logs")
    tail: int = Field(default=100, description="Number of lines to fetch")
