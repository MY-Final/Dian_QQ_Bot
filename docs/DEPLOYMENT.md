# Dian QQ Bot 部署指南

## 快速部署（Docker Compose）

### 1. 准备工作

确保已安装：
- Docker Desktop（Windows/Mac）或 Docker Engine 20.10+（Linux）
- Docker Compose 2.0+

### 2. 克隆项目

```bash
git clone https://github.com/yourusername/Dian_QQ_Bot.git
cd Dian_QQ_Bot
```

### 3. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，修改数据库密码等配置
# 重要：请修改 DB_PASSWORD 为强密码
```

### 4. 启动服务

```bash
# 一键启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 查看服务状态
docker-compose ps
```

### 5. 访问系统

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **前端页面**: http://localhost:80（完成 Setup 向导后）

### 6. 初始化系统

首次访问需要完成 Setup 向导：

1. 访问前端页面
2. 配置数据库连接（使用 docker-compose 中的 postgres 服务）
   - 主机：`postgres`
   - 端口：`5432`
   - 数据库：`dian_bot`
   - 用户名：`postgres`
   - 密码：`.env` 文件中配置的密码
3. 创建管理员账号

---

## 本地开发部署

### 1. 环境要求

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+（或使用 Docker 运行）

### 2. 安装后端依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. 启动 PostgreSQL（可选使用 Docker）

```bash
docker run -d \
  --name dian-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=dian_bot \
  -p 5432:5432 \
  postgres:16-alpine
```

### 4. 启动后端服务

```bash
# 配置环境变量
cp .env.example .env

# 启动服务
python backend/main.py

# 或使用 uvicorn 直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 安装前端依赖

```bash
cd frontend

# 安装依赖
npm install

# 复制环境变量
cp .env.example .env
```

### 6. 启动前端开发服务器

```bash
# 开发模式（热重载）
npm run dev

# 访问 http://localhost:5173
```

---

## 生产环境部署

### 1. 安全配置

- 修改 `.env` 中的默认密码
- 设置 `DEBUG=false`
- 配置合适的 `LOG_LEVEL=WARNING` 或 `ERROR`
- 使用 HTTPS（通过 Nginx 反向代理）

### 2. 使用 Nginx 反向代理

配置示例：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 3. 配置 systemd 服务

创建 `/etc/systemd/system/dian-qq-bot.service`:

```ini
[Unit]
Description=Dian QQ Bot Backend
After=network.target postgresql.service docker.service

[Service]
Type=exec
User=www-data
WorkingDirectory=/path/to/Dian_QQ_Bot
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python backend/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable dian-qq-bot
sudo systemctl start dian-qq-bot
sudo systemctl status dian-qq-bot
```

---

## 常见问题

### Docker 连接失败

**错误**: `无法连接到 Docker 守护进程`

**解决方案**:
- Windows/Mac: 确保 Docker Desktop 已启动
- Linux: 确保 Docker 服务运行 `sudo systemctl start docker`

### 数据库连接失败

**错误**: `数据库连接失败`

**解决方案**:
- 检查 PostgreSQL 是否运行
- 验证 `.env` 中的数据库配置
- 检查防火墙设置

### 端口冲突

**错误**: `端口已被占用`

**解决方案**:
- 修改 `.env` 中的端口配置
- 或停止占用端口的服务

---

## 备份和恢复

### 数据库备份

```bash
# 备份
docker exec dian-qq-bot-postgres pg_dump \
  -U postgres dian_bot > backup_$(date +%Y%m%d).sql

# 恢复
docker exec -i dian-qq-bot-postgres psql \
  -U postgres dian_bot < backup_20260303.sql
```

### 实例数据备份

```bash
# 备份所有 Bot 实例数据
tar -czf instances_backup_$(date +%Y%m%d).tar.gz \
  ./data/instances/
```

---

## 更新升级

```bash
# 拉取最新代码
git pull origin main

# 重新构建并重启
docker-compose down
docker-compose build
docker-compose up -d
```

---

**祝部署顺利！献给点点 🐱💕**

如有问题，请查看日志：
```bash
docker-compose logs -f
```
