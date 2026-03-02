# Dian_QQ_Bot - 开发指南

> QQ Bot 管理平台 - 献给我的点点 🐱❤️

**项目定位**：个人纪念项目 + 开源工具，优先级顺序：**可读性 > 正确性 > 性能 > 简洁性**  
**目标用户**：自己用 + 愿意折腾 Docker 的小众 QQ Bot 爱好者

## ★★★ 父约束 - 最高优先级红线（所有代码必须遵守） ★★★

这些是"不可逾越"的规则，AI 或任何人写代码时都必须严格执行，违反即打回重写。

1. **必须使用类型提示**  
   所有函数、方法、类属性、返回值**全部**加类型注解（typing + pydantic），不允许出现 `Any` 滥用。

2. **命名风格铁律**  
   - 类：PascalCase  
   - 函数/方法/变量：snake_case  
   - 常量：UPPER_CASE_WITH_UNDERSCORE  
   - 私有成员：_single_leading_underscore  
   - Bot 实例相关一律带 `instance` 或 `bot_instance` 字样（避免 id、bot 等过于泛化命名）

3. **异常处理强制要求**  
   - 所有可能失败的操作必须抛出**自定义异常**（继承自 BotError）  
   - 禁止使用裸 `except:`  
   - 所有 public 方法必须在 docstring 中声明 Raises

4. **日志使用规范**  
   - 必须使用 `logger = logging.getLogger(__name__)`  
   - 禁止 print()  
   - 重要操作必须有 info / debug / error 日志  
   - 异常发生时必须带 `exc_info=True`

5. **依赖注入 & 服务拆分**  
   - 业务逻辑必须放在 `services/` 目录下的 Service 类中  
   - FastAPI 路由只负责接收请求、校验、调用 service、返回响应  
   - 所有 service 必须支持依赖注入（通过 Depends）

6. **Docker 相关约束**  
   - 容器名称格式必须是：`dian-{protocol}-{short_uuid8}`  
   - 卷挂载路径格式：`./data/instances/{instance_id}/{protocol}/`  
   - 端口分配必须从配置文件范围中动态获取，且记录到数据库  
   - 禁止直接执行 `docker` 命令，必须全部通过 `docker-py` SDK

7. **代码风格强制工具**  
   - black + isort（line-length=100）  
   - flake8 + mypy（严格模式）  
   - pytest + coverage > 70%（核心 service 必须接近 90%）

8. **文档字符串要求**  
   - 所有 public 函数/类/方法必须写 Google 风格 docstring  
   - 必须包含 Args / Returns / Raises 三段

9. **禁止事项**  
   - 禁止全局变量（除 settings 单例）  
   - 禁止魔法数字（全部抽成常量）  
   - 禁止在 API 层写业务逻辑  
   - 禁止中文变量名、路径名、文件名（英文优先）

10. **点点情感约束**  
    - 所有重要日志、异常消息、API 响应中可适当加入温馨提示（可选，但鼓励）  
    - README、docstring、注释中可偶尔出现"献给点点""点点在看着呢"等字样

---

## ★ Git 工作流规范（必须遵守） ★

所有新功能、修复、优化都**禁止直接在 main 分支上开发**。

### 标准流程（GitHub Flow 风格，适合本项目）

