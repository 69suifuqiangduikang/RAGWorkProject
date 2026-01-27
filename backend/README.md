# RAG系统后端 - FastAPI 版本

这是基于UltraRAG的RAG系统后端实现，支持多轮对话、灵活的检索控制、完整的反馈管理，并提供了完整的 FastAPI RESTful API 接口。

## 🌟 最新更新

### ✅ FastAPI API 封装（新增）
- 完整的 RESTful API 接口
- 流式响应支持（SSE）
- 自动生成的交互式文档
- CORS 跨域支持

### ✅ 流式调用支持（新增）
- RAG 查询流式返回
- LLM 对话流式返回
- Server-Sent Events (SSE) 协议
- 前端实时渲染支持

### ✅ 改进的 LLM 接口（新增）
- 接受聊天历史记录参数
- 使用 OpenAI SDK 实现
- 支持异步调用
- API Key 和 Base URL 可配置

## 快速开始

### 1. 安装依赖

```bash
cd /root/workspace/RAGWorkProject/backend
pip install -r requirements.txt
```

### 2. 配置 LLM API

编辑 `rag_backend.py`，配置你的 LLM API：

```python
# 在 _run_llm_only_async 和 _run_llm_only_stream 函数中
api_key = "your-api-key-here"
base_url = "https://api.openai.com/v1"
```

### 3. 启动 API 服务

```bash
# 方法 1: 直接运行
python api.py

# 方法 2: 使用 uvicorn（推荐）
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点概览

| 端点 | 方法 | 描述 | 流式 |
|------|------|------|------|
| `/api/query` | POST | RAG 查询（带检索） | ❌ |
| `/api/query/stream` | POST | RAG 查询（流式） | ✅ |
| `/api/llm` | POST | LLM 对话（无检索） | ❌ |
| `/api/llm/stream` | POST | LLM 对话（流式） | ✅ |
| `/api/multi-turn` | POST | 多轮对话 | ❌ |
| `/api/session/{id}` | GET | 获取会话信息 | - |
| `/api/session/{id}` | DELETE | 删除会话 | - |
| `/api/feedback` | POST | 提交反馈 | - |
| `/api/suggestion` | POST | 提交建议 | - |
| `/api/feedback/stats` | GET | 反馈统计 | - |

## 使用示例

### Python 客户端示例

```python
import requests
import json

# 1. 流式 RAG 查询
def stream_query(query):
    url = "http://localhost:8000/api/query/stream"
    response = requests.post(
        url,
        json={"query": query, "use_retrieval": True, "top_k": 5},
        stream=True
    )
    
    for line in response.iter_lines():
        if line and line.startswith(b'data: '):
            data = json.loads(line[6:])
            if data['type'] == 'content':
                print(data['content'], end='', flush=True)

stream_query("如何提交python程序？")

# 2. 流式 LLM 对话
def chat_with_llm(messages):
    url = "http://localhost:8000/api/llm/stream"
    response = requests.post(
        url,
        json={"messages": messages},
        stream=True
    )
    
    for line in response.iter_lines():
        if line and line.startswith(b'data: '):
            data = json.loads(line[6:])
            if data['type'] == 'content':
                print(data['content'], end='', flush=True)

messages = [{"role": "user", "content": "写一个快速排序"}]
chat_with_llm(messages)
```

### JavaScript 前端示例

```javascript
// 流式查询
async function streamQuery(query) {
  const response = await fetch('http://localhost:8000/api/query/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, use_retrieval: true, top_k: 5 })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.type === 'content') {
          // 实时渲染到页面
          document.getElementById('answer').innerText += data.content;
        }
      }
    }
  }
}
```

## 核心功能

### 1. 多轮对话支持 (RAGBackend)

支持灵活的单轮和多轮对话，允许对每一轮对话独立控制是否使用检索。

**特点：**
- ✅ 单轮查询接口
- ✅ 多轮对话管理
- ✅ 逐轮灵活控制检索开关
- ✅ 完整的会话管理
- ✅ 自动日志记录

**使用示例：**

```python
from backend import RAGBackend

