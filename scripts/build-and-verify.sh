#!/bin/bash
# Docker 字节码版本构建和验证脚本

set -e

echo "=========================================="
echo "Docker .pyc 版本构建和验证"
echo "=========================================="

# 1. 构建镜像
echo ""
echo "📦 步骤 1: 构建字节码保护版本镜像..."
docker build -f docker/Dockerfile.pyc -t devops-agent:pyc-test .

# 2. 检查镜像大小
echo ""
echo "📊 步骤 2: 检查镜像大小..."
docker images devops-agent:pyc-test

# 3. 验证源码是否被删除
echo ""
echo "🔒 步骤 3: 验证源码保护..."
echo "检查 src/api/main.py 是否存在（应该不存在）："
docker run --rm devops-agent:pyc-test ls -la /app/src/api/main.py 2>&1 || echo "✅ 源码已删除"

echo ""
echo "检查 main.pyc 是否存在（应该存在）："
docker run --rm devops-agent:pyc-test ls -la /app/src/api/main.pyc

# 4. 测试功能
echo ""
echo "🧪 步骤 4: 测试应用功能..."
echo "启动容器（后台）..."
docker run -d --name pyc-test \
  -p 8888:8000 \
  -e DEEPSEEK_API_KEY=sk-test \
  devops-agent:pyc-test

# 等待启动
echo "等待应用启动..."
sleep 5

# 测试健康检查
echo ""
echo "测试健康检查接口..."
curl -s http://localhost:8888/api/v1/health | head -n 5

# 清理
echo ""
echo "🧹 清理测试容器..."
docker stop pyc-test
docker rm pyc-test

# 5. 完成
echo ""
echo "=========================================="
echo "✅ 验证完成！"
echo "=========================================="
echo ""
echo "镜像已准备就绪: devops-agent:pyc-test"
echo ""
echo "下一步："
echo "1. 推送到私有仓库: docker push your-registry/devops-agent:pyc-test"
echo "2. 或使用 docker-compose: docker-compose up -d"
