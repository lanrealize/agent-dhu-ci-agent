# 公司服务器部署方案

## 场景分析

**你的约束**：
- ✅ 源码已通过 .pyc 保护
- ❌ 不想暴露私人 Docker 账号
- ❌ 国内无法访问 Docker Hub
- ❌ 不想通过 GitHub 暴露源码

**推荐方案**：**Docker 镜像离线传输**（零依赖外部服务）

---

## 🎯 最佳方案：Docker 镜像离线传输

### 原理

```
本地电脑                           公司服务器
  ↓                                   ↓
构建镜像 ──→ 保存 tar ──→ 传输 ──→ 加载镜像
```

### 优势

- ✅ 不需要 Docker Hub
- ✅ 不需要私有镜像仓库
- ✅ 不暴露 Docker 账号
- ✅ 源码已 .pyc 保护
- ✅ 一次传输，多次部署

---

## 📋 完整部署流程

### 步骤 1：本地构建镜像

在你的私人电脑（Windows）上：

```powershell
# 1.1 构建字节码保护版镜像
docker build -f docker/Dockerfile.pyc -t devops-agent:production .

# 1.2 验证镜像
docker images | Select-String "devops-agent"
# 输出：devops-agent  production  xxx  2 minutes ago  800MB

# 1.3 测试运行（可选）
docker run --rm -p 8000:8000 `
  -e DEEPSEEK_API_KEY=610b268c-a36e-4a47-a8ed-386787eb26af `
  -e DEEPSEEK_BASE_URL=https://higress.devops.ecp.digitalvolvo.com/gateway/v1/chat/completions `
  devops-agent:production
```

---

### 步骤 2：保存镜像为文件

```powershell
# 2.1 创建导出目录
New-Item -ItemType Directory -Force -Path D:\docker-export

# 2.2 保存镜像为 tar 文件（约 800MB）
docker save devops-agent:production -o D:\docker-export\devops-agent.tar

# 2.3 验证文件
Get-Item D:\docker-export\devops-agent.tar
# 输出：devops-agent.tar  800MB
```

**可选：压缩以减小传输体积**

```powershell
# 使用 gzip 压缩（约 300-400MB）
docker save devops-agent:production | gzip > D:\docker-export\devops-agent.tar.gz
```

---

### 步骤 3：传输到服务器

#### 方式 A：SCP（推荐）

```powershell
# 使用 WinSCP 或命令行 scp
scp D:\docker-export\devops-agent.tar user@company-server:/tmp/

# 如果压缩了
scp D:\docker-export\devops-agent.tar.gz user@company-server:/tmp/
```

#### 方式 B：SFTP

```powershell
# 使用 FileZilla 或 WinSCP GUI
# 上传到：/tmp/devops-agent.tar
```

#### 方式 C：内网共享（如果可用）

```powershell
# 复制到共享盘
Copy-Item D:\docker-export\devops-agent.tar \\company-share\deploy\
```

---

### 步骤 4：服务器加载镜像

SSH 登录公司服务器：

```bash
# 4.1 加载镜像
docker load -i /tmp/devops-agent.tar

# 或解压后加载
gunzip < /tmp/devops-agent.tar.gz | docker load

# 4.2 验证镜像已加载
docker images | grep devops-agent
# 输出：devops-agent  production  xxx  2 minutes ago  800MB

# 4.3 清理临时文件
rm /tmp/devops-agent.tar
```

---

### 步骤 5：创建生产环境配置

在服务器上创建 `.env` 文件：

```bash
# 创建工作目录
mkdir -p /opt/devops-agent
cd /opt/devops-agent

# 创建 .env 文件
cat > .env << 'EOF'
# LLM 配置 - 公司 Higress 网关
DEEPSEEK_API_KEY=610b268c-a36e-4a47-a8ed-386787eb26af
DEEPSEEK_BASE_URL=https://higress.devops.ecp.digitalvolvo.com/gateway/v1/chat/completions
DEEPSEEK_MODEL=deepseek-reasoner

# 数据库配置
DATABASE_URL=sqlite:///./data/devops_agent.db
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=dhuci_agent_db

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# 日志配置
LOG_LEVEL=INFO
EOF

# 设置权限
chmod 600 .env
```

---

### 步骤 6：启动服务

#### 方式 A：直接运行（简单）

```bash
# 启动容器
docker run -d \
  --name devops-agent \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  -v /opt/devops-agent/data:/app/data \
  -v /opt/devops-agent/logs:/app/logs \
  devops-agent:production

# 查看日志
docker logs -f devops-agent

# 测试接口
curl http://localhost:8000/api/v1/health
```

#### 方式 B：使用 Docker Compose（推荐）

```bash
# 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  devops-agent:
    image: devops-agent:production
    container_name: devops-agent
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

---

## 🔄 更新部署流程

当代码更新时：

```powershell
# 1. 本地重新构建
docker build -f docker/Dockerfile.pyc -t devops-agent:production .

# 2. 保存新版本
docker save devops-agent:production -o D:\docker-export\devops-agent-v2.tar

# 3. 传输到服务器
scp D:\docker-export\devops-agent-v2.tar user@company-server:/tmp/

# 4. 服务器端更新
ssh user@company-server
docker load -i /tmp/devops-agent-v2.tar
docker-compose down
docker-compose up -d
```

---

## 🔒 安全加固

### 1. 网络安全

