#!/usr/bin/env bash
# Dian QQ Bot Linux 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "============================================================"
echo "  Dian QQ Bot - 启动脚本"
echo "============================================================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在，从示例创建..."
    cp .env.example .env
fi

# 创建必要目录
mkdir -p data logs instances

# 启动服务
echo "🚀 启动服务..."
docker compose up -d

echo ""
echo "✅ 服务已启动"
echo ""
echo "访问地址:"
echo "  - 前端：http://localhost:80"
echo "  - API: http://localhost:8000"
echo "  - 文档：http://localhost:8000/docs"
echo ""
echo "查看日志：docker compose logs -f"
echo "停止服务：docker compose down"
echo "============================================================"
