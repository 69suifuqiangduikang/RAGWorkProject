# RAG系统后端 - 系统架构与数据流

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          前端应用层                              │
│                    (待开发 - 前端Web界面)                       │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├──────────────────────────────────────────┐
             │                                          │
┌────────────▼─────────────────────────┐   ┌──────────▼────────────┐
│      API服务层 (待开发)               │   │  日志和反馈系统      │
│   ├─ POST /api/query                  │   │  ├─ 会话日志         │
│   ├─ POST /api/conversation           │   │  ├─ 反馈文件         │
│   ├─ POST /api/feedback               │   │  └─ 建议文件         │
│   └─ GET  /api/session/<id>           │   └──────────────────────┘
└────────────┬─────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────────────┐
│                      RAG后端系统 (已完成)                         │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  RAGBackend类                    FeedbackHandler类                │
│  ├─ query()              多轮对话          ├─ add_like_dislike()   │
│  ├─ multi_turn_conv()    灵活检索控制      ├─ submit_feedback()    │
│  ├─ save_session()       会话管理          ├─ submit_better_..()   │
│  ├─ load_session()       会话恢复          ├─ get_feedback_stats() │
│  └─ _run_rag_pipeline()  动态查询注入      └─ get_feedback_by_..() │
│                                                                    │
│  SessionWithFeedback类                                            │
│  └─ query_with_feedback_support() 集成反馈的查询                  │
└────────────┬──────────────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────────────┐
│                      UltraRAG框架层                                │
├───────────────────────────────────────────────────────────────────┤
│  ├─ Pipeline: examples/rag_deploy.yaml                           │
│  ├─ Parameters: examples/parameter/bnu_visrag_parameter.yaml     │
│  └─ PipelineCall(pipeline_file, parameter_file)                  │
└────────────┬──────────────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────────────┐
│                    RAG核心模块 (UltraRAG)                         │
├───────────────────────────────────────────────────────────────────┤
│  ├─ Benchmark        数据加载模块                                │
│  ├─ Retriever        检索模块                                    │
│  ├─ Generation       生成模块                                    │
│  ├─ Prompt           提示词模块                                  │
│  └─ Evaluation       评估模块                                    │
└────────────┬──────────────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────────────┐
│                      外部资源                                      │
├───────────────────────────────────────────────────────────────────┤
│  ├─ 文本检索模型 (Sentence Transformers)                         │
│  ├─ 图像检索模型 (Vision Transformer)                            │
│  ├─ 大语言模型   (GPT/Qwen/Claude)                               │
│  ├─ 向量数据库   (Milvus/Chroma)                                 │
│  └─ 知识库       (corpus.jsonl)                                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 数据流图

### 1. 单轮查询流程

```
┌─────────┐
│用户输入  │ query_text="如何提交python程序？"
└────┬────┘
     │
┌────▼────────────────────────────────────────────────┐
│ RAGBackend.query()                                  │
├─────────────────────────────────────────────────────┤
│ 1. 创建会话ID和轮次ID                              │
│ 2. 检查use_retrieval参数                           │
│ 3. 调用_run_rag_pipeline()或_run_llm_only()        │
└────┬────────────────────────────────────────────────┘
     │
     ├─── use_retrieval=True
     │
┌────▼────────────────────────────────────────────────┐
│ _run_rag_pipeline(query_text, top_k)               │
├─────────────────────────────────────────────────────┤
│ 1. 创建临时JSONL:                                  │
│    {"id": 0, "question": "...", ...}              │
│                                                    │
│ 2. 加载参数YAML                                    │
│                                                    │
│ 3. 修改path字段:                                   │
│    params['benchmark']['benchmark']['path']        │
│    = /tmp/temp_xyz.jsonl                          │
│                                                    │
│ 4. 保存临时参数YAML                                │
│                                                    │
│ 5. PipelineCall(pipeline_file, temp_param_file)   │
│    ├─ Benchmark: 加载/tmp/temp_xyz.jsonl         │
│    ├─ Retriever: 检索文档 (top_k=5)               │
│    ├─ Prompt: 生成提示词                          │
│    ├─ Generation: 生成答案                        │
│    └─ Evaluation: 评估结果                        │
│                                                    │
│ 6. 解析结果:                                       │
│    - 提取answer字段                               │
│    - 提取retrieved_docs字段                       │
│                                                    │
│ 7. 清理临时文件 (JSONL + YAML)                     │
└────┬────────────────────────────────────────────────┘
     │
     └─── use_retrieval=False
         │
    ┌────▼───────────────────────┐
    │ _run_llm_only()            │
    ├──────────────────────────────┤
    │ 直接调用LLM生成答案          │
    │ (不进行检索)                │
    └────┬──────────────────────────┘
     │
┌────▼────────────────────────────────────────────────┐
│ 构建结果对象:                                      │
│ {                                                 │
│   "turn_id": 0,                                   │
│   "query": "...",                                 │
│   "answer": "...",                                │
│   "use_retrieval": true,                          │
│   "retrieved_docs": [...],                        │
│   "status": "success",                            │
│   "timestamp": "2024-01-21T10:30:00"              │
│ }                                                 │
└────┬────────────────────────────────────────────────┘
     │
┌────▼────────────────────────────────────────────────┐
│ 添加到conversation_history                         │
└────┬────────────────────────────────────────────────┘
     │
┌────▼────────────────────────────────────────────────┐
│ 返回result给用户                                   │
└─────────────────────────────────────────────────────┘
```

