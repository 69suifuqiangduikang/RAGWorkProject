# 技术实现细节

## 1. 动态查询注入机制

### 问题背景

UltraRAG的官方API限制：
```python
# PipelineCall只支持这样的调用
PipelineCall(
    pipeline_file="examples/rag_deploy.yaml",
    parameter_file="examples/parameter/rag_deploy_parameter.yaml"
)
# 无法动态传入queries
```

查询数据必须来自文件 (`benchmark.path` 指向的JSONL文件)。

### 解决方案架构

```
用户调用
   ↓
rag.query(query_text="...")
   ↓
RAGBackend._run_rag_pipeline()
   ├─ Step 1: 创建临时查询JSONL
   ├─ Step 2: 加载原参数YAML
   ├─ Step 3: 动态修改benchmark.path
   ├─ Step 4: 保存为临时参数YAML
   ├─ Step 5: 调用PipelineCall
   ├─ Step 6: 解析结果
   └─ Step 7: 清理临时文件
   ↓
返回结果给用户
```

### 代码实现

**Step 1-4: 准备阶段**
```python
def _run_rag_pipeline(self, query_text: str, top_k: int = 5) -> Dict[str, Any]:
    # Step 1: 创建临时查询数据
    temp_query_data = {
        "id": 0,
        "question": query_text,      # ← 用户的查询文本
        "golden_answers": [],
        "meta_data": {}
    }
    
    # 写入临时JSONL文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        json.dump(temp_query_data, f)
        temp_query_file = f.name     # e.g., /tmp/tmpxyz123.jsonl
    
    try:
        # Step 2: 加载原参数文件
        with open(self.parameter_file, 'r') as f:
            params = yaml.safe_load(f)
        
        # Step 3: 修改数据路径
        if 'benchmark' in params:
            params['benchmark']['benchmark']['path'] = temp_query_file
        
        # Step 4: 保存为临时参数文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(params, f)
            temp_param_file = f.name   # e.g., /tmp/tmpxyz456.yaml
        
        # Step 5: 执行Pipeline
        result = PipelineCall(
            pipeline_file=self.pipeline_file,
            parameter_file=temp_param_file,
            log_level="error"
        )
        
        # Step 6: 解析结果
        answer = self._extract_answer(result)
        retrieved_docs = self._extract_retrieved_docs(result)
        
        return {
            'answer': answer,
            'retrieved_docs': retrieved_docs,
            'raw_result': result
        }
    finally:
        # Step 7: 清理临时文件
        if os.path.exists(temp_param_file):
            os.remove(temp_param_file)
    finally:
        if os.path.exists(temp_query_file):
            os.remove(temp_query_file)
```

### 关键技术点

**1. 临时文件管理**
```python
with tempfile.NamedTemporaryFile(...) as f:  # 自动清理
    # 写入内容
```

**2. YAML参数修改**
```python
params = yaml.safe_load(f)           # 解析原YAML
params['benchmark']['benchmark']['path'] = temp_file  # 修改特定字段
yaml.dump(params, f)                 # 保存为新YAML
```

**3. 异常处理**
```python
try:
    # 执行
finally:
    # 保证清理，即使出错也会执行
```

### 为什么这个方案有效？

1. **隐蔽性**: 用户无需知道临时文件的存在
2. **灵活性**: 支持任意查询文本
3. **安全性**: 使用finally保证资源清理
4. **可靠性**: 即使Pipeline失败也会清理文件

### 性能考虑

```
时间开销分析：
├─ 创建临时文件: ~1ms
├─ YAML解析和修改: ~5ms
├─ Pipeline执行: 100ms~1s (主要耗时)
├─ 结果解析: ~5ms
└─ 文件清理: ~1ms
   总计: 受Pipeline耗时主导 (≥100ms)
```

## 2. 多轮对话与会话管理

### 会话状态模型

```
RAGBackend实例
    ├─ session_id (UUID)
    ├─ session_start_time
    ├─ conversation_history (List)
    │   ├─ Turn 0 { query, answer, use_retrieval, turn_id, ... }
    │   ├─ Turn 1 { query, answer, use_retrieval, turn_id, ... }
    │   └─ Turn N { ... }
    └─ 配置参数
        ├─ ultrarag_path
        ├─ pipeline_file
        ├─ parameter_file
        └─ log_dir
```

### 数据流图

