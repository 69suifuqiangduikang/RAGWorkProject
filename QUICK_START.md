# RAG系统后端 - 快速开始指南

## 项目概述

这个后端系统基于UltraRAG框架，为RAG系统提供：
- ✅ **多轮对话支持** - 灵活控制每一轮是否使用检索
- ✅ **完整的反馈系统** - 点赞、详细反馈、更好建议
- ✅ **自动会话日志** - JSON格式，便于分析
- ✅ **函数级接口** - 为前端API开发做准备

## 5分钟快速开始

### 1. 初始化后端

```python
from backend import RAGBackend

rag = RAGBackend(
    ultrarag_path="/root/workspace/RAGWorkProject/UltraRAG",
    log_dir="/root/workspace/RAGWorkProject/config/logs"
)
```

### 2. 单轮查询

```python
# 执行带检索的查询
result = rag.query(
    query_text="如何提交python程序？",
    use_retrieval=True,
    top_k=5
)

print(f"答案: {result['answer']}")
print(f"会话ID: {rag.session_id}")
```

### 3. 多轮对话

```python
# 灵活控制每一轮的检索
queries = [
    {
        'text': '如何提交python程序？',
        'use_retrieval': True,   # 使用检索
        'top_k': 5
    },
    {
        'text': '有什么注意事项吗？',
        'use_retrieval': False   # 不使用检索，仅用LLM
    },
    {
        'text': '提交后有反馈吗？',
        'use_retrieval': True    # 再次使用检索
    }
]

results = rag.multi_turn_conversation(queries)
print(f"总轮次: {results['total_turns']}")
```

### 4. 反馈收集

```python
from backend import FeedbackHandler

feedback_handler = FeedbackHandler()

# 提交详细反馈
feedback_handler.submit_feedback(
    session_id=rag.session_id,
    turn_id=0,
    query="如何提交python程序？",
    answer=result['answer'],
    feedback_text="答案太简洁，需要更多步骤",
    feedback_category="完整性",
    user_id="user_123"
)

# 提交更好的建议
feedback_handler.submit_better_suggestion(
    session_id=rag.session_id,
    turn_id=0,
    query="如何提交python程序？",
    original_answer=result['answer'],
    suggested_answer="请按以下步骤：1. 访问官网 2. 登录 3. 上传文件...",
    improvement_reason="需要更详细的分步指导",
    user_id="user_123",
    quality_score=4
)
```

### 5. 保存会话

```python
# 自动保存所有交互记录到 config/logs/
saved_path = rag.save_session()
print(f"会话已保存: {saved_path}")
```

## 核心特性详解

### 🎯 特性1：代码传入查询

**以前的问题：** 官方文档中的PipelineCall只能从文件读取查询

**我们的解决方案：**
```python
# 现在可以直接通过代码传入查询，无需手动创建文件
rag.query(query_text="任何问题")  # ✅ 代码驱动

# 内部实现：
# 1. 创建临时JSONL文件
# 2. 动态修改YAML参数文件的path字段
# 3. 运行Pipeline后删除临时文件
```

### 🔄 特性2：多轮对话与灵活检索控制

**应用场景：**
- 第1轮：用户问问题 → 使用检索获取相关文档
- 第2轮：用户追问细节 → 不需要检索，直接从上下文回答
- 第3轮：用户提出新问题 → 再次使用检索

```python
# 每轮都可独立控制
queries = [
    {'text': '新问题', 'use_retrieval': True},   # 用检索
    {'text': '追问', 'use_retrieval': False},    # 不用检索
    {'text': '另一个问题', 'use_retrieval': True} # 再用检索
]
```

### 💬 特性3：三层反馈系统

```
用户反馈
├── ⭐ 点赞/点踩
│   ├─ 自动伴随对话保存
│   ├─ 存储位置: config/logs/session_*.json
│   └─ 用途: 快速质量反馈
│
├── 📝 详细反馈 (Detailed Feedback)
│   ├─ 单独保存文件: config/feedback/
│   ├─ 包含反馈类别: 准确性、完整性、清晰度等
│   └─ 用途: 系统改进分析
│
└── 💡 更好的建议 (Better Suggestions)
    ├─ 单独保存文件: config/better_suggestions/
    ├─ 包含质量评分: 1-5分
    └─ 用途: 模型微调和提示词优化
```

