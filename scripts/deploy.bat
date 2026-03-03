@echo off
REM Dian QQ Bot Windows 一键部署脚本
REM 使用：以管理员身份运行 deploy.bat

echo ============================================================
echo   Dian QQ Bot - Windows 一键部署脚本
echo   献给点点 🐱❤️
echo ============================================================
echo.

REM 检查 Docker Desktop
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker Desktop 未安装
    echo 请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [OK] Docker Desktop 已安装
docker --version
echo.

REM 检查 .env 文件
if not exist .env (
    echo [INFO] 创建 .env 配置文件...
    copy .env.example .env
    
    REM 生成随机密码
    powershell -Command "$password = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_}); (Get-Content .env.example) -replace 'DB_PASSWORD=.*', \"DB_PASSWORD=$password\" | Set-Content .env"
    
    echo [OK] .env 文件创建完成
) else (
    echo [OK] .env 文件已存在
)
echo.

REM 创建必要目录
echo [INFO] 创建必要目录...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist instances mkdir instances
echo [OK] 目录创建完成
echo.

REM 启动服务
echo [INFO] 启动服务...
docker compose -f docker-compose.windows.yml up -d

echo.
echo ============================================================
echo   服务已启动！
echo.
echo   访问地址:
echo     - 前端：http://localhost:80
echo     - API 文档：http://localhost:8000/docs
echo     - 健康检查：http://localhost:8000/health
echo ============================================================
echo.
echo 查看日志：docker compose logs -f
echo 停止服务：docker compose down
echo.
echo 🎉 部署成功！献给点点 💕
echo ============================================================

pause
