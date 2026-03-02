""" "数据库模块。

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
    """获取数据库会话。"""
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


async def update_instance(db_instance: BotInstanceDB) -> BotInstanceDB:
    """更新 Bot 实例在数据库中的记录。

    使用 SELECT + UPDATE 模式，避免 session.merge 的状态问题。

    Args:
        db_instance: Bot 实例数据库模型

    Returns:
        BotInstanceDB: 更新后的实例
    """
    async with async_session_maker() as session:
        # 从数据库获取最新的对象
        db_obj = await session.get(BotInstanceDB, db_instance.id)
        if db_obj is None:
            raise ValueError(f"Instance {db_instance.id} not found in database")

        # 更新所有字段
        db_obj.name = db_instance.name
        db_obj.qq_number = db_instance.qq_number
        db_obj.protocol = db_instance.protocol
        db_obj.status = db_instance.status
        db_obj.container_name = db_instance.container_name
        db_obj.port = db_instance.port
        db_obj.volume_path = db_instance.volume_path
        db_obj.description = db_instance.description
        db_obj.updated_at = db_instance.updated_at

        await session.commit()
        await session.refresh(db_obj)
        return db_obj


async def close_db() -> None:
    """关闭数据库连接。"""
    await engine.dispose()
