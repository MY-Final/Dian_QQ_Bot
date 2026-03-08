"""Setup 流程回归测试。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_setup_status_without_saved_config_returns_not_initialized(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """未保存数据库配置时，初始化状态应为 False。"""
    monkeypatch.setattr("app.services.setup_service.AppConfig.load", lambda: None)

    response = await client.get("/api/v1/setup/status")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["initialized"] is False


@pytest.mark.asyncio
async def test_create_admin_password_mismatch_returns_400(client: AsyncClient) -> None:
    """管理员密码不一致时应直接失败。"""
    payload = {
        "admin": {
            "username": "admin_user",
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "confirm_password": "AdminPass123!x",
        },
        "database": {
            "host": "127.0.0.1",
            "port": 5432,
            "database": "dian_bot",
            "username": "postgres",
            "password": "postgres",
        },
    }

    response = await client.post("/api/v1/setup/create-admin", json=payload)

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "密码" in data["message"]
