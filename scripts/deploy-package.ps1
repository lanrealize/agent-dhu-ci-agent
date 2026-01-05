# DevOps Agent 部署打包脚本
# 用于本地打包 Docker 镜像以便传输到公司服务器

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DevOps Agent 部署打包工具" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 配置
$imageName = "devops-agent:production"
$exportDir = "$env:USERPROFILE\Desktop\devops-deploy"
$tarFile = "$exportDir\devops-agent.tar.gz"

# 1. 创建导出目录
Write-Host "📁 步骤 1: 创建导出目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $exportDir | Out-Null
Write-Host "✅ 目录创建: $exportDir" -ForegroundColor Green

# 2. 构建镜像
Write-Host ""
Write-Host "🔨 步骤 2: 构建 .pyc 保护镜像..." -ForegroundColor Yellow
docker build -f docker/Dockerfile.pyc -t $imageName .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 构建失败！" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 镜像构建完成" -ForegroundColor Green

# 3. 保存并压缩镜像
Write-Host ""
Write-Host "📦 步骤 3: 保存并压缩镜像（约需 1-2 分钟）..." -ForegroundColor Yellow
docker save $imageName | gzip > $tarFile

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 保存失败！" -ForegroundColor Red
    exit 1
}

# 4. 显示结果
$fileSize = (Get-Item $tarFile).Length / 1MB
Write-Host "✅ 镜像已保存并压缩" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ 打包完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📄 文件信息:" -ForegroundColor Yellow
Write-Host "  位置: $tarFile"
Write-Host "  大小: $([math]::Round($fileSize, 2)) MB"
Write-Host ""
Write-Host "📋 下一步操作:" -ForegroundColor Yellow
Write-Host "  1. 使用 WinSCP/FileZilla 传输文件到服务器"
Write-Host "     目标路径: /tmp/devops-agent.tar.gz"
Write-Host ""
Write-Host "  2. SSH 登录服务器执行部署："
Write-Host "     bash deploy-server.sh" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔗 相关文档:" -ForegroundColor Yellow
Write-Host "  docs/COMPANY_DEPLOYMENT.md - 完整部署指南"
Write-Host ""

# 5. 询问是否打开导出目录
$open = Read-Host "是否打开导出目录? (Y/N)"
if ($open -eq "Y" -or $open -eq "y") {
    explorer $exportDir
}
