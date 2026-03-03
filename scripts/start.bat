@echo off
REM Dian QQ Bot Windows 启动脚本

echo ============================================================
echo   Dian QQ Bot - 启动脚本
echo ============================================================

REM 检查 Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker Desktop 未安装
    pause
    exit /b 1
)

REM 检查 .env 文件
if not exist .env (
    echo [INFO] 创建 .env 配置文件...
    copy .env.example .env
)

REM 创建目录
if not exist data mkdir data
if not exist logs mkdir logs
if not exist instances mkdir instances

REM 启动服务
echo [INFO] 启动服务...
docker compose -f docker-compose.windows.yml up -d

echo.
echo [OK] 服务已启动
echo.
echo 访问地址:
echo   - 前端：http://localhost:80
echo   - API: http://localhost:8000
echo   - 文档：http://localhost:8000/docs
echo.
echo 查看日志：docker compose logs -f
echo 停止服务：docker compose down
echo ============================================================
