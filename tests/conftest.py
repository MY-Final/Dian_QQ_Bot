"""测试配置和共享夹具。

提供测试所需的数据库、客户端和模拟对象。
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 添加 backend 目录到 Python 路径
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database import Base, get_db
from app.main import app


# 测试数据库 URL（使用内存 SQLite 或测试 PostgreSQL）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环。

    Yields:
        asyncio.AbstractEventLoop: 事件循环实例
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """创建测试数据库引擎。

    Yields:
        测试数据库引擎
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session_maker(test_engine):
    """创建测试数据库会话工厂。

    Args:
        test_engine: 测试数据库引擎

    Yields:
        测试会话工厂
    """
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield async_session_maker


@pytest_asyncio.fixture(scope="function")
async def client(test_session_maker) -> AsyncGenerator[AsyncClient, None]:
    """创建测试 HTTP 客户端。

    Args:
        test_session_maker: 测试会话工厂

    Yields:
        AsyncClient: HTTP 测试客户端
    """

    # 重写数据库依赖
    async def override_get_db():
        async with test_session_maker() as session:
            try:
                yield session
            finally:
                pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # 清除依赖重写
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict:
    """示例用户数据。

    Returns:
        dict: 用户测试数据
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
def sample_bot_data() -> dict:
    """示例 Bot 实例数据。

    Returns:
        dict: Bot 实例测试数据
    """
    return {
        "name": "test-bot",
        "qq_number": "123456789",
        "protocol": "napcat",
        "description": "测试 Bot",
    }