1. **创建功能分支**  
   从 main 分支拉取最新代码后，创建新分支。  
   分支命名规范（强制）：
   - 功能/特性：`feature/xxx` 或 `feat/xxx`
     - 示例：`feature/create-bot-instance`, `feat/add-log-viewer`
   - 修复 bug：`fix/xxx`
     - 示例：`fix/docker-port-conflict`, `fix/napcat-login-failed`
   - 文档/测试/重构：`docs/xxx`, `test/xxx`, `refactor/xxx`
   - 临时实验：`experiment/xxx` 或 `spike/xxx`（完成后可删除）

   命令示例：
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/add-instance-detail-page
   ```

2. **开发 & 提交**  
   在分支上开发，频繁 commit（小步提交）  
   commit 信息规范（英文优先，简洁清晰）：
   ```
   feat: add bot instance creation API
   fix: resolve container name conflict in napcat manager
   docs: update installation guide for docker
   refactor: extract docker utils from napcat manager
   ```

3. **完成 & 测试**  
   - 本地跑通所有测试（pytest）
   - 手动测试新功能（创建/启动/停止 Bot 等）
   - 确保 main 分支能正常运行

4. **创建 Pull Request**  
   - push 分支到远程：`git push origin feature/xxx`
   - 在 GitHub 上创建 PR（从 feature/xxx → main）
   - PR 标题：跟 commit 类似
   - PR 描述：写清楚做了什么、为什么、怎么测试

5. **合并**  
   - 使用 Squash and merge 或 Rebase and merge（推荐 Squash，保持 main 历史干净）
   - 合并后删除远程分支

### 禁止行为

- 禁止直接 push 到 main（除非紧急 hotfix，且需事后补 PR）
- 禁止 force push 到 main
- 禁止在 main 上直接修改文件

---

## 项目概述

基于 Docker 的多实例 QQ Bot 管理平台，支持 NapCat 协议。

- **编程语言**: Python 3.11+
- **前端**: Vue + shadcn-vue + Tailwind (计划中)
- **容器**: 每个 Bot 独立 Docker 容器

## 构建与运行命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python main.py

# 使用指定配置运行
python main.py --config config.yaml

# Docker 构建
docker build -t dian-qq-bot .

# Docker Compose
docker-compose up -d

# 运行测试
pytest

# 运行指定测试
pytest tests/test_bot.py -v

# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html

# 代码检查
flake8 src/

# 类型检查
mypy src/

# 代码格式化
black src/
isort src/
```

---

## 项目结构（推荐版 - 更清晰）

```
Dian_QQ_Bot/
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 应用入口
│   ├── api/
│   │   └── v1/
│   │       └── bots.py          # Bot 相关路由
│   ├── core/
│   │   ├── config.py            # Settings (Pydantic BaseSettings)
│   │   └── exceptions.py        # 所有自定义异常
│   ├── models/
│   │   └── bot.py               # Pydantic 模型 + ORM（如果用）
│   ├── services/
│   │   └── bot_service.py       # 核心业务逻辑
│   ├── managers/
│   │   └── napcat_manager.py    # Docker 容器具体操作
│   ├── utils/
│   │   ├── logger.py
│   │   └── docker_utils.py
│   └── database/
│       └── session.py           # 数据库会话
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── data/                        # .gitignore
│   └── instances/               # Bot 实例卷目录
├── logs/                        # .gitignore
├── docs/                        # 额外文档
├── scripts/                     # 辅助脚本
├── .env
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml               # black, isort, mypy, pytest 配置
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 代码风格示例

### 命名规范

```python
class BotManager:                   # 类名使用 PascalCase
    def __init__(self):
        self.instance_id = None     # 变量使用 snake_case
        
def create_bot_instance(config: dict) -> BotInstance:
    """创建新的 Bot 实例。"""
    pass

MAX_RETRY_COUNT = 3               # 常量使用 UPPER_CASE
DEFAULT_TIMEOUT = 30
```

### 导入顺序

```python
# 1. 标准库
import os
import sys
from pathlib import Path

# 2. 第三方包
import requests
from pydantic import BaseModel

# 3. 本地模块
from src.models.bot import BotConfig
from src.utils.logger import get_logger
```

### 类型提示

```python
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class BotInstance:
    id: str
    name: str
    status: str
    config: Dict[str, Any]

def start_bot(instance_id: str, timeout: Optional[int] = None) -> BotInstance:
    """启动 Bot 实例。
    
    Args:
        instance_id: Bot 的唯一标识符
        timeout: 可选的超时时间（秒）
        
    Returns:
        更新状态后的 BotInstance
        
    Raises:
        BotNotFoundError: 如果 instance_id 不存在
        BotStartError: 如果启动 Bot 失败
    """
    pass
```

### 错误处理

```python
# 自定义异常
class BotError(Exception):
    """Bot 错误的基类。"""
    pass

class BotNotFoundError(BotError):
    """当 Bot 实例未找到时抛出。"""
    pass

