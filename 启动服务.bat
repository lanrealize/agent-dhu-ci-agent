@echo off
chcp 65001 >nul
echo ==========================================
echo DevOps Agent 服务启动
echo ==========================================
echo.

cd /d %~dp0

echo [1/3] 激活虚拟环境...
call .venv\Scripts\activate.bat

echo [2/3] 创建数据目录...
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo [3/3] 启动服务...
echo.
echo ✅ 服务启动中，请稍候...
echo.
echo 📍 访问地址：
echo    - 健康检查: http://localhost:8000/api/v1/health
echo    - API 文档: http://localhost:8000/docs
echo.
echo 💡 按 Ctrl+C 可停止服务
echo.
echo ==========================================
echo.

python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

pause
