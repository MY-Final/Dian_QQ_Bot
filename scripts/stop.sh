#!/bin/bash
# Dian QQ Bot Linux 停止脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "============================================================"
echo "  Dian QQ Bot - 停止脚本"
echo "============================================================"

# 停止服务
echo "🛑 停止服务..."
docker compose down

echo ""
echo "✅ 服务已停止"
echo "============================================================"
