"""系统初始化业务服务模块。"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.db_config_manager import DatabaseConfig as AppConfig
from app.core.exceptions import (
    AdminCreationError,
    DatabaseConnectionError,
    DatabaseInitializationError,
    SetupError,
)
from app.database import Base, _ensure_runtime_schema, set_db_config
from app.models.settings import SystemSetting  # noqa: F401
from app.models.user import User  # noqa: F401
from app.utils.security import hash_password

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SetupStatusResult:
    """初始化状态结果。"""

    initialized: bool


class SetupService:
    """系统初始化业务服务。"""

    @staticmethod
    def _build_database_url(
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ) -> str:
        """构建数据库 URL。

        Args:
            host: 主机地址
            port: 端口
            database: 数据库名
            username: 用户名
            password: 密码

        Returns:
            str: 数据库连接 URL
        """
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        return (
            f"postgresql+asyncpg://{encoded_username}:{encoded_password}"
            f"@{host}:{port}/{database}"
        )

    async def get_setup_status(
        self,
        host: str | None,
        port: int | None,
        database: str | None,
        username: str | None,
        password: str | None,
    ) -> SetupStatusResult:
        """检查初始化状态。

        Args:
            host: 数据库主机
            port: 数据库端口
            database: 数据库名称
            username: 数据库用户名
            password: 数据库密码

        Returns:
            SetupStatusResult: 初始化状态结果

        Raises:
            SetupError: 状态检查失败时抛出
        """
        if (
            host is not None
            and port is not None
            and database is not None
            and username is not None
            and password is not None
        ):
            database_url = self._build_database_url(
                host=host,
                port=port,
                database=database,
                username=username,
                password=password,
            )
        else:
            saved_config = AppConfig.load()
            if saved_config is None:
                return SetupStatusResult(initialized=False)
            database_url = saved_config.database_url

        temp_engine = create_async_engine(database_url, echo=False, future=True)
        try:
            async with temp_engine.begin() as conn:
                result = await conn.execute(
                    text("SELECT value FROM system_settings WHERE key = 'initialized'")
                )
                row = result.first()
                is_initialized = row is not None and row[0] == "true"
            return SetupStatusResult(initialized=is_initialized)
        except Exception:
            logger.warning("检查初始化状态失败", exc_info=True)
            return SetupStatusResult(initialized=False)
        finally:
            await temp_engine.dispose()

    async def test_database_connection(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ) -> None:
        """测试数据库连接。

        Args:
            host: 数据库主机
            port: 数据库端口
            database: 数据库名称
            username: 用户名
            password: 密码

        Raises:
            DatabaseConnectionError: 连接失败时抛出
        """
        database_url = self._build_database_url(host, port, database, username, password)
        temp_engine = create_async_engine(database_url, echo=False, future=True, pool_pre_ping=True)
        try:
            async with temp_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as exc:
            logger.error("数据库连接测试失败: %s", exc, exc_info=True)
            raise self._map_database_connection_error(exc) from exc
        finally:
            await temp_engine.dispose()

    async def initialize_database(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ) -> None:
        """初始化数据库表。

        Args:
            host: 数据库主机
            port: 数据库端口
            database: 数据库名称
            username: 用户名
            password: 密码

        Raises:
            DatabaseInitializationError: 初始化失败时抛出
        """
        database_url = self._build_database_url(host, port, database, username, password)
        temp_engine = create_async_engine(database_url, echo=False, future=True)
        retry_count = 3
        retry_interval_seconds = 1.0
        last_exception: Exception | None = None

        try:
            for attempt in range(1, retry_count + 1):
                try:
                    async with temp_engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)
                        await _ensure_runtime_schema(conn)
                    return
                except Exception as exc:
                    last_exception = exc
                    is_last_attempt = attempt == retry_count
                    if is_last_attempt:
                        break
                    logger.warning(
                        "数据库初始化第 %s 次尝试失败，%s 秒后重试",
                        attempt,
                        retry_interval_seconds,
                        exc_info=True,
                    )
                    await asyncio.sleep(retry_interval_seconds)

            logger.error("数据库表初始化失败", exc_info=True)
            if last_exception is None:
                raise DatabaseInitializationError()
            raise self._map_database_initialization_error(last_exception) from last_exception
        finally:
            await temp_engine.dispose()

    async def create_admin(
        self,
        admin_username: str,
        admin_email: str,
        admin_password: str,
        confirm_password: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ) -> None:
        """创建管理员并完成初始化。

        Args:
            admin_username: 管理员用户名
            admin_email: 管理员邮箱
            admin_password: 管理员密码
            confirm_password: 确认密码
            host: 数据库主机
            port: 数据库端口
            database: 数据库名称
            username: 数据库用户名
            password: 数据库密码

        Raises:
            AdminCreationError: 管理员创建失败时抛出
            SetupError: 保存系统配置失败时抛出
        """
        if admin_password != confirm_password:
            raise AdminCreationError("两次输入的密码不一致")

        database_url = self._build_database_url(host, port, database, username, password)
        temp_engine = create_async_engine(database_url, echo=False, future=True)

        try:
            password_hash = hash_password(admin_password)
            async with temp_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                await _ensure_runtime_schema(conn)

                user_result = await conn.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": admin_username},
                )
                existing_user = user_result.first()

                if existing_user:
                    await conn.execute(
                        text(
                            """
                            UPDATE users
                            SET email = :email,
                                password_hash = :password_hash,
                                role = :role,
                                last_login = NULL
                            WHERE username = :username
                            """
                        ),
                        {
                            "username": admin_username,
                            "email": admin_email,
                            "password_hash": password_hash,
                            "role": "admin",
                        },
                    )
                else:
                    await conn.execute(
                        text(
                            """
                            INSERT INTO users (id, username, email, password_hash, role, created_at)
                            VALUES (:id, :username, :email, :password_hash, :role, NOW())
                            """
                        ),
                        {
                            "id": uuid.uuid4(),
                            "username": admin_username,
                            "email": admin_email,
                            "password_hash": password_hash,
                            "role": "admin",
                        },
                    )

                await conn.execute(
                    text(
                        """
                        INSERT INTO system_settings (key, value, description, updated_at)
                        VALUES ('initialized', 'true', '系统初始化完成标志', NOW())
                        ON CONFLICT (key)
                        DO UPDATE SET
                            value = EXCLUDED.value,
                            description = EXCLUDED.description,
                            updated_at = EXCLUDED.updated_at
                        """
                    )
                )
        except AdminCreationError:
            raise
        except SQLAlchemyError as exc:
            logger.error("创建管理员失败", exc_info=True)
            raise self._map_admin_creation_error(exc) from exc
        except Exception as exc:
            logger.error("创建管理员失败", exc_info=True)
            raise self._map_admin_creation_error(exc) from exc
        finally:
            await temp_engine.dispose()

        app_db_config = AppConfig(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
        )
        if not app_db_config.save():
            raise SetupError("数据库配置保存失败，请检查 data 目录权限")

        set_db_config(app_db_config)

    @staticmethod
    def _map_admin_creation_error(exc: Exception) -> AdminCreationError:
        """将底层异常映射为可读的管理员创建异常。

        Args:
            exc: 原始异常

        Returns:
            AdminCreationError: 映射后的业务异常
        """
        error_text = str(exc)
        error_type = exc.__class__.__name__

        if "InvalidPasswordError" in error_type or "password authentication failed" in error_text:
            return AdminCreationError("数据库认证失败，请检查数据库用户名或密码")

        if (
            "UndefinedTableError" in error_type
            or 'relation "system_settings" does not exist' in error_text
        ):
            return AdminCreationError("数据库表未初始化，请先执行“初始化数据库表”步骤")

        if "ConnectionRefusedError" in error_type or "connect" in error_text.lower():
            return AdminCreationError("数据库连接失败，请检查地址、端口和网络可达性")

        return AdminCreationError()

    @staticmethod
    def _map_database_connection_error(exc: Exception) -> DatabaseConnectionError:
        """将底层异常映射为可读的数据库连接异常。

        Args:
            exc: 原始异常

        Returns:
            DatabaseConnectionError: 可读异常信息
        """
        error_text = str(exc)
        lower_error_text = error_text.lower()

        if "password authentication failed" in lower_error_text:
            return DatabaseConnectionError("数据库认证失败，请检查用户名或密码")

        if (
            "name or service not known" in lower_error_text
            or "could not translate host name" in lower_error_text
        ):
            return DatabaseConnectionError(
                "数据库主机无法解析。Docker 内置模式请使用 host=postgres，外部数据库请填写真实地址"
            )

        if "connection refused" in lower_error_text:
            return DatabaseConnectionError("数据库连接被拒绝，请检查数据库服务是否启动")

        if "timeout" in lower_error_text:
            return DatabaseConnectionError("数据库连接超时，请检查网络和防火墙设置")

        return DatabaseConnectionError()

    @staticmethod
    def _map_database_initialization_error(
        exc: Exception,
    ) -> DatabaseInitializationError:
        """将底层异常映射为可读的数据库初始化异常。

        Args:
            exc: 原始异常

        Returns:
            DatabaseInitializationError: 可读异常信息
        """
        error_text = str(exc)
        lower_error_text = error_text.lower()

        if "permission denied" in lower_error_text:
            return DatabaseInitializationError(
                "数据库权限不足，无法创建表，请使用具备建表权限的账号"
            )

        if 'relation "bot_instances" does not exist' in lower_error_text:
            return DatabaseInitializationError(
                "实例表不存在，请重试初始化；若仍失败请清理旧数据库后重建"
            )

        if "connection refused" in lower_error_text:
            return DatabaseInitializationError("初始化时数据库连接被拒绝，请确认 postgres 容器正常")

        if "timeout" in lower_error_text:
            return DatabaseInitializationError("初始化时数据库连接超时，请稍后重试")

        return DatabaseInitializationError(f"数据库表创建失败：{error_text[:160]}")
