"""Dian QQ Bot 后端启动入口模块。

使用 uvicorn 启动 FastAPI 应用。
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn  # noqa: E402

from app.core.config import settings  # noqa: E402

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def main() -> None:
    """启动 FastAPI 应用服务器。"""
    logger.info("=" * 60)
    logger.info("Dian QQ Bot - 启动中...")
    logger.info(f"应用名称：{settings.app_name}")
    logger.info(f"调试模式：{settings.debug}")
    logger.info(f"主机：{settings.host}:{settings.port}")
    logger.info(f"日志级别：{settings.log_level}")
    logger.info("=" * 60)
    logger.info("点点在看着你呢～ 💕")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