```
用户输入: [Q1, Q2, Q3, ...]
   ↓
multi_turn_conversation()
   ├─ for each query:
   │   ├─ query()
   │   ├─ 执行RAG (if use_retrieval)
   │   ├─ 添加到conversation_history
   │   └─ 返回result
   ↓
results = [result1, result2, result3, ...]
   ↓
save_session()
   └─ 保存到 config/logs/session_*.json
```

### 会话保存格式

```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_time": "2024-01-21T10:30:00.123456",
    "end_time": "2024-01-21T10:35:30.654321",
    "total_turns": 3,
    "conversation_history": [
        {
            "turn_id": 0,
            "query": "如何提交python程序？",
            "answer": "通过官网提交表单...",
            "use_retrieval": true,
            "top_k": 5,
            "timestamp": "2024-01-21T10:30:05",
            "status": "success",
            "retrieved_docs": [
                {"id": 1, "title": "...", "content": "..."},
                {"id": 2, "title": "...", "content": "..."}
            ],
            "session_context": {"total_turns": 3}
        },
        {
            "turn_id": 1,
            "query": "有什么注意事项吗？",
            "answer": "需要注意以下几点...",
            "use_retrieval": false,
            "top_k": null,
            "timestamp": "2024-01-21T10:30:10",
            "status": "success",
            "retrieved_docs": []
        },
        {
            "turn_id": 2,
            "query": "提交后多久有反馈？",
            "answer": "通常在3-5个工作日内...",
            "use_retrieval": true,
            "top_k": 3,
            "timestamp": "2024-01-21T10:30:15",
            "status": "success",
            "retrieved_docs": [...]
        }
    ]
}
```

### 会话加载实现

```python
def load_session(self, filepath: str) -> None:
    with open(filepath, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    # 恢复会话状态
    self.session_id = session_data['session_id']
    self.conversation_history = session_data['conversation_history']
    
    # 不修改session_start_time，保持原始时间
    # 这样统计时间差时会更准确
```

## 3. 反馈系统的三层设计

### 为什么采用三层设计？

```
用户反馈需求：
├─ 快速反馈需求
│  └─ "这个答案好/不好"
│     ├─ 需要简单快捷
│     ├─ 不应该打断对话
│     └─ 自动保存即可
│
├─ 深度反馈需求
│  └─ "答案有这些问题..."
│     ├─ 需要填写表单
│     ├─ 需要分类标签
│     └─ 便于后期分析
│
└─ 改进建议需求
   └─ "答案应该这样写..."
      ├─ 包含具体建议
      ├─ 用于模型微调
      └─ 高价值内容
```

### 存储路径设计

```
config/
├─ logs/
│  └─ session_uuid_time.json
│     └─ conversation_history[].like_dislike (可选)
│        {
│            "is_like": true/false,
│            "reason": "optional"
│        }
│
├─ feedback/
│  └─ feedback_id.json
│     {
│         "feedback_type": "detailed_feedback",
│         "feedback_text": "具体意见",
│         "feedback_category": "完整性/准确性/清晰度"
│     }
│
└─ better_suggestions/
   └─ suggestion_id.json
      {
          "feedback_type": "better_suggestion",
          "original_answer": "...",
          "suggested_answer": "...",
          "quality_score": 1-5
      }
```

### 点赞/点踩集成方案

```python
# 方案A: 直接在会话中记录 (当前实现)
conversation_history = [
    {
        "query": "问题",
        "answer": "答案",
        "like_dislike": {              # ← 直接嵌入
            "is_like": true,
            "reason": "答案准确"
        }
    }
]

# 好处:
# ✓ 数据关联紧密
# ✓ 分析时无需JOIN多个表
# ✓ 保证对话完整性
```

### 反馈统计查询

```python
def get_feedback_statistics(self):
    """统计所有反馈"""
    # 遍历feedback/下的所有JSON
    feedback_count = len(list(Path(self.feedback_dir).glob('*.json')))
    
    # 遍历better_suggestions/下的所有JSON
    suggestion_count = len(list(Path(self.suggestions_dir).glob('*.json')))
    
    return {
        'feedback_count': feedback_count,
        'suggestion_count': suggestion_count,
        'total_feedback': feedback_count + suggestion_count
    }
```

### 按会话查询反馈