# 初始化RAG后端
rag = RAGBackend(
    ultrarag_path="/root/workspace/RAGWorkProject/UltraRAG",
    log_dir="/root/workspace/RAGWorkProject/config/logs"
)

# 单轮查询（带检索）
result = rag.query(
    query_text="如何提交python程序？",
    use_retrieval=True,
    top_k=5
)

# 多轮对话
queries = [
    {'text': '如何提交python程序？', 'use_retrieval': True},
    {'text': '有什么注意事项吗？', 'use_retrieval': False},  # 这一轮不使用检索
    {'text': '提交后多久有反馈？', 'use_retrieval': True}
]
results = rag.multi_turn_conversation(queries)

# 保存会话
rag.save_session()
```

### 2. 反馈系统 (FeedbackHandler)

三层反馈机制，支持不同粒度的用户反馈收集：

#### 2.1 点赞/点踩 (Like/Dislike)
- **存储位置**：伴随对话记录保存到会话日志
- **用途**：快速反馈回答质量
- **调用方式**：在RAGBackend的会话中直接标记

#### 2.2 详细反馈 (Detailed Feedback)
- **存储位置**：`config/feedback/` 文件夹
- **用途**：收集具体的改进意见
- **字段**：反馈类别（如准确性、完整性、清晰度等）

#### 2.3 更好的建议 (Better Suggestions)
- **存储位置**：`config/better_suggestions/` 文件夹
- **用途**：用户建议的更好答案，用于模型微调
- **字段**：原始答案、建议答案、改进原因、质量评分

**使用示例：**

```python
from backend import FeedbackHandler

feedback_handler = FeedbackHandler()

# 提交详细反馈
feedback = feedback_handler.submit_feedback(
    session_id="sess_123",
    turn_id=0,
    query="如何提交python程序？",
    answer="通过官网提交表单...",
    feedback_text="答案太简洁，需要更多步骤说明",
    feedback_category="完整性",
    user_id="user_456"
)

# 提交更好的建议
suggestion = feedback_handler.submit_better_suggestion(
    session_id="sess_123",
    turn_id=0,
    query="如何提交python程序？",
    original_answer="通过官网提交表单...",
    suggested_answer="请按以下步骤：1. 访问官网 2. 登录 3. 点击提交 4. 选择文件...",
    improvement_reason="原答案缺少具体分步指导",
    user_id="user_456",
    quality_score=4
)

# 获取统计信息
stats = feedback_handler.get_feedback_statistics()
```

### 3. 集成反馈的会话 (SessionWithFeedback)

简化的接口，将反馈功能集成到查询结果中：

```python
from backend import RAGBackend, FeedbackHandler, SessionWithFeedback

rag = RAGBackend(
    ultrarag_path="/root/workspace/RAGWorkProject/UltraRAG"
)
feedback_handler = FeedbackHandler()
session = SessionWithFeedback(rag, feedback_handler)

# 执行查询，返回的结果包含反馈函数
result = session.query_with_feedback_support(
    query_text="如何提交python程序？",
    use_retrieval=True
)

# 使用集成的反馈函数
result['feedback_functions']['like'](reason="回答很全面")
result['feedback_functions']['submit_feedback'](
    feedback_text="缺少代码示例",
    category="完整性"
)
result['feedback_functions']['suggest_better'](
    suggested_answer="更好的答案...",
    reason="原答案不够详细"
)
```

## 目录结构

```
RAGWorkProject/
├── backend/                      # 后端代码
│   ├── __init__.py
│   ├── rag_backend.py           # 核心RAG后端
│   ├── feedback_handler.py      # 反馈处理系统
│   └── example_usage.py         # 使用示例
│
└── config/                       # 配置和日志
    ├── logs/                     # 对话会话日志（JSON格式）
    ├── feedback/                 # 详细反馈文件
    └── better_suggestions/       # 用户建议文件