**文件位置说明：**
```
RAGWorkProject/config/
├── logs/                      # 对话会话日志（自动生成）
│   └── session_uuid_time.json
├── feedback/                  # 详细反馈文件（用户手动提交）
│   └── feedback_id.json
└── better_suggestions/        # 改进建议文件（用户手动提交）
    └── suggestion_id.json
```

### 📊 特性4：会话管理

```python
# 保存会话
rag.save_session()  # 自动保存到 config/logs/

# 加载之前的会话
rag.load_session("/path/to/session.json")

# 获取会话摘要
summary = rag.get_conversation_summary()
# 返回: {总轮数, 开始时间, 时长, 每轮概览...}
```

## 文件目录结构

```
RAGWorkProject/
├── backend/                   # 💻 后端代码目录
│   ├── __init__.py           # Python包初始化
│   ├── rag_backend.py        # ⭐ 核心RAG后端 (200+行)
│   ├── feedback_handler.py   # ⭐ 反馈处理系统 (300+行)
│   ├── example_usage.py      # 使用示例代码
│   └── README.md             # 详细文档
│
└── config/                    # 📁 配置与日志目录
    ├── logs/                 # 会话日志 (自动生成)
    │   └── session_*.json
    ├── feedback/             # 详细反馈 (自动生成)
    │   └── *.json
    └── better_suggestions/   # 改进建议 (自动生成)
        └── *.json
```

## 下一步：API封装

目前的实现是**函数级接口**，为了与前端集成，下一步需要封装为HTTP API：

```python
# 预计的API设计（Flask示例）
# POST /api/rag/query
# POST /api/rag/feedback
# POST /api/rag/suggestion
# GET /api/rag/session/<session_id>
# GET /api/rag/feedback/stats
```

## 常见问题

### Q: 如何修改检索的top_k值？
```python
rag.query(
    query_text="问题",
    use_retrieval=True,
    top_k=10  # 改为10
)
```

### Q: 如何禁用某一轮的检索？
```python
queries = [
    {'text': '问题1', 'use_retrieval': True},
    {'text': '问题2', 'use_retrieval': False},  # ← 禁用
]
```

### Q: 反馈保存在哪里？
```
点赞/点踩:     自动保存到 config/logs/session_*.json
详细反馈:      保存到 config/feedback/*.json
更好建议:      保存到 config/better_suggestions/*.json
```

### Q: 可以加载之前的会话继续对话吗？
```python
# 加载之前的会话
rag2 = RAGBackend(...)
rag2.load_session("config/logs/session_previous.json")

# 继续对话
rag2.query("继续提问...")
```

### Q: 性能如何？
- 首次查询：取决于UltraRAG的检索速度
- 后续查询：不涉及文件I/O，仅处理数据
- 反馈提交：异步，不阻塞对话

## 技术实现细节

### 动态查询注入

虽然UltraRAG的PipelineCall只支持从配置文件读取，但我们通过以下方式实现了代码驱动的查询：

1. **创建临时JSONL文件**
   ```python
   {"id": 0, "question": "用户问题", "golden_answers": [], "meta_data": {}}
   ```

2. **动态修改YAML参数**
   ```yaml
   benchmark:
     benchmark:
       path: /tmp/temp_query_xyz.jsonl  # ← 动态修改
   ```

3. **执行Pipeline并清理**
   ```python
   result = PipelineCall(pipeline_file, temp_param_file)
   # 清理临时文件
   ```

### 会话上下文管理

```python
# 自动维护对话历史
conversation_history = [
    {turn0},  # 第1轮
    {turn1},  # 第2轮
    {turn2},  # 第3轮
]
```

## 测试

```python
# 运行示例
python backend/example_usage.py

# 输出应该显示：
# - 反馈统计
# - 已保存的会话
# - 生成的日志文件
```

## 许可证

遵循主项目协议

---

**下一步建议：**
1. ✅ 测试基本功能
2. ⏳ 封装为REST API (Flask/FastAPI)
3. ⏳ 开发前端Web界面
4. ⏳ 集成模型微调流程
