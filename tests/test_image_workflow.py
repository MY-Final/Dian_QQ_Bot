"""镜像管理与实例镜像流程回归测试。"""

import pytest
from httpx import AsyncClient

from app.main import app


async def _login_and_get_token(client: AsyncClient, username: str) -> str:
    """注册并登录获取访问令牌。

    Args:
        client: 异步测试客户端
        username: 用户名

    Returns:
        str: access token
    """
    register_payload = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "TestPass123!",
    }
    await client.post("/api/v1/auth/register", json=register_payload)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "TestPass123!"},
    )
    login_data = login_response.json()
    return str(login_data["data"]["access_token"])


@pytest.mark.asyncio
async def test_images_local_requires_authentication(client: AsyncClient) -> None:
    """镜像本地列表接口应要求登录。"""
    response = await client.get("/api/v1/images/local")

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_images_search_supports_custom_registry(client: AsyncClient) -> None:
    """自定义仓库搜索应返回引导结果。"""
    token = await _login_and_get_token(client, "image_search_user")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        "/api/v1/images/search",
        headers=headers,
        params={"query": "napcat", "registry": "registry.example.com"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert data["data"][0]["registry"] == "registry.example.com"


@pytest.mark.asyncio
async def test_instance_update_image_endpoint_returns_updated_payload(
    client: AsyncClient,
) -> None:
    """更新实例镜像接口应返回更新后的镜像信息。"""
    from app.api.v1.instances import get_instance_service

    token = await _login_and_get_token(client, "update_image_user")
    headers = {"Authorization": f"Bearer {token}"}

    class DummyInstanceService:
        """用于覆盖依赖的实例服务。"""

        async def update_instance_image(
            self,
            instance_id: str,
            image_registry: str | None,
            image_repo: str,
            image_tag: str,
            auto_pull: bool,
        ) -> dict[str, object]:
            return {
                "id": instance_id,
                "name": "test-instance",
                "qq_number": "123456789",
                "protocol": "napcat",
                "status": "running",
                "container_name": "dian-napcat-1234abcd",
                "port": 30000,
                "port_web_ui": None,
                "port_ws": 30001,
                "volume_path": "./data/instances/1234abcd/napcat/",
                "description": None,
                "image_repo": (
                    f"{image_registry}/{image_repo}" if image_registry else image_repo
                ),
                "image_tag": image_tag,
                "image_digest": None,
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
                "auto_pull": auto_pull,
            }

    app.dependency_overrides[get_instance_service] = lambda: DummyInstanceService()
    try:
        response = await client.patch(
            "/api/v1/instances/abcd1234/image",
            headers=headers,
            json={
                "image_registry": "registry.example.com",
                "image_repo": "my/napcat",
                "image_tag": "v1.2.3",
                "auto_pull": True,
            },
        )
    finally:
        app.dependency_overrides.pop(get_instance_service, None)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["image_repo"] == "registry.example.com/my/napcat"
    assert data["data"]["image_tag"] == "v1.2.3"


@pytest.mark.asyncio
async def test_instance_recreate_endpoint_returns_instance_data(client: AsyncClient) -> None:
    """按镜像重建接口应返回实例数据。"""
    from app.api.v1.instances import get_instance_service

    token = await _login_and_get_token(client, "recreate_image_user")
    headers = {"Authorization": f"Bearer {token}"}

    class DummyInstanceService:
        """用于覆盖依赖的实例服务。"""

        async def recreate_instance_with_image(
            self,
            instance_id: str,
            auto_pull: bool,
        ) -> dict[str, object]:
            return {
                "id": instance_id,
                "name": "test-instance",
                "qq_number": "123456789",
                "protocol": "napcat",
                "status": "running",
                "container_name": "dian-napcat-1234abcd",
                "port": 30000,
                "port_web_ui": None,
                "port_ws": 30001,
                "volume_path": "./data/instances/1234abcd/napcat/",
                "description": None,
                "image_repo": "mlikiowa/napcat-docker",
                "image_tag": "latest",
                "image_digest": None,
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
                "auto_pull": auto_pull,
            }

    app.dependency_overrides[get_instance_service] = lambda: DummyInstanceService()
    try:
        response = await client.post(
            "/api/v1/instances/abcd1234/recreate",
            headers=headers,
            params={"auto_pull": True},
        )
    finally:
        app.dependency_overrides.pop(get_instance_service, None)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "abcd1234"
    assert data["data"]["status"] == "running"
