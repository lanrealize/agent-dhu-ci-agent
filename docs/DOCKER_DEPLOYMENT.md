# Docker 部署指南

## 概述

本项目提供两种 Docker 镜像构建方式：

1. **标准版** (`Dockerfile`) - 开发和调试使用
2. **字节码编译版** (`Dockerfile.pyc`) - 生产部署，保护源码

---

## 快速开始

### 方式 1：标准版（开发）

```bash
# 构建
docker build -f docker/Dockerfile -t devops-agent:latest .

# 运行
docker run -d \
  -p 8000:8000 \
  --name devops-agent \
  -e DEEPSEEK_API_KEY=your-key-here \
  devops-agent:latest
```

### 方式 2：字节码编译版（生产）

```bash
# 构建
docker build -f docker/Dockerfile.pyc -t devops-agent:protected .

# 运行
docker run -d \
  -p 8000:8000 \
  --name devops-agent-protected \
  -e DEEPSEEK_API_KEY=your-key-here \
  devops-agent:protected
```

---

## 源码保护验证

### 标准版（源码可见）

```bash
# 进入容器
docker run -it devops-agent:latest /bin/bash

# 查看源码
cat /app/src/api/main.py
# ✅ 可以看到完整源码
```

### 字节码编译版（源码已删除）

```bash
# 进入容器
docker run -it devops-agent:protected /bin/bash

# 查看目录结构
ls -la /app/src/api/
# 输出：
# main.pyc          ← 只有字节码文件
# __init__.py       ← 保留（必需）
# routes/

# 尝试查看源码
cat /app/src/api/main.py
# 输出：cat: /app/src/api/main.py: No such file or directory

# 查看字节码
cat /app/src/api/main.pyc
# 输出：乱码（二进制字节码）
```

---

## Docker Compose 部署

### docker-compose.yml

```yaml
version: '3.8'

services:
  devops-agent:
    build:
      context: .
      dockerfile: docker/Dockerfile.pyc  # 使用字节码版本
    image: devops-agent:protected
    container_name: devops-agent
    ports:
      - "8000:8000"
    environment:
      # LLM 配置
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - DEEPSEEK_BASE_URL=https://api.deepseek.com
      - DEEPSEEK_MODEL=deepseek-reasoner

      # 数据库配置
      - DATABASE_URL=sqlite:///./devops_agent.db
      - MONGODB_URL=mongodb://mongo:27017
      - MONGODB_DATABASE=dhuci_agent_db

      # API 配置
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - LOG_LEVEL=INFO

    volumes:
      # 持久化数据库（可选）
      - ./data:/app/data

    restart: unless-stopped

    # 安全加固
    read_only: false  # 需要写日志
    security_opt:
      - no-new-privileges:true

  # 可选：MongoDB 服务
  mongo:
    image: mongo:7
    container_name: devops-mongo
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db
    restart: unless-stopped

volumes:
  mongo-data:
```

### 使用 Docker Compose

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f devops-agent

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

---

## 环境变量配置

### 必需变量

```bash
# LLM API
DEEPSEEK_API_KEY=sk-xxxxx

# 可选
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner
```

### 推荐方式：使用 .env 文件

```bash
# 创建 .env 文件
cat > .env << EOF
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner
MONGODB_URL=mongodb://mongo:27017
MONGODB_DATABASE=dhuci_agent_db
EOF

# 使用 docker-compose 自动加载
docker-compose up -d
```

---

## 生产部署最佳实践

### 1. 使用私有镜像仓库

```bash
# 推送到私有仓库
docker tag devops-agent:protected registry.company.com/devops-agent:v1.0
docker push registry.company.com/devops-agent:v1.0

# 从私有仓库拉取
docker pull registry.company.com/devops-agent:v1.0
```

### 2. 健康检查

```dockerfile
# 在 Dockerfile.pyc 中添加
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"
```

### 3. 资源限制

```bash
docker run -d \
  --name devops-agent \
  --memory="2g" \
  --cpus="2" \
  -p 8000:8000 \
  devops-agent:protected
```

### 4. 日志管理

```bash
docker run -d \
  --name devops-agent \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -p 8000:8000 \
  devops-agent:protected
```

---

## 镜像大小优化

### 当前镜像大小

```bash
docker images devops-agent
# REPOSITORY      TAG         SIZE
# devops-agent    latest      ~800MB  (标准版)
# devops-agent    protected   ~800MB  (字节码版，删除源码后几乎一样)
```

### 优化建议

如果需要进一步减小镜像：

1. 使用 `python:3.10-alpine`（约 400MB）
2. 使用多阶段构建
3. 清理不必要的依赖

---

## 常见问题

### Q: .pyc 文件能运行吗？

A: 能！Python 解释器完全支持直接运行 .pyc 文件。

### Q: 性能有影响吗？

A: 几乎没有。.pyc 文件实际上可能略快，因为跳过了编译步骤。

### Q: 如何调试？

A: 开发环境使用标准版 Dockerfile，生产环境使用 .pyc 版本。

### Q: .pyc 安全吗？

A: 可以反编译，但增加了逆向难度。适合内部部署和一般商业场景。

### Q: 如何更新代码？

A: 重新构建镜像：

```bash
# 拉取最新代码
git pull

# 重新构建
docker build -f docker/Dockerfile.pyc -t devops-agent:protected .

# 重启容器
docker-compose up -d --force-recreate
```

---

## 测试验证

### 1. 构建测试

```bash
# 构建字节码版本
docker build -f docker/Dockerfile.pyc -t devops-agent:test .

# 验证构建成功
docker images | grep devops-agent
```

### 2. 功能测试

```bash
# 启动容器
docker run -d -p 8000:8000 \
  -e DEEPSEEK_API_KEY=sk-test \
  --name test-agent \
  devops-agent:test

# 测试健康检查
curl http://localhost:8000/api/v1/health

# 测试聊天接口
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "session_id": null}'

# 清理
docker stop test-agent && docker rm test-agent
```

### 3. 源码保护验证

```bash
# 进入容器
docker run -it devops-agent:test /bin/bash

# 检查源码是否被删除
ls -la /app/src/api/
cat /app/src/api/main.py  # 应该报错 No such file

# 检查 .pyc 文件
ls -la /app/src/api/main.pyc  # 应该存在
file /app/src/api/main.pyc    # 显示为 python 2.7 byte-compiled

exit
```

---

## 下一步

1. ✅ 使用 `Dockerfile.pyc` 构建生产镜像
2. ✅ 配置 `docker-compose.yml`
3. ✅ 设置环境变量
4. ✅ 测试功能正常
5. ✅ 推送到私有镜像仓库
6. ✅ 部署到生产环境

---

## 技术细节

### 编译原理

```bash
# compileall 做了什么
python -m compileall -b src/
# -b: 输出 .pyc 到源码同级目录（而不是 __pycache__）

# 结果：
# src/api/main.py   → src/api/main.pyc
# src/agent/devops_agent.py → src/agent/devops_agent.pyc
```

### 保留 __init__.py 的原因

```python
# __init__.py 通常很小，且对包导入是必需的
# 示例：
# src/api/__init__.py (几乎为空)
# 删除它不会增加安全性，反而可能导致导入错误
```

### PYTHONOPTIMIZE=2 的作用

```bash
# 优化级别 2：
# - 移除 assert 语句
# - 移除 __doc__ 字符串
# - 生成更小的字节码
```

---

## 支持

如有问题，请参考：
- 项目 README.md
- docs/ 目录下的文档
- 提交 Issue