### 2. 多轮对话流程

```
┌───────────────────────┐
│ 多轮查询列表:          │
│ ┌─────────────────┐  │
│ │Q1: use_ret=True │  │
│ │Q2: use_ret=False│  │
│ │Q3: use_ret=True │  │
│ └─────────────────┘  │
└───────┬───────────────┘
        │
┌───────▼─────────────────────────────────┐
│ multi_turn_conversation(queries)        │
├──────────────────────────────────────────┤
│ for each query in queries:               │
│   ├─ turn_id = len(conversation_history)│
│   ├─ query(query_text, use_retrieval)   │
│   ├─ 等待返回result                     │
│   ├─ append to conversation_history     │
│   └─ 继续下一个                          │
└───────┬─────────────────────────────────┘
        │
┌───────▼──────────────────────────────────┐
│ 构建多轮结果:                             │
│ {                                        │
│   "session_id": "uuid",                  │
│   "total_turns": 3,                      │
│   "results": [result0, result1, result2] │
│ }                                        │
└───────┬──────────────────────────────────┘
        │
└───────┴──────────────────────────────────┘
         返回多轮对话结果
```

### 3. 反馈流程

```
┌──────────────────────────────────────────┐
│         用户与AI交互                      │
├──────────────────────────────────────────┤
│ 用户看到AI的答案                         │
└──────┬───────────────────────────────────┘
       │
       ├────────────────────┬──────────────────┬─────────────────┐
       │                    │                  │                 │
    ✓点赞                 📝详细反馈          💡更好建议
       │                    │                  │
       │                    │                  │
┌──────▼──────┐  ┌─────────▼────────────┐  ┌──▼────────────────┐
│点赞/点踩数据 │  │详细反馈表单          │  │用户输入更好答案    │
│             │  │                      │  │                  │
│{            │  │{                     │  │{                 │
│ is_like:✓   │  │ feedback_text:"...", │  │ suggested:"..."  │
│ reason:"..." │  │ category:"完整性",   │  │ reason:"..."     │
│}            │  │ user_id:"..."        │  │ quality_score:4  │
│             │  │}                     │  │}                 │
└──────┬──────┘  └─────────┬────────────┘  └──┬────────────────┘
       │                    │                  │
       │ 伴随对话自动保存    │ 保存到独立文件   │ 保存到独立文件
       │                    │                  │
┌──────▼────────────────────▼──────────────────▼─────────────────┐
│                         反馈管理                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  config/logs/                 config/feedback/  config/better_/│
│  └─session_*.json            └─feedback_*.json   └─sugg_*.json│
│     ├─ conversation_history[]  ├─ session_id     ├─ session_id│
│     │   ├─ query             │  ├─ turn_id       │  ├─ turn_id │
│     │   ├─ answer            │  ├─ feedback_text │  ├─ original│
│     │   ├─ timestamp         │  ├─ category      │  ├─ suggested
│     │   └─ like_dislike ◄────┘  ├─ user_id       │  ├─ reason  │
│     │      ├─ is_like        │  └─ timestamp    │  ├─ score   │
│     │      └─ reason         │                  │  └─ timestamp
│     │                        └──────────────────┘
│     └─ session_id
│     └─ start_time
│     └─ total_turns
│
└────────────────────────────────────────────────────────────────┘
```

### 4. 会话保存与加载

