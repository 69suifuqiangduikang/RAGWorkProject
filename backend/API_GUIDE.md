# RAG API 快速开始指南

## API概览

本API为RAG多轮对话系统的FastAPI封装，支持：
- 多轮对话管理
- 检索模式和无检索模式切换
- 流式响应（无检索模式）
- 用户反馈和建议收集

## 快速启动

### 1. 安装依赖

```bash
pip install fastapi uvicorn
```

### 2. 启动服务

```bash
cd /root/workspace/RAGWorkProject/backend
python run_api.py
```

服务将在 `http://127.0.0.1:8000` 启动。

### 3. 查看API文档

- **交互式文档**: http://127.0.0.1:8000/docs (Swagger UI)
- **ReDoc文档**: http://127.0.0.1:8000/redoc

## API端点说明

### 会话管理

#### 初始化会话
```bash
POST /api/sessions/init
```

**请求**: 无需参数

**响应**:
```json
{
  "session_id": "abc123...",
  "created_at": "2026-01-27T15:00:00"
}
```

#### 获取会话信息
```bash
GET /api/sessions/{session_id}
```

**响应**: 包含对话历史和会话信息

#### 保存会话
```bash
POST /api/sessions/{session_id}/save
```

**响应**:
```json
{
  "status": "success",
  "saved_path": "/path/to/session.json"
}
```

#### 删除会话
```bash
DELETE /api/sessions/{session_id}
```

---

### 对话接口

#### 发送消息（非流式）
```bash
POST /api/chat?session_id={session_id}

Content-Type: application/json
{
  "content": "如何提交我写好的python训练程序？",
  "use_retrieval": true,
  "top_k": 5
}
```

**响应**:
```json
{
  "session_id": "abc123...",
  "turn_id": 0,
  "query": "如何提交我写好的python训练程序？",
  "answer": "根据提供的文档图片，提交写好的 Python 训练程序...",
  "use_retrieval": true,
  "status": "success",
  "timestamp": "2026-01-27T15:00:00",
  "conversation_history": [...]
}
```

#### 发送消息（流式响应）
```bash
POST /api/chat/stream?session_id={session_id}

Content-Type: application/json
{
  "content": "你好，请介绍一下自己",
  "use_retrieval": false,
  "top_k": 5
}
```

**响应**: 流式文本，可逐字符接收

> **注意**: 流式接口仅支持无检索模式（`use_retrieval: false`）。检索模式请使用非流式接口。

---

### 反馈接口

#### 点赞反馈
```bash
POST /api/feedback/like?session_id={session_id}&turn_id=0&reason=回答很全面&user_id=user123
```

**响应**:
```json
{
  "status": "success",
  "message": "点赞反馈已保存",
  "saved_path": "/path/to/feedback.json"
}
```

#### 详细反馈
```bash
POST /api/feedback/detailed?session_id={session_id}

Content-Type: application/json
{
  "turn_id": 0,
  "feedback_text": "答案缺少具体代码示例",
  "category": "完整性",
  "user_id": "user123",
  "score": 4
}
```

#### 建议更好的答案
```bash
POST /api/feedback/suggest?session_id={session_id}

Content-Type: application/json
{
  "turn_id": 0,
  "suggested_answer": "建议的答案内容...",
  "reason": "原答案太简洁，建议补充步骤",
  "user_id": "user123",
  "score": 5
}
```

---

## 使用示例

### Python 客户端示例

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# 1. 初始化会话
response = requests.post(f"{BASE_URL}/api/sessions/init")
session_data = response.json()
session_id = session_data["session_id"]
print(f"创建会话: {session_id}")

# 2. 发送第一条消息（使用检索）
message = {
    "content": "如何提交我写好的python训练程序？",
    "use_retrieval": True,
    "top_k": 5
}
response = requests.post(
    f"{BASE_URL}/api/chat?session_id={session_id}",
    json=message
)
result = response.json()
print(f"回答: {result['answer']}")

