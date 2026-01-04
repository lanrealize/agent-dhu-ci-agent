# 如何在 Windows 终端看到流式效果

## 问题原因

在 Windows 的 cmd 或 PowerShell 中看不到流式效果，主要原因：
1. Python 输出缓冲
2. 终端缓冲
3. 脚本没有强制刷新输出

## ✅ 推荐方法（最佳）

### 方法1: 使用优化的交互式脚本

```cmd
cd D:\Codes\Agents\InitialProject
.venv\Scripts\python.exe -u demo_stream_interactive.py
```

**重要**:
- 必须加 `-u` 参数（禁用 Python 缓冲）
- 看到菜单后选择 1 或 2

### 方法2: 使用 curl（实时效果最好）

在 PowerShell 中：

```powershell
cd D:\Codes\Agents\InitialProject

# 简单查询
curl.exe -N -X POST http://127.0.0.1:8006/api/v1/chat/stream `
  -H "Content-Type: application/json" `
  -d '{\"message\": \"请查询 my-project 的测试覆盖率\", \"session_id\": null}'
```

在 cmd 中：

```cmd
cd D:\Codes\Agents\InitialProject

curl.exe -N -X POST http://127.0.0.1:8006/api/v1/chat/stream ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"请查询 my-project 的测试覆盖率\", \"session_id\": null}"
```

**重要**:
- 必须使用 `curl.exe`（不是 curl 别名）
- 必须加 `-N` 参数（禁用缓冲）

## 📝 完整演示步骤

### Step 1: 确保服务运行

```cmd
cd D:\Codes\Agents\InitialProject
.venv\Scripts\uvicorn.exe src.api.main:app --host 127.0.0.1 --port 8006
```

### Step 2: 打开新的终端窗口

### Step 3: 运行演示脚本

```cmd
cd D:\Codes\Agents\InitialProject
.venv\Scripts\python.exe -u demo_stream_interactive.py
```

### Step 4: 选择测试场景

```
请选择测试场景:
1. 简单查询（1个工具）      <- 推荐先试这个
2. 综合分析（5个工具）      <- 看到多个工具的流式效果
3. 退出

请输入选择 (1-3): 1
```

## 🎬 预期效果

你应该看到类似这样的**实时输出**：

```
[21:05:23] >>> 开始发送请求...
[21:05:23] >>> 连接建立，等待响应...

[21:05:24] [START] 会话已创建: b3192b5e...

[21:05:25] [THINK] Agent 正在分析问题...
[21:05:26] [ACTION] 决定调用工具: test_coverage
[21:05:27] [TOOL] 正在调用第 1 个工具: test_coverage
        . . .等待工具返回...
[21:05:32] [TOOL] 工具返回成功 [8.3s]

[21:05:33] [THINK] Agent 正在分析问题...
[21:05:34] [DONE] Agent 完成分析，正在生成回答...

--------------------------------------------------------------------------------
最终回答:
--------------------------------------------------------------------------------

my-project项目的测试覆盖率情况如下：... (打字机效果显示)
```

**关键特征**：
- ✅ 每一行都**立即显示**
- ✅ 看到"等待工具返回"的动画
- ✅ 看到时间戳在变化
- ✅ 最后的答案有**打字机效果**

## ❌ 如果还是看不到流式效果

### 可能原因1: 没有加 -u 参数

❌ 错误:
```cmd
.venv\Scripts\python.exe demo_stream_interactive.py
```

✅ 正确:
```cmd
.venv\Scripts\python.exe -u demo_stream_interactive.py
```

### 可能原因2: 使用了 PowerShell 的 curl 别名

❌ 错误:
```powershell
curl -N ...
```

✅ 正确:
```powershell
curl.exe -N ...
```

### 可能原因3: Windows Terminal 缓冲设置

在 Windows Terminal 设置中，确保：
- 关闭"快速编辑模式"
- 关闭"插入模式"

### 可能原因4: 服务没运行

检查服务：
```cmd
curl http://127.0.0.1:8006/api/v1/health
```

应该返回：
```json
{"status":"healthy","version":"0.1.0","timestamp":"..."}
```

## 🔧 故障排查

### 测试1: 检查 curl 是否支持流式

```cmd
curl.exe -N http://httpbin.org/stream/3
```

应该看到**实时输出** 3 行 JSON。

### 测试2: 检查 Python 是否禁用缓冲

```cmd
.venv\Scripts\python.exe -u -c "import sys; print('Line 1', flush=True); import time; time.sleep(2); print('Line 2', flush=True)"
```

应该看到 Line 1 立即显示，2秒后显示 Line 2。

### 测试3: 直接用 curl 测试流式 API

```cmd
curl.exe -N -X POST http://127.0.0.1:8006/api/v1/chat/stream ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"你好\", \"session_id\": null}"
```

应该看到：
```
data: {"type": "start", ...}
data: {"type": "thinking", ...}
...
```

## 📌 最简单的验证方法

如果上面的都不行，用这个**最简单的方法**验证流式 API 是否工作：

### Windows:

1. 安装 Git Bash（如果没有）
2. 在 Git Bash 中运行：

```bash
curl -N -X POST http://127.0.0.1:8006/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "session_id": null}'
```

### 或者用浏览器：

1. 打开 http://127.0.0.1:8006/docs
2. 找到 `POST /api/v1/chat/stream`
3. 点击 "Try it out"
4. 输入请求体：
   ```json
   {
     "message": "你好",
     "session_id": null
   }
   ```
5. 点击 Execute

**应该看到实时的事件流！**

## 💡 提示

如果你在 **PyCharm** 或 **VS Code** 的终端中运行，可能有额外的缓冲。
建议使用**独立的 cmd 或 PowerShell 窗口**。

## 📞 仍然无法解决？

请提供：
1. 使用的终端类型（cmd / PowerShell / Windows Terminal）
2. Python 版本：`.venv\Scripts\python.exe --version`
3. 运行的完整命令
4. 看到的输出（截图或文字）