class BotStartError(BotError):
    """当 Bot 启动失败时抛出。"""
    def __init__(self, message: str, exit_code: int):
        super().__init__(message)
        self.exit_code = exit_code

# 使用示例
try:
    bot = start_bot(instance_id)
except BotNotFoundError:
    logger.error(f"Bot {instance_id} 未找到")
    raise
except BotStartError as e:
    logger.error(f"启动 Bot 失败: {e}, 退出码: {e.exit_code}")
    raise
```

### 日志记录

```python
import logging

logger = logging.getLogger(__name__)
logger.info("启动 Bot 实例")
logger.debug(f"配置: {config}")
logger.warning("检测到高内存使用")
logger.error("连接 Docker 守护进程失败", exc_info=True)
```

---

## 配置示例

```python
# config.py
from pydantic import BaseSettings, Field
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "Dian QQ Bot"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    docker_socket: Path = Field(default="/var/run/docker.sock", env="DOCKER_SOCKET")
    container_prefix: str = Field(default="dian-bot", env="CONTAINER_PREFIX")
    database_url: str = Field(default="sqlite:///./data/bot.db", env="DATABASE_URL")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 测试最佳实践

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    """创建测试客户端。"""
    return TestClient(app)
```

```python
# test_bot_service.py
import pytest
from unittest.mock import patch
from src.services.bot_service import BotService
from src.models.bot import BotInstance

class TestBotService:
    @pytest.fixture
    def service(self):
        return BotService()
    
    def test_create_bot_instance(self, service, mock_docker):
        """测试创建新的 Bot 实例。"""
        config = {"name": "test-bot", "qq": "123456789"}
        result = service.create_instance(config)
        assert isinstance(result, BotInstance)
        assert result.name == "test-bot"
    
    def test_start_bot_instance_not_found(self, service):
        """测试启动不存在的 Bot 会抛出错误。"""
        with pytest.raises(BotNotFoundError):
            service.start_instance("non-existent-id")
```

---

## API 开发示例

```python
# bot_routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from src.models.bot import BotInstance, BotConfig
from src.services.bot_service import BotService

router = APIRouter(prefix="/bots", tags=["bots"])

def get_bot_service() -> BotService:
    """依赖注入获取 BotService 实例。"""
    return BotService()

@router.post("/", response_model=BotInstance, status_code=201)
async def create_bot(
    config: BotConfig,
    service: BotService = Depends(get_bot_service)
):
    """创建新的 Bot 实例。"""
    try:
        return service.create_instance(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[BotInstance])
async def list_bots(service: BotService = Depends(get_bot_service)):
    """列出所有 Bot 实例。"""
    return service.list_instances()

@router.post("/{bot_id}/start", response_model=BotInstance)
async def start_bot(bot_id: str, service: BotService = Depends(get_bot_service)):
    """启动 Bot 实例。"""
    try:
        return service.start_instance(bot_id)
    except BotNotFoundError:
        raise HTTPException(status_code=404, detail="Bot not found")
```

---

## 后续 AI 写代码时的 Prompt 模板

你可以把下面这段直接复制给 AI，作为每次让它写代码的前置要求：

```
你现在要为 Dian_QQ_bot 项目写代码，必须严格遵守以下父约束：

1. 所有函数、方法、类属性必须加完整类型提示，不允许使用 Any
2. 命名：类 PascalCase，函数/变量 snake_case，常量 UPPER_CASE
3. 必须使用 logging.getLogger(__name__)，禁止 print
4. 所有 public 方法必须写 Google 风格 docstring（Args/Returns/Raises）
5. 异常必须抛自定义异常（继承自 core.exceptions.BotError）
6. Docker 操作全部通过 docker-py，不允许 os.system / subprocess.call("docker")
7. 容器名格式：dian-napcat-{uuid8}
8. 卷路径：./data/instances/{instance_id}/napcat/
9. 使用 dependency injection (Depends) 注入 service / manager
10. 代码必须能通过 black --line-length=100、isort、mypy、flake8 检查

现在请实现：[具体任务描述]
请输出完整文件路径 + 代码，不要省略导入语句。
```

---

*点点会喜欢这种有条理、干净的代码的～ 💕🐱*