```

## API文档

### RAGBackend

#### 初始化
```python
RAGBackend(
    ultrarag_path: str,                                    # UltraRAG项目路径
    pipeline_file: str = "examples/rag_deploy.yaml",      # Pipeline配置
    parameter_file: str = "examples/parameter/bnu_visrag_parameter.yaml",  # 参数配置
    log_dir: str = "config/logs"                          # 日志目录
)
```

#### 方法

##### `query()`
执行单轮查询。

**参数：**
- `query_text` (str): 用户查询文本
- `use_retrieval` (bool, default=True): 是否使用检索
- `top_k` (int, default=5): 检索返回文档数
- `session_context` (Dict, optional): 额外会话上下文

**返回：**
```python
{
    'query': str,                    # 原始查询
    'answer': str,                   # 生成的答案
    'retrieved_docs': List[Dict],   # 检索到的文档
    'use_retrieval': bool,           # 是否使用了检索
    'status': str,                   # 'success' 或 'error'
    'timestamp': str,                # ISO格式时间戳
    'turn_id': int                   # 对话轮次ID
}
```

##### `multi_turn_conversation()`
执行多轮对话。

**参数：**
- `queries` (List[Dict]): 查询列表
  ```python
  [
      {
          'text': str,                           # 查询文本（必需）
          'use_retrieval': bool (optional),      # 是否使用检索
          'top_k': int (optional)                # 检索数量
      }
  ]
  ```

**返回：**
```python
{
    'session_id': str,
    'total_turns': int,
    'results': List[Dict],          # 每轮的查询结果
    'session_duration': float        # 会话时长（秒）
}
```

##### `save_session()`
保存当前会话的所有交互记录。

**参数：**
- `custom_filename` (str, optional): 自定义文件名

**返回：** 保存文件的路径

##### `load_session()`
加载之前保存的会话。

**参数：**
- `filepath` (str): 会话文件路径

##### `get_conversation_summary()`
获取对话的总结信息。

**返回：**
```python
{
    'session_id': str,
    'total_turns': int,
    'start_time': str,
    'current_time': str,
    'duration_seconds': float,
    'turns': List[Dict]  # 每轮的简要信息
}
```

### FeedbackHandler

#### 初始化
```python
FeedbackHandler(
    feedback_dir: str = "config/feedback",              # 详细反馈目录
    suggestions_dir: str = "config/better_suggestions"  # 建议目录
)
```

#### 方法

##### `add_like_dislike()`
记录点赞/点踩反馈（返回反馈数据结构供保存）。

**参数：**
- `session_id` (str): 会话ID
- `turn_id` (int): 对话轮次
- `is_like` (bool): True=点赞，False=点踩
- `query` (str): 查询文本
- `answer` (str): 答案文本
- `reason` (str, optional): 反馈原因

**返回：** 反馈数据字典

##### `submit_feedback()`
提交详细反馈。

**参数：**
- `session_id` (str): 会话ID
- `turn_id` (int): 对话轮次
- `query` (str): 查询文本
- `answer` (str): 答案文本
- `feedback_text` (str): 详细反馈内容
- `feedback_category` (str, optional): 反馈类别
- `user_id` (str, optional): 用户ID

**返回：** 反馈数据字典（包含saved_path）

##### `submit_better_suggestion()`
提交更好的建议。

**参数：**
- `session_id` (str): 会话ID
- `turn_id` (int): 对话轮次
- `query` (str): 查询文本
- `original_answer` (str): 原始答案
- `suggested_answer` (str): 建议的答案
- `improvement_reason` (str): 改进原因
- `user_id` (str, optional): 用户ID
- `quality_score` (int, optional): 质量评分(1-5)

**返回：** 建议数据字典（包含saved_path）

##### `get_feedback_statistics()`
获取反馈统计信息。

**返回：**
```python
{
    'feedback_count': int,
    'suggestion_count': int,
    'total_feedback': int,
    'feedback_dir': str,
    'suggestions_dir': str
}
```

##### `get_feedback_by_session()`
获取某个会话的所有反馈。

**参数：**
- `session_id` (str): 会话ID

**返回：**
```python
{
    'session_id': str,
    'feedback': List[Dict],
    'suggestions': List[Dict],
    'total_count': int
}
```

##### `export_all_feedback()`
导出所有反馈为JSON文件。

**参数：**
- `export_path` (str): 导出文件路径

**返回：** 导出文件路径

## 文件格式

### 会话日志 (`config/logs/session_*.json`)
```json
{
    "session_id": "uuid",
    "start_time": "2024-01-21T10:30:00",
    "end_time": "2024-01-21T10:35:00",
    "total_turns": 3,
    "conversation_history": [
        {
            "query": "用户问题",
            "answer": "系统答案",
            "use_retrieval": true,
            "turn_id": 0,
            "timestamp": "2024-01-21T10:30:10",
            "status": "success",
            "retrieved_docs": []
        }
    ]
}
```

### 反馈记录 (`config/feedback/*.json`)
```json
{
    "feedback_id": "sess_123_0_20240121_103000",
    "feedback_type": "detailed_feedback",
    "session_id": "sess_123",
    "turn_id": 0,
    "user_id": "user_456",
    "query": "用户问题",
    "answer": "系统答案",
    "feedback_text": "具体反馈内容",
    "feedback_category": "完整性",
    "timestamp": "2024-01-21T10:30:15"
}
```

### 建议记录 (`config/better_suggestions/*.json`)
```json
{
    "suggestion_id": "sess_123_0_20240121_103000",
    "feedback_type": "better_suggestion",
    "session_id": "sess_123",
    "turn_id": 0,
    "user_id": "user_456",
    "query": "用户问题",
    "original_answer": "原始答案",
    "suggested_answer": "用户建议的更好答案",
    "improvement_reason": "为什么更好",
    "quality_score": 4,
    "timestamp": "2024-01-21T10:30:15"
}
```

## 关键回答

### Q1: 如何通过代码传入RAG查询？

**答案：** 通过以下方式实现：

1. **动态修改参数文件**：在`RAGBackend._run_rag_pipeline()`中，代码会在运行时修改YAML参数文件，将`benchmark.path`指向临时创建的查询文件。

2. **临时查询文件**：每次查询都创建一个临时的JSONL文件，包含`id`, `question`, `golden_answers`, `meta_data`等字段。

3. **代码示例**：
```python
rag = RAGBackend(ultrarag_path="/path/to/UltraRAG")
result = rag.query(
    query_text="你的问题",  # 直接通过代码传入
    use_retrieval=True
)
```

**技术细节**：虽然`PipelineCall`本身不支持直接传入查询，但我们通过动态创建临时参数文件绕过了这个限制，实现了完全的代码驱动。

### Q2: 如何支持多轮对话？

**答案：** 通过`multi_turn_conversation()`方法：

1. **会话管理**：维护一个`conversation_history`列表，存储所有轮次的结果。

2. **逐轮控制**：每个查询可独立指定`use_retrieval`参数，控制该轮是否使用检索。

3. **代码示例**：
```python
queries = [
    {'text': '问题1', 'use_retrieval': True},
    {'text': '问题2', 'use_retrieval': False},  # 仅使用LLM
    {'text': '问题3', 'use_retrieval': True}
]
results = rag.multi_turn_conversation(queries)
```

### Q3: 反馈如何存储？

**答案：** 三层存储机制：

| 反馈类型 | 存储位置 | 特点 |
|---------|--------|------|
| 点赞/点踩 | 会话日志JSON | 伴随对话自动保存 |
| 详细反馈 | `config/feedback/` | 独立文件，便于后续分析 |
| 更好的建议 | `config/better_suggestions/` | 独立文件，用于模型微调 |

## 开发计划

- [x] 基础RAG后端（单轮、多轮）
- [x] 反馈系统（点赞、详细反馈、建议）
- [x] 会话管理和日志记录
- [ ] API封装（Flask/FastAPI）
- [ ] 前端web界面
- [ ] 模型微调集成

## 依赖

- Python 3.8+
- UltraRAG
- PyYAML
- 其他UltraRAG依赖

## 许可证

根据项目主协议
