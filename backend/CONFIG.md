# RAG Backend 配置说明

## 配置文件位置

`/root/workspace/RAGWorkProject/config/backend.yaml`

## 配置内容

```yaml
rag:
  # 用于RAG模式生成的模型与API设置
  model: "openai/gpt-4o-mini-2024-07-18"
  base_url: "https://openrouter.ai/api/v1/"
  api_key: "your-api-key-here"  # 或 ENV:OPENAI_API_KEY

no_retrieval:
  # 用于无检索对话的模型与API设置
  model: "openai/gpt-4o-mini-2024-07-18"
  base_url: "https://openrouter.ai/api/v1/"
  api_key: "your-api-key-here"  # 或 ENV:OPENAI_API_KEY
```

## API Key 配置方式

### 方式1: 直接在配置文件中写入

```yaml
api_key: "sk-or-v1-xxxxxxxxxxxx"
```

### 方式2: 使用环境变量（推荐）

```yaml
api_key: "ENV:OPENAI_API_KEY"
```

然后在终端设置环境变量：
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 常见错误

### Error 401: User not found

**原因**: API Key 无效或已过期

**解决方案**:
1. 检查 API Key 是否正确
2. 如使用 OpenRouter，请访问 https://openrouter.ai/ 获取有效的 API Key
3. 如使用其他服务，请确认服务商和 API Key 有效性

### 无检索模式失败

无检索模式需要配置 `no_retrieval` 部分的 model、base_url 和 api_key。

如果不需要无检索模式，可以只使用检索模式（RAG Pipeline）。

## 检查配置

运行配置检查脚本：

```bash
cd /root/workspace/RAGWorkProject/backend
python check_config.py
```

该脚本会：
- 检查配置文件是否存在
- 验证配置格式
- 测试 API 连接

## 仅使用 RAG 模式（不需要 OpenAI）

如果只想使用 RAG 检索模式（UltraRAG Pipeline），可以：

1. 只调用 `/api/chat` 端点并设置 `use_retrieval: true`
2. 不调用 `/api/chat/stream` 端点
3. 配置文件中的 `no_retrieval` 可以留空或使用占位符

## 示例配置（仅RAG）

```yaml
rag:
  model: ""  # RAG模式使用UltraRAG Pipeline，不需要额外的LLM
  base_url: ""
  api_key: ""

no_retrieval:
  model: "placeholder"  # 如不使用可留空
  base_url: ""
  api_key: ""
```

在这种配置下：
- ✅ `/api/chat` with `use_retrieval: true` - 正常工作
- ❌ `/api/chat` with `use_retrieval: false` - 会失败
- ❌ `/api/chat/stream` - 会失败
