"""认证 API 测试模块。

测试用户登录、注册、token 刷新等功能。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """测试用户注册。"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "testuser"
    assert data["data"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """测试注册重复用户名。"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }
    
    # 第一次注册
    await client.post("/api/v1/auth/register", json=user_data)
    
    # 第二次注册应该失败
    response = await client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "已存在" in data["message"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """测试登录成功。"""
    # 先注册用户
    user_data = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "testpassword123",
    }
    await client.post("/api/v1/auth/register", json=user_data)
    
    # 登录
    login_data = {
        "username": "loginuser",
        "password": "testpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """测试登录密码错误。"""
    # 先注册用户
    user_data = {
        "username": "wrongpwduser",
        "email": "wrong@example.com",
        "password": "correctpassword",
    }
    await client.post("/api/v1/auth/register", json=user_data)
    
    # 使用错误密码登录
    login_data = {
        "username": "wrongpwduser",
        "password": "wrongpassword",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "密码错误" in data["message"] or "用户名或密码错误" in data["message"]


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """测试刷新 token。"""
    # 注册并登录
    user_data = {
        "username": "refreshtokenuser",
        "email": "refresh@example.com",
        "password": "testpassword123",
    }
    await client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "username": "refreshtokenuser",
        "password": "testpassword123",
    }
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    refresh_token = login_response.json()["data"]["refresh_token"]
    
    # 刷新 token
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """测试获取当前用户信息。"""
    # 注册并登录
    user_data = {
        "username": "currentuser",
        "email": "current@example.com",
        "password": "testpassword123",
    }
    await client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "username": "currentuser",
        "password": "testpassword123",
    }
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    access_token = login_response.json()["data"]["access_token"]
    
    # 获取当前用户
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "currentuser"
    assert data["data"]["email"] == "current@example.com"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """测试无效 token。"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