```python
def get_feedback_by_session(self, session_id: str):
    """获取某个会话的所有反馈"""
    feedback_list = []
    suggestion_list = []
    
    # 遍历所有反馈文件，按session_id过滤
    for filepath in Path(self.feedback_dir).glob('*.json'):
        with open(filepath) as f:
            data = json.load(f)
            if data.get('session_id') == session_id:
                feedback_list.append(data)
    
    # 遍历所有建议文件，按session_id过滤
    for filepath in Path(self.suggestions_dir).glob('*.json'):
        with open(filepath) as f:
            data = json.load(f)
            if data.get('session_id') == session_id:
                suggestion_list.append(data)
    
    return {
        'session_id': session_id,
        'feedback': feedback_list,
        'suggestions': suggestion_list,
        'total_count': len(feedback_list) + len(suggestion_list)
    }
```

## 4. 结果解析与适配

### Pipeline输出结构

UltraRAG Pipeline的输出结构：
```python
{
    'final_result': {
        # 最后一步的输出
        'answer': '...',
        'response': '...',
        # 其他字段
    },
    'all_results': [
        # 第1步的输出
        {
            'benchmark_result': [...],
            'q_ls': ['问题1', '问题2'],
        },
        # 第2步的输出
        {
            'retrieved_docs': [...],
            'ret_psg': [...]
        },
        # ...其他步骤...
        # 最后一步
        {
            'answer': '最终答案',
            'evaluation': {...}
        }
    ]
}
```

### 答案提取逻辑

```python
def _extract_answer(self, result: Dict[str, Any]) -> str:
    """智能提取答案"""
    
    # 优先级1: 从final_result提取
    if 'final_result' in result:
        final = result['final_result']
        if isinstance(final, dict):
            if 'answer' in final:
                return final['answer']
            if 'response' in final:
                return final['response']
    
    # 优先级2: 从result直接提取
    if 'answer' in result:
        return result['answer']
    if 'response' in result:
        return result['response']
    
    # 降级: 返回整个结果的字符串表示
    return str(result)
```

### 文档提取逻辑

```python
def _extract_retrieved_docs(self, result: Dict[str, Any]) -> List[Dict]:
    """提取检索到的文档"""
    retrieved_docs = []
    
    # 在all_results中查找包含文档的步骤
    if 'all_results' in result and isinstance(result['all_results'], list):
        for step_result in result['all_results']:
            if isinstance(step_result, dict):
                # 不同步骤可能使用不同的字段名
                if 'retrieved_docs' in step_result:
                    return step_result['retrieved_docs']
                if 'ret_psg' in step_result:
                    return step_result['ret_psg']
    
    return []
```

## 5. 错误处理策略

### 查询错误处理

```python
def query(self, query_text: str, use_retrieval: bool = True, ...):
    result = {
        'query': query_text,
        'use_retrieval': use_retrieval,
        'timestamp': datetime.now().isoformat(),
        'turn_id': len(self.conversation_history)
    }
    
    try:
        if use_retrieval:
            rag_result = self._run_rag_pipeline(query_text, top_k)
            result['answer'] = rag_result.get('answer', '')
            result['retrieved_docs'] = rag_result.get('retrieved_docs', [])
        else:
            result['answer'] = self._run_llm_only(query_text)
            result['retrieved_docs'] = []
        
        result['status'] = 'success'
    
    except Exception as e:
        # 错误记录
        result['status'] = 'error'
        result['error'] = str(e)
        result['answer'] = None
    
    # 无论成功或失败，都保存到历史
    self.conversation_history.append(result)
    return result
```

### 文件操作错误处理

```python
def save_session(self, custom_filename: Optional[str] = None) -> str:
    # 确保目录存在
    Path(self.log_dir).mkdir(parents=True, exist_ok=True)
    
    filepath = os.path.join(self.log_dir, f"{filename}.json")
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        return filepath
    except IOError as e:
        print(f"保存失败: {e}")
        raise
```

## 6. 性能优化考虑

### 内存使用

```python
# 当前实现的内存占用
conversation_history = []  # List[Dict]
# 单个Turn的大小 ~ 1-10KB (包含检索文档)
# 100轮对话 ~ 100-1000KB (可接受)
```

### 文件I/O优化

```python
# 当前方案: 每次查询创建临时文件
优点:
  - 简单可靠
  - 无污染 (自动清理)
  - 支持并发

缺点:
  - 涉及磁盘I/O (~5ms)

# 未来优化方案:
  - 使用内存文件系统 (/dev/shm)
  - 直接传递对象 (修改UltraRAG源码)
```

### 批量处理

```python
# 当前实现: 逐个处理每个查询
queries = [q1, q2, q3]
for q in queries:
    result = rag.query(q)

# 未来优化: 批量处理
results = rag.batch_query(queries)  # 并行执行
```

---

这个文档详细说明了每个关键模块的技术实现原理，为后续的改进和维护提供了技术基础。
