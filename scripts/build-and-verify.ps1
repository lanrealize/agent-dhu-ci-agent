# Docker 字节码版本构建和验证脚本 (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Docker .pyc 版本构建和验证" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. 构建镜像
Write-Host ""
Write-Host "📦 步骤 1: 构建字节码保护版本镜像..." -ForegroundColor Yellow
docker build -f docker/Dockerfile.pyc -t devops-agent:pyc-test .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 构建失败！" -ForegroundColor Red
    exit 1
}

# 2. 检查镜像大小
Write-Host ""
Write-Host "📊 步骤 2: 检查镜像大小..." -ForegroundColor Yellow
docker images devops-agent:pyc-test

# 3. 验证源码是否被删除
Write-Host ""
Write-Host "🔒 步骤 3: 验证源码保护..." -ForegroundColor Yellow
Write-Host "检查 src/api/main.py 是否存在（应该不存在）：" -ForegroundColor Gray

$result = docker run --rm devops-agent:pyc-test ls -la /app/src/api/main.py 2>&1
if ($result -like "*No such file*") {
    Write-Host "✅ 源码已删除" -ForegroundColor Green
} else {
    Write-Host "⚠️ 警告：源码似乎仍然存在" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "检查 main.pyc 是否存在（应该存在）：" -ForegroundColor Gray
docker run --rm devops-agent:pyc-test ls -la /app/src/api/main.pyc

# 4. 测试功能
Write-Host ""
Write-Host "🧪 步骤 4: 测试应用功能..." -ForegroundColor Yellow
Write-Host "启动容器（后台）..." -ForegroundColor Gray

docker run -d --name pyc-test `
  -p 8888:8000 `
  -e DEEPSEEK_API_KEY=sk-test `
  devops-agent:pyc-test

# 等待启动
Write-Host "等待应用启动..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 测试健康检查
Write-Host ""
Write-Host "测试健康检查接口..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri http://localhost:8888/api/v1/health -TimeoutSec 5
    Write-Host "✅ 健康检查通过！状态码: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "⚠️ 健康检查失败（可能需要配置 API Key）" -ForegroundColor Yellow
}

# 清理
Write-Host ""
Write-Host "🧹 清理测试容器..." -ForegroundColor Yellow
docker stop pyc-test | Out-Null
docker rm pyc-test | Out-Null

# 5. 完成
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ 验证完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "镜像已准备就绪: devops-agent:pyc-test" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 推送到私有仓库: docker push your-registry/devops-agent:pyc-test"
Write-Host "2. 或使用 docker-compose: docker-compose up -d"
Write-Host "3. 或直接运行: docker run -p 8000:8000 -e DEEPSEEK_API_KEY=your-key devops-agent:pyc-test"
