#!/bin/bash
# Dian QQ Bot Linux 一键部署脚本
# 使用：bash deploy.sh

set -e

echo "============================================================"
echo "  Dian QQ Bot - Linux 一键部署脚本"
echo "  献给点点 🐱❤️"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否已安装 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装${NC}"
        echo "正在安装 Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        echo -e "${GREEN}✅ Docker 安装完成${NC}"
    else
        echo -e "${GREEN}✅ Docker 已安装：$(docker --version)${NC}"
    fi
}

# 检查是否已安装 Docker Compose
check_docker_compose() {
    if ! command -v docker compose &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker Compose 未安装，尝试安装...${NC}"
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo -e "${GREEN}✅ Docker Compose 安装完成${NC}"
    else
        echo -e "${GREEN}✅ Docker Compose 已安装：$(docker compose version)${NC}"
    fi
}

# 检查 Docker 是否运行
check_docker_running() {
    if ! sudo systemctl is-active --quiet docker; then
        echo -e "${YELLOW}⚠️  Docker 服务未运行，正在启动...${NC}"
        sudo systemctl start docker
        sudo systemctl enable docker
        echo -e "${GREEN}✅ Docker 服务已启动${NC}"
    else
        echo -e "${GREEN}✅ Docker 服务运行正常${NC}"
    fi
}

# 创建 .env 文件
create_env_file() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}创建 .env 配置文件...${NC}"
        cp .env.example .env
        
        # 生成随机密码
        RANDOM_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
        sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$RANDOM_PASSWORD/" .env
        
        echo -e "${GREEN}✅ .env 文件创建完成${NC}"
    else
        echo -e "${GREEN}✅ .env 文件已存在${NC}"
    fi
}

# 创建必要目录
create_directories() {
    echo -e "${YELLOW}创建必要目录...${NC}"
    mkdir -p data logs instances
    chmod -R 755 data logs instances
    echo -e "${GREEN}✅ 目录创建完成${NC}"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动服务...${NC}"
    docker compose up -d
    
    echo ""
    echo -e "${GREEN}✅ 服务启动完成！${NC}"
    echo ""
    echo "============================================================"
    echo "  访问地址："
    echo "  - 前端：http://localhost:80"
    echo "  - API 文档：http://localhost:8000/docs"
    echo "  - 健康检查：http://localhost:8000/health"
    echo "============================================================"
    echo ""
    echo "查看日志：docker compose logs -f"
    echo "停止服务：docker compose down"
    echo ""
}

# 主函数
main() {
    echo ""
    check_docker
    check_docker_compose
    check_docker_running
    create_env_file
    create_directories
    start_services
    
    echo -e "${GREEN}🎉 部署成功！献给点点 💕${NC}"
}

# 运行主函数
main
