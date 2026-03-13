"""数据库模块。

提供异步数据库会话管理和表初始化功能。
使用动态数据库配置（Setup 向导配置的数据库）。
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.db_config_manager import DatabaseConfig as AppConfig
from app.models.db_models import Base, BotInstanceDB

logger = logging.getLogger(__name__)

# 全局数据库配置
_db_config: AppConfig | None = None

# 全局引擎和会话工厂
engine = None
async_session_maker = None


def get_db_config() -> AppConfig:
    """获取数据库配置。

    Returns:
        AppConfig: 数据库配置对象

    Raises:
        RuntimeError: 如果数据库未配置
    """
    global _db_config

    # 优先使用已加载的配置
    if _db_config is not None:
        return _db_config

    # 尝试从文件加载
    _db_config = AppConfig.load()

    if _db_config is None:
        # 如果没有配置，使用默认配置（仅用于首次启动）
        _db_config = AppConfig(
            host="localhost",
            port=5432,
            database="dian_bot",
            username="postgres",
            password="postgres",
        )

    return _db_config


def set_db_config(config: AppConfig) -> None:
    """设置数据库配置并重新初始化引擎。

    Args:
        config: 数据库配置对象
    """
    global _db_config, engine, async_session_maker

    _db_config = config

    # 重新创建引擎和会话工厂
    engine = create_async_engine(
        config.database_url,
        echo=False,
        future=True,
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_engine():  # type: ignore[no-untyped-def]
    """获取数据库引擎。

    Returns:
        异步数据库引擎
    """
    global engine

    if engine is None:
        config = get_db_config()
        engine = create_async_engine(
            config.database_url,
            echo=False,
            future=True,
        )

    return engine


def get_session_maker():  # type: ignore[no-untyped-def]
    """获取会话工厂。

    Returns:
        异步会话工厂
    """
    global async_session_maker

    if async_session_maker is None:
        async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话。

    Yields:
        AsyncSession: 数据库会话
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """初始化数据库表。

    注意：仅在数据库已配置时才会执行初始化。
    首次启动时如果没有配置文件，会跳过初始化，等待 Setup 完成后自动初始化。
    """
    # 检查是否已配置数据库
    if not AppConfig.is_configured():
        logger.warning("数据库配置文件不存在，跳过初始化。请完成 Setup 向导配置数据库。")
        return

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_runtime_schema(conn)

    logger.info("数据库表初始化完成")


async def _ensure_runtime_schema(conn: AsyncConnection) -> None:
    """确保运行时所需列存在。

    Args:
        conn: 数据库连接对象
    """
    await conn.execute(
        text(
            """
            ALTER TABLE bot_instances
            ADD COLUMN IF NOT EXISTS port_web_ui INTEGER
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE bot_instances
            ADD COLUMN IF NOT EXISTS port_ws INTEGER
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE bot_instances
            ADD COLUMN IF NOT EXISTS image_repo VARCHAR(255) NOT NULL
            DEFAULT 'mlikiowa/napcat-docker'
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE bot_instances
            ADD COLUMN IF NOT EXISTS image_tag VARCHAR(100) NOT NULL DEFAULT 'latest'
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE bot_instances
            ADD COLUMN IF NOT EXISTS image_digest VARCHAR(255)
            """
        )
    )


async def save_instance(db_instance: BotInstanceDB) -> BotInstanceDB:
    """保存 Bot 实例到数据库。

    Args:
        db_instance: Bot 实例数据库模型

    Returns:
        BotInstanceDB: 保存后的实例
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
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
    session_maker = get_session_maker()
    async with session_maker() as session:
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
        db_obj.image_repo = db_instance.image_repo
        db_obj.image_tag = db_instance.image_tag
        db_obj.image_digest = db_instance.image_digest
        db_obj.updated_at = db_instance.updated_at

        await session.commit()
        await session.refresh(db_obj)
        # Explicitly return the correct type
        result: BotInstanceDB = db_obj
        return result


async def close_db() -> None:
    """关闭数据库连接。"""
    global engine, async_session_maker

    if engine is not None:
        await engine.dispose()
        engine = None

    async_session_maker = None
