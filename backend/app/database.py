"""数据库模块。

提供异步数据库会话管理和表初始化功能。
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.db_models import BotInstanceDB, Base


# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# 创建会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话。

    用法:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...

    Yields:
        AsyncSession: 数据库会话
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """初始化数据库表。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_instance(db_instance: BotInstanceDB) -> BotInstanceDB:
    """保存 Bot 实例到数据库。

    Args:
        db_instance: Bot 实例数据库模型

    Returns:
        BotInstanceDB: 保存后的实例
    """
    async with async_session_maker() as session:
        session.add(db_instance)
        await session.commit()
        await session.refresh(db_instance)
        return db_instance


async def close_db() -> None:
    """关闭数据库连接。"""
    await engine.dispose()
