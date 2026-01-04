# DHUCI Agent 快速启动指南

## 项目状态

项目已成功修复所有依赖问题，服务可以正常启动！

## 完成的修复

### 1. LangChain 导入问题修复

在 LangChain 1.2+ 版本中，旧的 API 已迁移到 `langchain_classic` 和 `langchain_core` 包中。

修改的文件：
- `src/agent/devops_agent.py` - 使用 `langchain_classic.agents`
- `src/agent/memory.py` - 使用 `langchain_classic.memory`
- `src/agent/mongodb_memory.py` - 使用 `langchain_classic.memory` 和 `langchain_core.messages`
- `src/agent/prompts.py` - 使用 `langchain_core.prompts`
- `src/tools/base.py` - 使用 `langchain_core.tools` 和 `langchain_core.callbacks`

### 2. 依赖配置修复

- 修复了 `requirements.txt` 的编码问题（移除中文注释）
- 简化了 `configs/logging.yaml`（移除未使用的 JSON formatter）
- 添加了 MongoDB 依赖：pymongo, motor

### 3. 启动容错处理

修改了 `src/api/main.py` 的启动事件，使服务在 MongoDB 不可用时也能正常启动：
```python
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("初始化 MongoDB 连接...")
    try:
        MongoDBManager.init_indexes()
        logger.info("MongoDB 连接成功")
    except Exception as e:
        logger.warning(f"MongoDB 连接失败: {str(e)}")
        logger.warning("服务将继续运行，但数据持久化功能不可用")

    logger.info("DHUCI Agent API 启动成功")
```

## 启动服务

### 1. 激活虚拟环境并安装依赖

```bash
# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# Linux/Mac
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件，至少需要配置：

```env
# LLM Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# MongoDB Configuration (可选)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=dhuci_agent_db
```

### 3. 启动服务

```bash
# 方式 1: 使用 uvicorn（推荐开发环境）
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload

# 方式 2: 使用 run.py
python run.py
```

### 4. 访问服务

- **API 文档**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/api/v1/health
- **根路径**: http://127.0.0.1:8000/

## 测试示例

### 健康检查

```bash
curl http://127.0.0.1:8000/api/v1/health
```

响应：
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-01-04T19:59:55.827763"
}
```

### 对话接口（需要配置 API Key）

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "测试覆盖率如何？",
    "session_id": null
  }'
```

## 下一步配置

### 1. 配置 MongoDB（必需，用于数据持久化）

参考 `docs/MONGODB_SETUP.md` 配置您的 MongoDB 连接。

更新 `.env` 文件：
```env
MONGODB_URL=your_mongodb_connection_string
MONGODB_DATABASE=dhuci_agent_db
```

然后运行初始化脚本：
```bash
python init_mongodb.py
```

### 2. 配置 Deepseek API Key（必需，用于 LLM）

在 `.env` 文件中配置：
```env
DEEPSEEK_API_KEY=your_actual_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 3. 配置实际的 DevOps API（可选）

当前所有工具使用 Mock 数据。要使用实际数据，需要配置：

- Jenkins URL 和凭证
- Gerrit URL 和凭证
- Artifactory URL 和凭证
- 自定义后端 API

在 `.env` 文件中配置相关参数。

## 故障排查

### 服务无法启动

1. 检查 Python 版本（需要 3.8+）
2. 确保虚拟环境已激活
3. 重新安装依赖：`pip install --force-reinstall -r requirements.txt`
4. 检查端口 8000 是否被占用

### MongoDB 连接失败

这不会阻止服务启动，但会影响数据持久化功能。服务会显示警告但继续运行。

要解决此问题：
1. 确保 MongoDB 服务正在运行
2. 检查 `.env` 中的 MONGODB_URL 配置
3. 测试连接：`python init_mongodb.py`

### API 调用失败

1. 检查是否配置了 `DEEPSEEK_API_KEY`
2. 检查 API Key 是否有效
3. 查看日志文件：`logs/devops_agent.log`

## 项目结构

```
InitialProject/
├── src/
│   ├── agent/          # Agent 核心模块
│   ├── api/            # FastAPI 路由
│   ├── models/         # 数据模型
│   ├── tools/          # LangChain 工具
│   └── utils/          # 工具函数
├── configs/            # 配置文件
├── docs/               # 文档
├── logs/               # 日志（自动创建）
└── .env                # 环境变量
```

## 开发建议

1. **日志监控**: 查看 `logs/devops_agent.log` 了解运行详情
2. **API 文档**: 访问 `/docs` 查看完整的 API 文档
3. **热重载**: 使用 `--reload` 参数启动服务，代码修改会自动重启
4. **测试**: 使用 Postman 或 curl 测试 API 接口

## 联系支持

如有问题，请检查：
1. `logs/` 目录中的日志文件
2. 控制台输出的错误信息
3. MongoDB 连接状态
4. API Key 配置
