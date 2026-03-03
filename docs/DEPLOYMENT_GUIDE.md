# Dian QQ Bot 部署指南

> 最新更新时间：2026-03-04  
> 支持平台：Windows 10/11, Linux (Ubuntu 20.04+), macOS

---

## 📋 目录

- [快速开始](#快速开始)
- [Windows 部署](#windows-部署)
- [Linux 部署](#linux-部署)
- [macOS 部署](#macos-部署)
- [故障排查](#故障排查)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 方法一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/Dian_QQ_Bot.git
cd Dian_QQ_Bot

# 2. 一键部署
# Linux/macOS:
bash scripts/deploy.sh

# Windows (管理员权限运行):
.\scripts\deploy.bat

# 3. 访问
# 前端：http://localhost:80
# API 文档：http://localhost:8000/docs
```

### 方法二：手动 Docker Compose

```bash
# 复制环境变量
cp .env.example .env

# 修改配置（重要：修改密码）
vim .env  # 或 .env.example 复制到 .env

# 启动服务
# Linux:
docker compose up -d

# Windows:
docker compose -f docker-compose.windows.yml up -d

# 查看日志
docker compose logs -f
```

---

## 🪟 Windows 部署

### 前置要求

1. **Docker Desktop** (必须)
   - 下载地址：https://www.docker.com/products/docker-desktop
   - 安装后确保 WSL 2 后端已启用

2. **Git** (可选)
   - 下载地址：https://git-scm.com/download/win

### 步骤

#### 1. 下载项目

```powershell
# 使用 Git
git clone https://github.com/yourusername/Dian_QQ_Bot.git
cd Dian_QQ_Bot

# 或手动下载 ZIP 解压
```

#### 2. 一键部署

右键点击 `scripts\deploy.bat`，选择"以管理员身份运行"

#### 3. 手动部署

```powershell
# 复制环境变量
copy .env.example .env

# 编辑 .env 文件，修改密码等配置
notepad .env

# 启动服务
docker compose -f docker-compose.windows.yml up -d

# 查看日志
docker compose logs -f
```

#### 4. 验证

打开浏览器访问：
- 前端：http://localhost:80
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

---

## 🐧 Linux 部署

### 前置要求

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose curl git

# CentOS/RHEL
sudo yum install -y docker docker-compose git

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组（避免使用 sudo）
sudo usermod -aG docker $USER
newgrp docker
```

### 步骤

#### 1. 下载项目

```bash
git clone https://github.com/yourusername/Dian_QQ_Bot.git
cd Dian_QQ_Bot
```

#### 2. 一键部署

```bash
chmod +x scripts/*.sh
bash scripts/deploy.sh
```

#### 3. 手动部署

```bash
# 复制环境变量
cp .env.example .env

# 编辑配置
vim .env

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f
```

#### 4. 设置开机自启

```bash
# 创建 systemd 服务
sudo tee /etc/systemd/system/dian-qq-bot.service > /dev/null <<'EOF'
[Unit]
Description=Dian QQ Bot
Requires=docker.service
After=docker.service

[Service]
Restart=always
WorkingDirectory=/path/to/Dian_QQ_Bot
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable dian-qq-bot
sudo systemctl start dian-qq-bot
```

---

## 🍎 macOS 部署

### 前置要求

1. **Docker Desktop for Mac**
   - 下载地址：https://www.docker.com/products/docker-desktop

2. **Homebrew** (可选)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   brew install docker-compose git
   ```

### 步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/Dian_QQ_Bot.git
cd Dian_QQ_Bot

# 2. 启动服务
docker compose up -d

# 3. 查看状态
docker compose ps

# 4. 访问
# 前端：http://localhost:80
# API: http://localhost:8000
```

---

## 🔧 故障排查

### Docker 相关

#### 1. Docker 无法启动

**错误**: `Cannot connect to the Docker daemon`

**解决**:
```bash
# Linux
sudo systemctl start docker
sudo systemctl enable docker

# Windows
# 重启 Docker Desktop

# macOS
# 重启 Docker Desktop
```

#### 2. 端口冲突

**错误**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**解决**:
```bash
# 查看占用端口的进程
# Linux/macOS
lsof -i :8000

# Windows
netstat -ano | findstr :8000

# 修改 .env 中的端口
API_PORT=8001
FRONTEND_PORT=81
```

#### 3. Docker Socket 权限问题

**错误**: `Permission denied while trying to connect to the Docker daemon socket`

**解决**:
```bash
# Linux
sudo chmod 666 /var/run/docker.sock

# 或将用户加入 docker 组
sudo usermod -aG docker $USER
```

### 数据库相关

#### 1. 数据库连接失败

**错误**: `could not connect to server: Connection refused`

**解决**:
```bash
# 等待 PostgreSQL 完全启动
docker compose logs postgres

# 重启服务
docker compose restart api

# 检查网络
docker compose exec api ping postgres
```

#### 2. 数据持久化

```bash
# 备份数据
docker compose exec postgres pg_dump -U postgres dian_bot > backup.sql

# 恢复数据
docker compose exec -T postgres psql -U postgres dian_bot < backup.sql
```

### 应用相关

#### 1. 健康检查失败

```bash
# 查看详细日志
docker compose logs api

# 重启服务
docker compose restart api

# 查看容器状态
docker compose ps
```

#### 2. 无法访问 Bot 实例

**错误**: Bot 实例创建成功但无法连接

**解决**:
```bash
# 检查 Docker Socket 配置
# Linux: 确保挂载了 /var/run/docker.sock
# Windows: 确保 DOCKER_HOST 环境变量正确

docker compose exec api env | grep DOCKER
```

---

## ❓ 常见问题

### 1. 数据存储在哪个目录？

```
Dian_QQ_Bot/
├── data/           # 应用数据
├── logs/           # 日志文件
└── instances/      # Bot 实例数据
```

### 2. 如何备份数据？

```bash
# 备份所有数据
tar -czf backup_$(date +%Y%m%d).tar.gz data/ logs/ instances/

# 备份数据库
docker compose exec postgres pg_dump -U postgres dian_bot > db_backup.sql
```

### 3. 如何升级版本？

```bash
# 拉取最新代码
git pull origin main

# 重新构建并重启
docker compose down
docker compose build
docker compose up -d
```

### 4. 如何查看日志？

```bash
# 所有服务日志
docker compose logs -f

# 单个服务
docker compose logs -f api
docker compose logs -f postgres
docker compose logs -f frontend
```

### 5. 如何重置系统？

```bash
# 停止并删除所有容器和数据
docker compose down -v

# 删除本地数据
rm -rf data/ logs/ instances/

# 重新启动
docker compose up -d
```

---

## 📞 获取帮助

如有问题，请：
1. 查看日志：`docker compose logs -f`
2. 检查 [.github/ISSUE_TEMPLATE](https://github.com/yourusername/Dian_QQ_Bot/issues)
3. 提交 Issue

---

**献给点点 🐱💕**
