"""安全加固相关回归测试。"""

import pytest
from httpx import AsyncClient

from app.utils import docker_utils


@pytest.mark.asyncio
async def test_auth_me_requires_authorization_header(client: AsyncClient) -> None:
    """未提供 Authorization 头时应返回 401。"""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "认证头" in data["message"]


@pytest.mark.asyncio
async def test_auth_me_rejects_invalid_bearer_format(client: AsyncClient) -> None:
    """无效 Bearer 格式应被拒绝。"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Token abc"},
    )

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "认证头格式" in data["message"]


@pytest.mark.asyncio
async def test_login_internal_error_does_not_leak_details(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """登录异常应返回通用错误，避免泄露内部细节。"""
    register_data = {
        "username": "security_user",
        "email": "security@example.com",
        "password": "Security123!",
    }
    await client.post("/api/v1/auth/register", json=register_data)

    def _raise_runtime_error(_: str, __: str) -> bool:
        raise RuntimeError("db secret leaked")

    monkeypatch.setattr("app.api.v1.auth.verify_password", _raise_runtime_error)

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "security_user", "password": "Security123!"},
    )

    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert "稍后重试" in data["message"]
    assert "db secret leaked" not in data["message"]


@pytest.mark.asyncio
async def test_allocate_port_skips_conflicts(monkeypatch: pytest.MonkeyPatch) -> None:
    """端口分配应跳过 Docker/数据库/主机冲突端口。"""

    async def _mock_database_allocated_ports() -> set[int]:
        return {35001}

    monkeypatch.setattr(docker_utils, "_get_docker_mapped_ports", lambda: {35000})
    monkeypatch.setattr(docker_utils, "_get_database_allocated_ports", _mock_database_allocated_ports)
    monkeypatch.setattr(
        docker_utils,
        "_is_host_port_available",
        lambda port: port not in {35002},
    )

    original_start = docker_utils.settings.port_range_start
    original_end = docker_utils.settings.port_range_end

    docker_utils.settings.port_range_start = 35000
    docker_utils.settings.port_range_end = 35003

    try:
        allocated_port = await docker_utils.allocate_port()
    finally:
        docker_utils.settings.port_range_start = original_start
        docker_utils.settings.port_range_end = original_end

    assert allocated_port == 35003


@pytest.mark.asyncio
async def test_system_init_uses_database_state(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """无数据库配置时应明确返回未初始化。"""

    monkeypatch.setattr("app.api.v1.system.AppConfig.load", lambda: None)

    response = await client.get("/api/v1/system/init")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["initialized"] is False
