# MongoDB 配置说明

## 数据库命名

基于您的 Agent 名字 **DHUCIAgent**，数据库命名如下：

- **数据库名**: `dhuci_agent_db`
- **Collections**:
  - `conversations`: 对话历史（包含完整的 agent 执行步骤）
  - `analysis_records`: 分析记录
  - `reports`: 生成的报告

## 配置步骤

### 1. 更新环境变量

编辑 `.env` 文件，配置你的 MongoDB 连接：

```env
# MongoDB 配置
MONGODB_URL=你的MongoDB地址
MONGODB_DATABASE=dhuci_agent_db
```

例如：
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=dhuci_agent_db
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库

运行初始化脚本，创建索引并测试连接：

```bash
python init_mongodb.py
```

你会看到类似的输出：
```
============================================================
MongoDB 数据库初始化
============================================================

连接信息:
  MongoDB URL: mongodb://localhost:27017
  数据库名称: dhuci_agent_db
  集合列表:
    - conversations (对话历史)
    - analysis_records (分析记录)
    - reports (报告)

正在连接 MongoDB...
✓ MongoDB 连接成功
✓ 数据库 'dhuci_agent_db' 已连接

正在创建索引...
✓ 索引创建完成

索引信息:
  conversations:
    - _id_: {'_id': 1}
    - session_id_1: {'session_id': 1}
    - updated_at_-1: {'updated_at': -1}
    ...

✓ 数据库初始化完成
============================================================
```

### 4. 启动服务

```bash
python run.py
```

或者：

```bash
python src/api/main.py
```

### 5. 访问 API 文档

打开浏览器访问：
- http://localhost:8000/docs

## 数据结构说明

### conversations 集合

```javascript
{
  "_id": ObjectId("..."),
  "session_id": "abc-123-def-456",  // 会话 ID (唯一)
  "user_id": null,  // 可选：用户 ID
  "title": null,    // 可选：对话标题

  // 所有对话轮次
  "turns": [
    {
      "turn_id": 1,
      "user_input": "测试覆盖率如何？",

      // 完整的 Agent 执行步骤（用于前端展示）
      "agent_steps": [
        {
          "step_number": 1,
          "thought": "需要查询测试覆盖率",
          "action": "test_coverage",
          "action_input": {"project": "my-project"},
          "observation": "{...}",
          "duration_ms": 234,
          "timestamp": ISODate("...")
        }
      ],

      // 最终回复（用于 LLM 上下文）
      "final_response": "测试覆盖率为 75.8%",

      "total_tokens": 1850,
      "duration_ms": 3400,
      "timestamp": ISODate("...")
    }
  ],

  "metadata": {},
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

## 主要改动

1. **移除 SQLAlchemy 依赖**：Agent 和 API 不再依赖 `db: Session` 参数
2. **新的 Memory 类**：`MongoDBConversationMemory` 替代 `PersistentConversationMemory`
3. **完整步骤存储**：对话记录包含完整的 `agent_steps`（Thought/Action/Observation）
4. **分离存储和推理**：
   - 存储：完整的执行步骤（用于前端展示和调试）
   - LLM 上下文：只发送最终的 Q&A（节省 token）

## 测试

### 测试对话接口

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "测试覆盖率如何？",
    "session_id": null
  }'
```

### 查看数据库

使用 MongoDB Compass 或命令行：

```bash
mongosh
use dhuci_agent_db
db.conversations.find().pretty()
```

## 注意事项

- MongoDB 连接默认无用户名密码，如需配置请修改 `MONGODB_URL`
- 数据库初始化脚本会自动创建索引，无需手动创建
- 对话历史会自动保存到 MongoDB，支持跨会话恢复