# 3. 发送第二条消息（无检索，流式）
message = {
    "content": "有什么注意事项吗？",
    "use_retrieval": False
}
response = requests.post(
    f"{BASE_URL}/api/chat/stream?session_id={session_id}",
    json=message,
    stream=True
)
print("流式回答: ", end="", flush=True)
for chunk in response.iter_content(decode_unicode=True):
    print(chunk, end="", flush=True)
print()

# 4. 点赞反馈
response = requests.post(
    f"{BASE_URL}/api/feedback/like",
    params={
        "session_id": session_id,
        "turn_id": 0,
        "reason": "回答很全面",
        "user_id": "user123"
    }
)
print(f"反馈: {response.json()}")

# 5. 保存会话
response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/save")
print(f"保存路径: {response.json()['saved_path']}")
```

### cURL 示例

```bash
# 初始化会话
SESSION_ID=$(curl -s -X POST http://127.0.0.1:8000/api/sessions/init | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

# 发送消息
curl -X POST "http://127.0.0.1:8000/api/chat?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "如何提交我写好的python训练程序？",
    "use_retrieval": true,
    "top_k": 5
  }' | jq '.'

# 流式对话
curl -X POST "http://127.0.0.1:8000/api/chat/stream?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好",
    "use_retrieval": false
  }'

# 点赞
curl -X POST "http://127.0.0.1:8000/api/feedback/like?session_id=$SESSION_ID&turn_id=0&reason=很好" \
  | jq '.'
```

---

## 数据模型

### MessageInput
- `content` (str): 消息内容
- `use_retrieval` (bool): 是否使用检索，默认 true
- `top_k` (int): 检索文档数，默认 5

### ChatResponse
- `session_id` (str): 会话ID
- `turn_id` (int): 当前轮次
- `query` (str): 用户查询
- `answer` (str): 系统回答
- `use_retrieval` (bool): 是否使用检索
- `status` (str): success/error
- `timestamp` (str): ISO 8601时间戳
- `conversation_history` (List[Turn]): 对话历史

### FeedbackInput
- `turn_id` (int): 反馈的轮次ID
- `feedback_text` (str): 反馈文本
- `category` (str): 反馈类别（如"完整性"、"准确性"）
- `user_id` (str, optional): 用户ID
- `score` (int, optional): 评分 1-5

### SuggestionInput
- `turn_id` (int): 建议涉及的轮次
- `suggested_answer` (str): 建议的答案
- `reason` (str): 建议原因
- `user_id` (str, optional): 用户ID
- `score` (int, optional): 评分 1-5

---

## 会话管理

### 内存中的会话存储
- 会话默认存储在内存中
- 服务器重启后会丢失
- 可通过 `/api/sessions/{session_id}/save` 保存到文件

### 会话生命周期
1. 客户端调用 `/api/sessions/init` 创建会话
2. 后续所有操作使用返回的 `session_id`
3. 会话数据持久化存储在 `/root/workspace/RAGWorkProject/config/logs/`
4. 可随时调用 `/api/sessions/{session_id}/save` 手动保存

---

## 常见问题

### Q: 流式接口返回什么格式？
A: 流式接口返回纯文本，逐字符返回。前端可以实时渲染。

### Q: 多轮对话如何实现？
A: 会话ID确保同一用户的多轮对话被关联。每次请求返回完整的`conversation_history`，下次请求时系统会根据历史调整行为。

### Q: 反馈数据存储在哪里？
A: 反馈和建议分别保存在：
- `/root/workspace/RAGWorkProject/config/feedback/`
- `/root/workspace/RAGWorkProject/config/better_suggestions/`

### Q: 如何扩展会话存储？
A: 当前实现使用内存字典。生产环境建议：
1. 使用数据库（Redis、PostgreSQL等）存储会话
2. 实现会话过期机制
3. 添加认证/授权

---

## 部署注意事项

### 开发环境
```bash
python run_api.py
```

### 生产环境
```bash
# 使用gunicorn + uvicorn
pip install gunicorn

gunicorn api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 健康检查
```bash
curl http://127.0.0.1:8000/health
```

---

## 许可证

与RAG系统相同的许可证
