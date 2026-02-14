# RAG FastAPI 接口文档

本接口文档基于当前后端代码与测试脚本整理，供前端开发对接使用。

## Base URL

```
http://127.0.0.1:8000
```

## 通用说明

- 请求体均为 JSON，Header 使用 `Content-Type: application/json`。
- 会话通过 `session_id` 标识，需先调用会话初始化接口。
- `use_retrieval=true` 时走 RAG 检索流程，`use_retrieval=false` 时走无检索 LLM 对话。
- `retrieved_docs` 可能是字符串列表或对象列表，具体取决于 UltraRAG Pipeline 输出。
- `retrieved_images` 为从检索结果中提取的图片路径列表。

## 数据结构

### MessageInput

```json
{
  "content": "用户问题",
  "use_retrieval": true,
  "top_k": 5
}
```

### SessionInit

```json
{
  "session_id": "uuid",
  "created_at": "2026-02-14T11:41:12.209494"
}
```

### Turn

```json
{
  "turn_id": 0,
  "query": "用户问题",
  "answer": "模型回答",
  "use_retrieval": true,
  "timestamp": "2026-02-14T11:41:12.209494",
  "status": "success",
  "retrieved_docs": ["/path/a.jpg", "..."],
  "retrieved_images": ["/path/a.jpg"]
}
```

### ChatResponse

```json
{
  "session_id": "uuid",
  "turn_id": 0,
  "query": "用户问题",
  "answer": "模型回答",
  "use_retrieval": true,
  "status": "success",
  "timestamp": "2026-02-14T11:41:12.209494",
  "retrieved_docs": ["/path/a.jpg", "..."],
  "retrieved_images": ["/path/a.jpg"],
  "conversation_history": [
    { "turn_id": 0, "query": "...", "answer": "...", "use_retrieval": true, "timestamp": "...", "status": "success", "retrieved_docs": [], "retrieved_images": [] }
  ]
}
```

### FeedbackInput

```json
{
  "session_id": "uuid",
  "turn_id": 0,
  "feedback_text": "可选",
  "category": "general",
  "user_id": "optional_user",
  "score": 5
}
```

### SuggestionInput

```json
{
  "session_id": "uuid",
  "turn_id": 0,
  "suggested_answer": "更好的回答",
  "reason": "可选",
  "user_id": "optional_user",
  "score": 5
}
```

## 接口列表

### 1) 健康检查

- Method: `GET`
- Path: `/health`

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-14T11:41:12.209494"
}
```

### 2) 初始化会话

- Method: `POST`
- Path: `/api/sessions/init`

Response: `SessionInit`

### 3) 发送对话（非流式）

- Method: `POST`
- Path: `/api/chat?session_id={session_id}`
- Body: `MessageInput`

Response: `ChatResponse`

说明:
- 当 `use_retrieval=true`，返回 `retrieved_docs` 与 `retrieved_images`。
- 当 `use_retrieval=false`，两者为空数组。

### 4) 发送对话（流式）

- Method: `POST`
- Path: `/api/chat/stream?session_id={session_id}`
- Body: `MessageInput`

说明:
- 仅支持 `use_retrieval=false`。
- 返回 `text/plain` 字符流（非 JSON）。

### 5) 获取会话信息

- Method: `GET`
- Path: `/api/sessions/{session_id}`

Response:
```json
{
  "session_id": "uuid",
  "created_at": "2026-02-14T11:41:12.209494",
  "start_time": "2026-02-14T11:41:12.209494",
  "total_turns": 3,
  "duration_seconds": 12.34,
  "conversation_history": ["Turn", "..."]
}
```

### 6) 保存会话

- Method: `POST`
- Path: `/api/sessions/{session_id}/save`

Response:
```json
{
  "status": "success",
  "message": "会话已保存",
  "saved_path": "/root/workspace/RAGWorkProject/config/logs/session_xxx.json"
}
```

### 7) 删除会话

- Method: `DELETE`
- Path: `/api/sessions/{session_id}`

Response:
```json
{
  "status": "success",
  "message": "会话已删除，数据已保存",
  "saved_path": "/root/workspace/RAGWorkProject/config/logs/session_xxx.json"
}
```

### 8) 点赞反馈

- Method: `POST`
- Path: `/api/feedback/like?session_id={session_id}&turn_id={turn_id}&reason={reason?}&user_id={user_id?}`

Response:
```json
{
  "status": "success",
  "message": "点赞反馈已保存",
  "saved_path": "/root/workspace/RAGWorkProject/config/feedback/...json"
}
```

### 9) 详细反馈

- Method: `POST`
- Path: `/api/feedback/detailed?session_id={session_id}`
- Body: `FeedbackInput`

说明:
- `session_id` 同时出现在 query 与 body，建议保持一致。

### 10) 提交更好建议

- Method: `POST`
- Path: `/api/feedback/suggest?session_id={session_id}`
- Body: `SuggestionInput`

说明:
- `session_id` 同时出现在 query 与 body，建议保持一致。

## 错误码

- `400`: 参数不合法或流式接口请求了检索模式。
- `404`: 会话不存在。
- `422`: 请求参数校验失败。

## 示例（与测试脚本一致）

### 初始化会话

```bash
curl -X POST http://127.0.0.1:8000/api/sessions/init
```

### RAG 检索对话

```bash
curl -X POST "http://127.0.0.1:8000/api/chat?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"content":"如何提交我写好的python训练程序？","use_retrieval":true,"top_k":5}'
```

### 无检索对话

```bash
curl -X POST "http://127.0.0.1:8000/api/chat?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"content":"再详细解释一下第一步","use_retrieval":false}'
```

### 流式对话

```bash
curl -N -X POST "http://127.0.0.1:8000/api/chat/stream?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"content":"你好","use_retrieval":false}'
```

### 运行测试脚本

```bash
./test_simple.sh
```
