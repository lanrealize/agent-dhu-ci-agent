# 公司服务器快速部署指南

## 🎯 推荐方案：Docker 镜像离线传输

**为什么？**
- ✅ 不需要 Docker Hub（国内访问困难）
- ✅ 不暴露个人 Docker 账号
- ✅ 不通过 GitHub 暴露源码
- ✅ 源码已通过 .pyc 字节码保护
- ✅ 简单可靠，4 步完成部署

---

## 📋 部署流程（4 步）

### 第 1 步：本地打包（Windows）

```powershell
# 在项目目录运行
.\scripts\deploy-package.ps1
```

**自动完成**：
- ✅ 构建 .pyc 保护的 Docker 镜像
- ✅ 保存并压缩为 tar.gz 文件
- ✅ 输出到桌面 `devops-deploy` 文件夹
- 📦 文件大小：约 300-400 MB

---

### 第 2 步：传输到服务器

使用 **WinSCP** 或 **FileZilla**：

```
本地文件: C:\Users\你的用户名\Desktop\devops-deploy\devops-agent.tar.gz
上传到:   /tmp/devops-agent.tar.gz (服务器)
```

或使用命令行：

```powershell
# PowerShell
scp $env:USERPROFILE\Desktop\devops-deploy\devops-agent.tar.gz user@company-server:/tmp/
```

---

### 第 3 步：部署脚本传输

将部署脚本也传到服务器：

```powershell
scp .\scripts\deploy-server.sh user@company-server:/tmp/
```

---

### 第 4 步：服务器部署

SSH 登录服务器后：

```bash
# 赋予执行权限
chmod +x /tmp/deploy-server.sh

# 执行部署
sudo /tmp/deploy-server.sh
```

**自动完成**：
- ✅ 加载 Docker 镜像
- ✅ 创建工作目录
- ✅ 创建环境配置（.env）
- ✅ 停止旧容器
- ✅ 启动新容器
- ✅ 健康检查
- ✅ 清理临时文件

---

## ✅ 部署完成！

### 验证服务

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 查看日志
docker logs -f devops-agent

# 测试聊天接口
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "session_id": null}'
```

### 服务地址

- **健康检查**: http://server-ip:8000/api/v1/health
- **API 文档**: http://server-ip:8000/docs
- **聊天接口**: http://server-ip:8000/api/v1/chat/stream

---

## 🔄 更新部署

代码更新后：

```powershell
# 1. 本地重新打包
.\scripts\deploy-package.ps1

# 2. 传输新文件
scp $env:USERPROFILE\Desktop\devops-deploy\devops-agent.tar.gz user@server:/tmp/

# 3. 服务器重新部署
ssh user@server 'sudo /tmp/deploy-server.sh'
```

---

## 🛠 常用命令

```bash
# 查看日志
docker logs -f devops-agent

# 重启服务
docker restart devops-agent

# 停止服务
docker stop devops-agent

# 查看状态
docker ps | grep devops-agent

# 进入容器（调试）
docker exec -it devops-agent /bin/bash

# 修改配置
sudo vim /opt/devops-agent/.env
docker restart devops-agent
```

---

## 📊 配置文件

### 服务器配置位置

```
/opt/devops-agent/
├── .env              # 环境配置（API Key 等）
├── data/             # 数据库文件
│   └── devops_agent.db
└── logs/             # 日志文件
    └── app.log
```

### 修改 API 配置

```bash
# 编辑配置
sudo vim /opt/devops-agent/.env

# 修改以下配置
DEEPSEEK_API_KEY=你的新Key
DEEPSEEK_BASE_URL=你的新URL

# 重启生效
docker restart devops-agent
```

---

## 🆘 常见问题

### Q: 打包脚本报错找不到 Docker？

A: 确保 Docker Desktop 已启动：
```powershell
# 检查 Docker
docker --version
```

### Q: 传输文件太慢？

A: 镜像已经压缩过，如果还是慢：
- 使用公司内网
- 或在非高峰时段传输

### Q: 服务器加载镜像失败？

A: 检查 Docker 版本：
```bash
docker --version  # 需要 20.10+
```

### Q: 健康检查失败？

A: 检查配置：
```bash
# 查看日志
docker logs devops-agent

# 检查 API Key 是否正确
cat /opt/devops-agent/.env
```

### Q: 如何回滚到旧版本？

A: 保留旧镜像：
```bash
# 部署新版本前打标签
docker tag devops-agent:production devops-agent:backup-$(date +%Y%m%d)

# 回滚
docker stop devops-agent && docker rm devops-agent
docker run -d --name devops-agent ... devops-agent:backup-20260105
```

---

## 📞 支持

- 完整文档：`docs/COMPANY_DEPLOYMENT.md`
- 源码保护：`docs/PYC_PROTECTION.md`
- Docker 部署：`docs/DOCKER_DEPLOYMENT.md`

---

## 🔒 安全提示

1. **不要提交 .env 文件**：已在 .gitignore 中排除
2. **保护 API Key**：不要在日志中打印
3. **限制网络访问**：使用防火墙限制端口访问
4. **定期更新**：保持依赖包和 Docker 镜像最新

---

## 📈 监控建议（可选）

```bash
# 查看资源使用
docker stats devops-agent

# 查看容器日志大小
du -sh /var/lib/docker/containers/$(docker inspect -f '{{.Id}}' devops-agent)

# 定期清理旧镜像
docker image prune -a
```

---

**准备开始？运行第一步命令：**

```powershell
.\scripts\deploy-package.ps1
```
