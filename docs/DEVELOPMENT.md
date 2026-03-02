项目名为 **Dian_QQ_bot**（纪念你的小猫点点 🐱❤️），这是一个基于 Docker 的 QQ Bot 管理平台，主要目标是让用户通过 Web 界面轻松管理多个 QQ Bot 实例（重点支持 NapCat Docker 镜像，后续可扩展 LLOneBot 或其他）。

### 项目整体架构（2026 年实用版）

```
Dian_QQ_bot (monorepo 或前后端分离目录)
├── backend/                      # FastAPI 后端 (Python)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # 入口：uvicorn app.main:app
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── instances.py  # 实例 CRUD + 操作接口
│   │   ├── core/
│   │   │   ├── config.py         # 设置、路径、端口池等
│   │   │   └── exceptions.py
│   │   ├── managers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # 抽象 BotManager
│   │   │   └── napcat.py         # NapCat Docker 管理实现
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── instance.py       # Pydantic + DB 模型
│   │   ├── schemas/              # 请求/响应 Pydantic schema
│   │   ├── database.py           # SQLite 会话
│   │   └── utils/
│   │       └── docker_utils.py   # 端口分配、卷路径生成等工具
│   ├── data/                     # .gitignore 忽略
│   │   ├── db.sqlite             # SQLite 文件
│   │   └── instances/            # 每个实例的卷目录（自动创建）
│   ├── .env                      # 环境变量
│   └── requirements.txt
│
├── frontend/                     # Vue 3 + Vite + Tailwind + shadcn-vue
│   ├── src/
│   │   ├── assets/               # main.css (Tailwind)
│   │   ├── components/
│   │   │   └── ui/               # shadcn-vue 组件目录（button、card、table 等）
│   │   ├── views/
│   │   │   ├── InstanceList.vue  # 实例列表 + 操作按钮
│   │   │   ├── InstanceCreate.vue # 创建表单
│   │   │   └── InstanceDetail.vue # 详情 + 日志
│   │   ├── api/                  # axios 实例 + 接口封装
│   │   ├── router/               # vue-router
│   │   ├── stores/               # pinia（可选：主题、实例状态）
│   │   ├── App.vue
│   │   └── main.ts
│   ├── components.json           # shadcn-vue 配置
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── index.html
│
├── docker-compose.yml            # 可选：平台本身容器化运行（后期加）
├── .gitignore
├── README.md                     # 项目说明 + 献给点点的寄语
└── LICENSE                       # MIT
```

**关键设计点**：
- 所有 Bot 实例以 Docker 容器运行（用户自备镜像，如 mlikiowa/napcat-docker:latest）
- 平台只负责 docker-py 操作：创建/启动/停止/重启/删除容器 + 管理卷/端口
- 数据库只存元数据（容器名、端口映射、状态等），实际数据在文件系统
- 前端用 shadcn-vue 组件 + Tailwind 自定义点点粉色主题

### 任务待办清单（优先级从高到低，适合分批给 AI 实现）

#### Phase 1: 项目初始化 & 后端骨架（1-2 天）
1. 创建 GitHub 仓库 Dian_QQ_bot，初始化 README（包含献给点点的描述）
2. 本地创建项目目录结构（backend + frontend）
3. backend: 创建虚拟环境，安装核心依赖（fastapi, uvicorn, pydantic, docker, sqlalchemy, aiosqlite, python-dotenv, psutil）
4. backend: 写 models/instance.py（Pydantic 模型：InstanceCreate, Instance, Status Enum, Protocol Enum）
5. backend: 写 database.py（SQLite 会话 + 简单 Instance 表创建）
6. backend: 写 core/config.py（DATA_DIR, PORT_RANGE_START/END 等配置，从 .env 读取）
7. backend: 创建 main.py（FastAPI app，添加 /health 接口测试）

#### Phase 2: NapCat Docker 管理核心（2-3 天，最重要）
8. backend: 写 managers/base.py（抽象 BotManager 类，定义 create/start/stop/restart/delete 接口）
9. backend: 实现 managers/napcat.py（继承 base，使用 docker-py）
   - create：生成 instance_id、目录、端口、卷路径，创建容器（run 或 create+start）
   - start/stop/restart：操作容器
   - delete：stop → rm → 删除目录
   - get_status / get_logs
   - 预设 NapCat 模板（image, ports, volumes, env 如 UID/GID）
10. backend: 写 utils/docker_utils.py（端口分配函数、卷路径生成、容器名规则如 napcat-{id}）

#### Phase 3: 后端 API（1-2 天）
11. backend: 写 api/v1/instances.py（使用 APIRouter）
    - POST /instances （创建 NapCat 实例）
    - GET /instances （列表）
    - GET /instances/{id}
    - POST /instances/{id}/start
    - POST /instances/{id}/stop
    - POST /instances/{id}/restart
    - DELETE /instances/{id}
12. backend: 添加全局异常处理 + CORS（允许前端访问）

#### Phase 4: 前端基础 & 界面（3-5 天）
13. frontend: 初始化 Vite + Vue + TS 项目
14. frontend: 安装 Tailwind CSS + shadcn-vue，运行 npx shadcn-vue@latest init
15. frontend: 添加必要 shadcn 组件（button, card, table, dialog, badge, input, toast 等）
16. frontend: 配置自定义主题（dian-primary 等颜色）
17. frontend: 创建 InstanceList.vue（用 Table 显示实例列表 + Badge 状态 + Button 操作）
18. frontend: 创建 InstanceCreate.vue（Dialog + Form 表单提交创建）
19. frontend: 写 api/index.ts（axios 封装，baseURL http://localhost:8000）
20. frontend: 加 Pinia store（可选：管理主题切换 dark/light）

#### Phase 5: 联调 & 增强（后续迭代）
21. 测试：用 Postman 测试后端 API → 前端调用
22. 加实时状态：WebSocket 端点推送容器状态/日志（后期）
23. 加 LLOneBot 支持：自定义镜像模式（用户输入 image/ports/volumes）
24. 加安全：简单 JWT 登录（防止别人乱用你的平台）
25. 文档：完善 README（安装、运行、截图、点点寄语）
26. 打包：写 docker-compose.yml（可选：平台本身跑在容器里）
