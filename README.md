# DevOps Agent

智能 DevOps 项目分析 Agent，基于 LangChain 和 Deepseek R1 构建。

## 项目简介

DevOps Agent 是一个智能的项目状况分析工具，能够：

- 查询测试覆盖率和测试用例执行情况
- 监控 Gerrit 代码审查和 Patchset 合并状态
- 追踪 Jenkins 构建历史和成功率
- 管理 Artifactory 制品版本
- 集成自定义后端服务的各类指标
- 生成项目健康报告和趋势分析
- 通过自然语言对话进行交互

## 技术栈

- **LLM**: Deepseek R1 (兼容 OpenAI API 格式)
- **Agent 框架**: LangChain
- **Web 框架**: FastAPI
- **数据库**: SQLAlchemy + SQLite/PostgreSQL
- **容器化**: Docker + Docker Compose

## 快速开始

### 环境要求

- Python 3.10+
- Docker (可选)

### 本地开发

1. **克隆项目**

```bash
git clone <your-repo-url>
cd devops-agent
```

2. **安装依赖**

```bash
pip install -r requirements-dev.txt
```

3. **配置环境变量**

复制环境变量示例文件并编辑：

```bash
cp configs/.env.example .env
```

编辑 `.env` 文件，至少需要配置：

```env
DEEPSEEK_API_KEY=your_actual_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

4. **初始化数据库**

```bash
python -c "from src.models.database import init_db; init_db()"
```

5. **启动服务**

```bash
python src/api/main.py
```

或使用 uvicorn：

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

6. **访问 API 文档**

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker 部署

1. **配置环境变量**

编辑 `docker/docker-compose.yml` 或创建 `.env` 文件

2. **构建并启动**

```bash
cd docker
docker-compose up -d
```

3. **查看日志**

```bash
docker-compose logs -f devops-agent
```

4. **停止服务**

```bash
docker-compose down
```

## API 使用示例

### 1. 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

### 2. 对话查询

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请查询 my-project 的测试覆盖率情况",
    "session_id": null
  }'
```

### 3. 项目分析

```bash
curl -X POST http://localhost:8000/api/v1/analysis/project \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-project"
  }'
```

### 4. 生成报告

```bash
curl -X POST http://localhost:8000/api/v1/analysis/report \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-project",
    "report_type": "weekly"
  }'
```

### 5. 查询趋势

```bash
curl "http://localhost:8000/api/v1/analysis/trend?project=my-project&metric=coverage&days=30"
```

## 可用工具

Agent 集成了以下工具：

1. **test_coverage**: 查询测试覆盖率
2. **test_cases**: 查询测试用例执行情况
3. **gerrit**: 查询 Gerrit Patchset 和代码审查
4. **jenkins**: 查询 Jenkins 构建状态
5. **artifactory**: 查询 Artifactory 制品版本
6. **custom_backend**: 查询自定义后端服务

## 项目结构

```
devops-agent/
├── src/
│   ├── agent/          # Agent 核心
│   ├── tools/          # DevOps 工具集
│   ├── api/            # FastAPI 路由
│   ├── models/         # 数据模型
│   ├── services/       # 业务逻辑
│   ├── utils/          # 工具函数
│   └── config.py       # 配置管理
├── tests/              # 测试代码
├── docker/             # Docker 配置
├── configs/            # 配置文件
└── docs/               # 文档
```

## 配置说明

### 核心配置

在 `.env` 文件中配置：

```env
# LLM 配置
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 数据库 (SQLite)
DATABASE_URL=sqlite:///./devops_agent.db

# 数据库 (PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/devops_agent

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
```

### 外部服务配置

配置 Jenkins、Gerrit、Artifactory 等服务的连接信息：

```env
JENKINS_URL=http://your-jenkins:8080
JENKINS_USER=your_user
JENKINS_TOKEN=your_token

GERRIT_URL=http://your-gerrit:8080
GERRIT_USER=your_user
GERRIT_PASSWORD=your_password

ARTIFACTORY_URL=http://your-artifactory:8081
ARTIFACTORY_API_KEY=your_api_key

CUSTOM_BACKEND_URL=http://your-backend:3000
CUSTOM_BACKEND_API_KEY=your_api_key
```

## 开发指南

### 添加新工具

1. 在 `src/tools/` 下创建新的工具文件
2. 继承 `DevOpsBaseTool` 类
3. 实现 `_execute` 方法
4. 在 `src/agent/devops_agent.py` 中注册工具

示例：

```python
from src.tools.base import DevOpsBaseTool

class MyNewTool(DevOpsBaseTool):
    name: str = "my_tool"
    description: str = "My tool description"

    def _execute(self, query: str) -> dict:
        # 实现工具逻辑
        return {"result": "data"}
```

### 运行测试

```bash
pytest tests/ -v
```

### 代码质量检查

```bash
# 格式化代码
black src/ tests/

# Lint 检查
ruff check src/ tests/

# 类型检查
mypy src/
```

## 注意事项

1. **API Key 安全**: 不要将 API Key 提交到代码库
2. **Mock 数据**: 当前所有外部 API 调用都使用 Mock 数据，需要替换为实际 API
3. **数据库迁移**: 使用 Alembic 管理数据库变更
4. **日志**: 查看 `logs/` 目录下的日志文件

## 后续开发

- [ ] 替换 Mock API 为实际 API 调用
- [ ] 添加用户认证和权限管理
- [ ] 实现 WebSocket 实时流式响应
- [ ] 添加更多 DevOps 工具集成
- [ ] 实现定时任务和自动报告
- [ ] 添加 Web Dashboard
- [ ] 完善单元测试和集成测试

## 许可证

MIT License

## 联系方式

如有问题，请联系 DevOps 团队。
