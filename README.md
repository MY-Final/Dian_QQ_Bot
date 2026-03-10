# Dian QQ Bot 🐱❤️

**QQ Bot 管理平台** —— 献给我的点点

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个基于 Docker 的多实例 QQ Bot 管理平台，支持 NapCat 协议，通过 Web 界面或 API 轻松创建、启动、停止、重启、监控 Bot 实例。

> 点点是我的小猫猫，虽然它已经离开，但我想用这个项目纪念它，让更多人能简单地玩转 QQ Bot。 💕

---

## ✨ 特性

- 🐳 **Docker 多实例隔离** - 每个 Bot 独立容器，互不干扰
- 🚀 **一键创建 NapCat Bot** - 自动分配端口、挂载卷、配置环境变量
- 📊 **Web 仪表盘** - Vue 3 + shadcn-vue + Tailwind（计划中）
- 📝 **实时日志查看** - 支持获取容器最新日志
- 🎨 **点点主题色** - 温馨粉色主题 💕
- 🔧 **RESTful API** - 完整的 CRUD 接口，易于集成
- 📦 **Docker Compose / Docker Hub** - 单容器运行前后端，用户只需启动一个应用容器

---

## 🏗️ 架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Dian QQ Bot Platform                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────────────────────────────────────────┐  │
│  │   Frontend   │────▶│             FastAPI Backend (Port 18080)         │  │
│  │  (Vue 3 +    │     │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │  │
│  │  shadcn-vue) │     │  │  API Routes │  │  Services   │  │ Managers │ │  │
│  └──────────────┘     │  │  /api/v1/*  │  │  BotService │  │ NapCat   │ │  │
│                       │  └──────┬──────┘  └──────┬──────┘  └────┬─────┘ │  │
│                       └─────────┼─────────────────┼─────────────┼───────┘  │
│                                 │                 │             │          │
│  ┌──────────────────────────────┼─────────────────┼─────────────┼───────┐  │
│  │                         Database Layer          │             │       │  │
│  │  ┌───────────────────────────▼───────┐         │             │       │  │
│  │  │      PostgreSQL (5432)            │         │             │       │  │
│  │  │  - Bot Instances (metadata)       │◀────────┘             │       │  │
│  │  │  - Users & Auth                   │                       │       │  │
│  │  │  - Settings                       │                       │       │  │
│  │  └───────────────────────────────────┘                       │       │  │
│  └───────────────────────────────────────────────────────────────┼───────┘  │
│                                                                  │          │
│  ┌───────────────────────────────────────────────────────────────▼───────┐  │
│  │                    Docker Containers (Bot Instances)                   │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │  │
│  │  │  NapCat Bot #1  │  │  NapCat Bot #2  │  │  NapCat Bot #N  │       │  │
│  │  │  Port: 30000    │  │  Port: 30002    │  │  Port: 30XXX    │       │  │
│  │  │  Container:     │  │  Container:     │  │  Container:     │       │  │
│  │  │  dian-napcat-   │  │  dian-napcat-   │  │  dian-napcat-   │       │  │
│  │  │  {uuid8}        │  │  {uuid8}        │  │  {uuid8}        │       │  │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘       │  │
│  │           │                    │                    │                 │  │
│  │  ┌────────▼────────────────────▼────────────────────▼────────┐       │  │
│  │  │           Docker Socket (npipe:////./pipe/docker_engine)  │       │  │
│  │  └───────────────────────────────────────────────────────────┘       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                      Volume Mounts (./data/instances/)                  │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │  │
│  │  │  {id}/napcat/    │  │  {id}/napcat/    │  │  {id}/napcat/    │     │  │
│  │  │  - config/       │  │  - config/       │  │  - config/       │     │  │
│  │  │  - logs/         │  │  - logs/         │  │  - logs/         │     │  │
│  │  │  - data/         │  │  - data/         │  │  - data/         │     │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘     │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 数据流示例（创建 Bot 实例）

```
User Request (POST /api/v1/instances)
        │
        ▼
┌───────────────────┐
│  API Router       │───▶ Validate Request (InstanceCreate)
│  (instances.py)   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  NapCatManager    │───▶ Generate: instance_id, container_name, ports
│  (napcat.py)      │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Docker Engine    │───▶ Create Container (dian-napcat-{uuid8})
│  (docker-py)      │       Mount Volumes
                   │       Expose Ports (3000, 3001, 6099)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  PostgreSQL DB    │───▶ Save Instance Metadata
│  (bot_instances)  │       (id, name, qq, ports, status, etc.)
└─────────┬─────────┘
          │
          ▼
    Return InstanceResponse
```

---

## 📁 项目结构

```
Dian_QQ_Bot/
├── backend/                      # FastAPI 后端
│   └── app/
│       ├── __init__.py
│       ├── main.py               # 应用入口（FastAPI + 中间件 + 生命周期）
│       ├── database.py           # 数据库会话管理
│       ├── api/
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── instances.py  # Bot 实例 CRUD API
│       │       └── system.py     # 系统相关 API
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py         # Pydantic Settings
│       │   └── exceptions.py     # 自定义异常
│       ├── managers/
│       │   ├── __init__.py
│       │   ├── base.py           # 抽象 Bot 管理器
│       │   └── napcat.py         # NapCat Docker 管理器
│       ├── models/
│       │   ├── __init__.py
│       │   ├── instance.py       # Pydantic 模型
│       │   └── db_models.py      # SQLAlchemy ORM 模型
│       └── utils/
│           ├── __init__.py
│           ├── docker_utils.py   # Docker 工具函数
│           └── security.py       # 安全工具
├── frontend/                     # Vue 3 前端（计划中）
├── data/                         # .gitignore
│   └── instances/                # Bot 实例卷目录
├── logs/                         # 日志目录
├── docs/
│   └── DEVELOPMENT.md            # 开发文档
├── .env.example                  # 环境变量示例
├── docker-compose.yml            # Docker Compose 配置
├── Dockerfile.backend            # 后端 Dockerfile
├── Dockerfile.frontend           # 前端 Dockerfile
├── nginx.conf                    # Nginx 配置
├── requirements.txt              # Python 依赖
├── main.py                       # 开发模式入口
├── README.md                     # 本文件
└── AGENTS.md                     # AI 开发指南
```

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Docker Desktop（Windows/Mac）或 Docker Engine（Linux）
- PostgreSQL（或使用 Docker Compose 自动部署）

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/Dian_QQ_Bot.git
cd Dian_QQ_Bot

# 2. 复制环境变量文件
cp .env.example .env
# 修改 .env 中的配置（数据库密码、端口等）

# 3. 启动所有服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f app

# 5. 访问应用（前端 + API）
# Web: http://localhost:16788
# API Docs: http://localhost:16788/api/docs
```

### 方式二：Docker Hub（一个容器直接运行）

```bash
docker run -d \
  --name dian-qq-bot \
  -p 16788:16788 \
  -e DB_HOST=<your_db_host> \
  -e DB_PORT=5432 \
  -e DB_NAME=dian_bot \
  -e DB_USER=postgres \
  -e DB_PASSWORD=<your_db_password> \
  -e JWT_SECRET_KEY=<your_strong_secret> \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/instances:/app/instances \
  <your_dockerhub_user>/dian-qq-bot:latest
```

### 方式二：本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 启动 PostgreSQL（可选：使用 Docker）
docker run -d \
  --name dian-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=dian_bot \
  -p 5432:5432 \
  postgres:16-alpine

# 4. 启动后端
python main.py

# 5. 访问 API 文档
# http://localhost:8000/docs
```

---

## 📖 API 使用示例

### 创建 Bot 实例

```bash
curl -X POST "http://localhost:16788/api/v1/instances" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-bot",
    "qq_number": "123456789",
    "protocol": "napcat",
    "description": "我的第一个 QQ Bot"
  }'
```

响应：

```json
{
  "success": true,
  "message": "实例创建成功",
  "data": {
    "id": "a1b2c3d4e5f6",
    "name": "my-bot",
    "qq_number": "123456789",
    "protocol": "napcat",
    "status": "running",
    "container_name": "dian-napcat-a1b2c3d4e5f6",
    "port": 30000,
    "port_web_ui": null,
    "port_ws": 30001,
    "volume_path": "./data/instances/a1b2c3d4e5f6/napcat",
    "created_at": "2026-03-03T12:00:00"
  }
}
```

### 列出所有实例

```bash
curl "http://localhost:16788/api/v1/instances"
```

### 启动实例

```bash
curl -X POST "http://localhost:16788/api/v1/instances/{instance_id}/start"
```

### 停止实例

```bash
curl -X POST "http://localhost:16788/api/v1/instances/{instance_id}/stop"
```

### 获取日志

```bash
curl "http://localhost:16788/api/v1/instances/{instance_id}/logs?tail=100"
```

### 删除实例

```bash
curl -X DELETE "http://localhost:16788/api/v1/instances/{instance_id}"
```

---

## ⚙️ 配置说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_USER` | `postgres` | PostgreSQL 用户名 |
| `DB_PASSWORD` | `postgres` | PostgreSQL 密码 |
| `DB_NAME` | `dian_bot` | PostgreSQL 数据库名 |
| `DB_PORT` | `5432` | PostgreSQL 端口 |
| `DEBUG` | `false` | 调试模式 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `APP_PORT` | `16788` | 单容器应用对外端口（前端 + API 入口） |
| `DOCKER_SOCKET` | `npipe:////./pipe/docker_engine` | Docker Socket 路径（Windows） |
| `CONTAINER_PREFIX` | `dian` | 容器名称前缀 |
| `NAPCAT_IMAGE` | `mlikiowa/napcat-docker:latest` | NapCat 镜像 |
| `PORT_RANGE_START` | `30000` | Bot 实例端口范围起始 |
| `PORT_RANGE_END` | `40000` | Bot 实例端口范围结束 |

---

## 🧪 开发

### 运行测试

```bash
pytest
pytest tests/ -v
pytest --cov=backend --cov-report=html
```

### 代码格式化

```bash
black backend/
isort backend/
flake8 backend/
mypy backend/
```

---

## 📝 技术栈

### 后端

- **Python 3.11+** - 主要编程语言
- **FastAPI** - Web 框架
- **SQLAlchemy 2.0** - ORM
- **PostgreSQL** - 数据库
- **Docker-py** - Docker SDK
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI 服务器

### 前端（计划中）

- **Vue 3** - 渐进式框架
- **shadcn-vue** - UI 组件库
- **Tailwind CSS** - 原子化 CSS
- **Axios** - HTTP 客户端

---

## 🙏 致谢

- [NapCat](https://github.com/NapCatQQ/NapCat) - 优秀的 QQ 协议实现
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Docker](https://www.docker.com/) - 容器化技术

---

## 📄 许可证

MIT License - 用爱发电，献给点点 🐱❤️

---

*点点在看着你呢～ 💕*
