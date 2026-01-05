@echo off
chcp 65001 >nul
echo ==========================================
echo DevOps Agent 服务测试
echo ==========================================
echo.

echo [测试 1] 健康检查...
curl -s http://localhost:8000/api/v1/health
echo.
echo.

echo [测试 2] 聊天接口测试...
echo 发送消息: "你好"
echo.
curl -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d "{\"message\": \"你好\", \"session_id\": null}"
echo.
echo.

echo ==========================================
echo ✅ 测试完成
echo ==========================================
pause