```bash
# 只允许内网访问
docker run -d \
  -p 127.0.0.1:8000:8000 \  # 只监听本地
  ...

# 或通过防火墙限制
firewall-cmd --add-rich-rule='rule family="ipv4" source address="10.0.0.0/8" port port="8000" protocol="tcp" accept'
```

### 2. 日志轮转

```bash
# 限制日志大小
docker run -d \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  ...
```

### 3. 资源限制

```bash
# 限制 CPU 和内存
docker run -d \
  --memory="2g" \
  --cpus="2" \
  ...
```

---

## 📊 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **离线传输（推荐）** | ✅ 零外部依赖<br>✅ 源码保护<br>✅ 简单可靠 | ⚠️ 需要手动传输<br>⚠️ 文件较大 | ⭐⭐⭐⭐⭐ |
| Docker Hub | ✅ 自动化 | ❌ 需要账号<br>❌ 国内访问困难 | ⭐ |
| 阿里云镜像 | ✅ 国内快 | ⚠️ 需要账号<br>💰 可能收费 | ⭐⭐⭐ |
| 公司 GitLab + CI/CD | ✅ 自动化<br>✅ 版本管理 | ⚠️ 需要搭建 CI/CD<br>⚠️ 复杂 | ⭐⭐⭐⭐ |
| 直接传代码 | ✅ 灵活 | ❌ 暴露源码<br>❌ 需要服务器构建 | ⭐ |

---

## 🎯 快速执行脚本

### 本地打包脚本（PowerShell）

```powershell
# deploy-package.ps1
Write-Host "开始打包部署镜像..." -ForegroundColor Green

# 构建
docker build -f docker/Dockerfile.pyc -t devops-agent:production .

# 保存
$exportPath = "$env:USERPROFILE\Desktop\devops-agent.tar.gz"
docker save devops-agent:production | gzip > $exportPath

Write-Host "✅ 打包完成！" -ForegroundColor Green
Write-Host "文件位置: $exportPath" -ForegroundColor Yellow
Write-Host "文件大小: $((Get-Item $exportPath).Length / 1MB) MB" -ForegroundColor Yellow
Write-Host ""
Write-Host "下一步：使用 WinSCP 或 scp 传输到服务器" -ForegroundColor Cyan
```

### 服务器部署脚本（Bash）

```bash
#!/bin/bash
# deploy-server.sh

echo "开始部署 DevOps Agent..."

# 加载镜像
echo "1. 加载 Docker 镜像..."
gunzip < /tmp/devops-agent.tar.gz | docker load

# 创建目录
echo "2. 创建工作目录..."
mkdir -p /opt/devops-agent/{data,logs}
cd /opt/devops-agent

# 停止旧容器
echo "3. 停止旧容器..."
docker stop devops-agent 2>/dev/null || true
docker rm devops-agent 2>/dev/null || true

# 启动新容器
echo "4. 启动新容器..."
docker run -d \
  --name devops-agent \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  devops-agent:production

# 等待启动
echo "5. 等待服务启动..."
sleep 5

# 健康检查
echo "6. 健康检查..."
curl -f http://localhost:8000/api/v1/health

echo "✅ 部署完成！"
echo "查看日志: docker logs -f devops-agent"
```

---

## 🆘 常见问题

### Q1: 传输太慢怎么办？

A: 使用压缩：
```powershell
docker save devops-agent:production | gzip > devops-agent.tar.gz
# 可以减少 50-60% 大小
```

### Q2: 服务器没有 Docker 怎么办？

A: 安装 Docker：
```bash
# CentOS/RHEL
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Ubuntu/Debian
sudo apt-get install -y docker.io
sudo systemctl start docker
```

### Q3: 如何回滚到旧版本？

A: 保留旧镜像：
```bash
# 打标签保存
docker tag devops-agent:production devops-agent:v1.0
docker tag devops-agent:production devops-agent:v2.0

# 回滚
docker stop devops-agent
docker rm devops-agent
docker run -d --name devops-agent devops-agent:v1.0 ...
```

### Q4: 能否自动化？

A: 可以，使用公司内部的工具：
- Jenkins + 内网镜像仓库
- GitLab CI/CD + Harbor
- Ansible 自动化部署

---

## 📝 部署检查清单

- [ ] 本地构建 .pyc 镜像
- [ ] 保存镜像为 tar 文件
- [ ] 传输到服务器
- [ ] 服务器加载镜像
- [ ] 创建 .env 配置文件
- [ ] 启动容器
- [ ] 测试健康检查接口
- [ ] 测试 AG-UI 流式接口
- [ ] 配置日志轮转
- [ ] 配置监控告警
- [ ] 文档化部署流程

---

## 🚀 下一步优化

1. **CI/CD 集成**（长期）
   - 搭建公司内部 GitLab
   - 配置自动构建和部署

2. **监控告警**
   - Prometheus + Grafana
   - 日志聚合（ELK）

3. **高可用**
   - 多实例部署
   - 负载均衡（Nginx）

---

## 总结

**推荐方案**：Docker 镜像离线传输
- **简单**：4 个命令完成部署
- **安全**：不依赖外部服务
- **可靠**：源码已 .pyc 保护

**立即开始**：
```powershell
# 1. 构建
docker build -f docker/Dockerfile.pyc -t devops-agent:production .

# 2. 打包
docker save devops-agent:production | gzip > devops-agent.tar.gz

# 3. 传输（使用 WinSCP）

# 4. 部署（服务器端）
gunzip < devops-agent.tar.gz | docker load
docker run -d --name devops-agent -p 8000:8000 --env-file .env devops-agent:production
```