```
┌─────────────────────────────────┐
│  对话进行中                      │
│  RAGBackend实例存储在内存        │
│  conversation_history = [...]   │
└────────┬────────────────────────┘
         │
         └─ rag.save_session()
            │
            ├─ 组织会话数据:
            │  {
            │    "session_id": "...",
            │    "start_time": "...",
            │    "end_time": "...",
            │    "total_turns": 3,
            │    "conversation_history": [...]
            │  }
            │
            ├─ 生成文件名:
            │  session_uuid_timestamp.json
            │
            └─ 保存到: config/logs/
               │
               └─ session_550e8400_20240121_103000.json

┌─────────────────────────────────┐
│  程序结束，重新启动              │
└────────┬────────────────────────┘
         │
         └─ rag.load_session("config/logs/session_*.json")
            │
            ├─ 读取JSON文件
            │
            ├─ 恢复session_id
            │
            ├─ 恢复conversation_history
            │
            └─ RAGBackend实例恢复
               │
               └─ 继续对话: rag.query("新问题")
```

---

## 文件系统结构

```
RAGWorkProject/
│
├── backend/                         ⭐ 后端代码
│   ├── __init__.py                 (35行) 包初始化
│   ├── rag_backend.py              (450+行) 核心RAG后端
│   ├── feedback_handler.py         (400+行) 反馈处理
│   ├── example_usage.py            (300+行) 使用示例
│   └── README.md                   (500+行) API文档
│
├── config/                          📁 配置与日志
│   ├── logs/                        (自动生成)
│   │   ├── session_550e8400_20240121_103000.json
│   │   ├── session_660f9501_20240121_104500.json
│   │   └── ...
│   ├── feedback/                    (自动生成)
│   │   ├── sess_123_0_20240121_103015.json
│   │   ├── sess_124_1_20240121_103020.json
│   │   └── ...
│   └── better_suggestions/          (自动生成)
│       ├── sess_123_0_20240121_103020.json
│       ├── sess_124_1_20240121_103025.json
│       └── ...
│
├── UltraRAG/                        UltraRAG框架
│   ├── examples/
│   │   ├── rag_deploy.yaml         (Pipeline配置)
│   │   └── parameter/
│   │       └── bnu_visrag_parameter.yaml (参数配置)
│   ├── src/
│   ├── servers/
│   └── ...
│
└── 项目文档
    ├── QUICK_START.md              (5分钟快速开始)
    ├── PROJECT_SUMMARY.md          (项目总结报告)
    ├── TECHNICAL_DETAILS.md        (技术实现细节)
    └── DELIVERY_CHECKLIST.md       (交付验证清单)
```

---

## 关键数据结构

### Result对象
```python
{
    # 基本信息
    "query": "用户问题",
    "turn_id": 0,
    "session_context": {},
    
    # 查询控制
    "use_retrieval": True,
    "top_k": 5,
    
    # 执行结果
    "answer": "生成的答案",
    "retrieved_docs": [
        {"id": 1, "title": "...", "content": "..."},
        {"id": 2, "title": "...", "content": "..."}
    ],
    
    # 元数据
    "status": "success",  # 或 "error"
    "timestamp": "2024-01-21T10:30:00",
    "error": None  # 如果status="error"则包含错误信息
}
```

### Session对象
```python
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_time": "2024-01-21T10:30:00",
    "end_time": "2024-01-21T10:35:30",
    "total_turns": 3,
    "conversation_history": [result1, result2, result3]
}
```

### Feedback对象
```python
# 详细反馈
{
    "feedback_id": "sess_123_0_20240121_103015",
    "feedback_type": "detailed_feedback",
    "session_id": "sess_123",
    "turn_id": 0,
    "query": "用户问题",
    "answer": "系统答案",
    "feedback_text": "具体反馈",
    "feedback_category": "完整性",
    "user_id": "user_456",
    "timestamp": "2024-01-21T10:30:15"
}

# 更好建议
{
    "suggestion_id": "sess_123_0_20240121_103020",
    "feedback_type": "better_suggestion",
    "session_id": "sess_123",
    "turn_id": 0,
    "original_answer": "原始答案",
    "suggested_answer": "更好的答案",
    "improvement_reason": "原因说明",
    "quality_score": 4,
    "user_id": "user_456",
    "timestamp": "2024-01-21T10:30:20"
}
```

---

## 系统优势

✅ **架构清晰**
- 分层设计：表现层 → 业务层 → 框架层 → 资源层
- 模块独立：RAG、反馈、会话管理分离
- 易于维护：代码结构一致，命名规范

✅ **功能完整**
- 多轮对话支持
- 灵活检索控制
- 三层反馈系统
- 完整会话管理

✅ **生产就绪**
- 错误处理完善
- 资源自动清理
- 数据持久化
- 接口规范

✅ **易于扩展**
- API层待开发
- 前端层待开发
- 微调集成待开发
- 分析仪表板待开发

---

这个系统架构为RAG系统提供了一个坚实的基础，可以轻松扩展为完整的生产系统。
