# RAG系统后端 - 文档索引

欢迎使用RAG系统后端！本索引帮助您快速找到所需的文档。

## 📚 文档导航

### 🚀 新用户入门
如果您是第一次使用，请按以下顺序阅读：

1. **[快速开始指南](QUICK_START.md)** (5分钟) ⭐ 推荐首先阅读
   - 项目概述
   - 5分钟快速开始
   - 核心特性介绍
   - 常见问题解答

2. **[系统架构图](SYSTEM_ARCHITECTURE.md)** (10分钟)
   - 系统整体架构
   - 数据流程图
   - 文件系统结构
   - 关键数据结构

3. **[API完整文档](backend/README.md)** (参考)
   - RAGBackend类API
   - FeedbackHandler类API
   - 使用示例代码
   - 文件格式说明

---

### 📖 按功能查找

#### 🔍 查询和对话
- **如何执行单轮查询？** → [QUICK_START.md - 第2部分](QUICK_START.md#2-单轮查询)
- **如何进行多轮对话？** → [QUICK_START.md - 第3部分](QUICK_START.md#3-多轮对话)
- **如何控制每一轮是否使用检索？** → [backend/README.md - query()方法](backend/README.md)
- **代码通过什么方式传入查询？** → [TECHNICAL_DETAILS.md - 第1节](TECHNICAL_DETAILS.md)

#### 💬 反馈系统
- **如何收集点赞/点踩？** → [QUICK_START.md - 第4部分](QUICK_START.md#4-反馈收集)
- **如何提交详细反馈？** → [backend/README.md - submit_feedback()方法](backend/README.md)
- **如何提交改进建议？** → [backend/README.md - submit_better_suggestion()方法](backend/README.md)
- **反馈保存在哪里？** → [QUICK_START.md - 常见问题](QUICK_START.md#常见问题)

#### 💾 会话管理
- **如何保存会话？** → [QUICK_START.md - 第5部分](QUICK_START.md#5-保存会话)
- **如何加载之前的会话？** → [backend/README.md - load_session()方法](backend/README.md)
- **会话文件存储在哪？** → [SYSTEM_ARCHITECTURE.md - 文件系统](SYSTEM_ARCHITECTURE.md)

---

## 🛠️ 技术深度

#### 核心实现原理
- **动态查询注入如何工作？** → [TECHNICAL_DETAILS.md - 第1部分](TECHNICAL_DETAILS.md)
- **多轮对话如何管理状态？** → [TECHNICAL_DETAILS.md - 第2部分](TECHNICAL_DETAILS.md)
- **反馈系统如何设计的？** → [TECHNICAL_DETAILS.md - 第3部分](TECHNICAL_DETAILS.md)
- **结果如何解析的？** → [TECHNICAL_DETAILS.md - 第4部分](TECHNICAL_DETAILS.md)

---

## 🗂️ 快速查询

| 文件 | 用途 | 阅读时间 |
|-----|------|--------|
| [QUICK_START.md](QUICK_START.md) | 5分钟快速开始 | 5分钟 |
| [backend/README.md](backend/README.md) | 完整API参考 | 15分钟 |
| [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | 系统架构详解 | 10分钟 |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | 项目总结报告 | 10分钟 |
| [TECHNICAL_DETAILS.md](TECHNICAL_DETAILS.md) | 技术实现细节 | 20分钟 |
| [DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md) | 交付验证清单 | 5分钟 |
| [backend/example_usage.py](backend/example_usage.py) | 使用示例代码 | 10分钟 |

---

## ⚡ 按角色快速入门

### 👨‍💼 使用者（集成RAG功能）
1. 阅读 [QUICK_START.md](QUICK_START.md) (5分钟)
2. 查阅 [backend/README.md](backend/README.md) 的API部分 (15分钟)
3. 参考 [backend/example_usage.py](backend/example_usage.py) 的示例 (10分钟)

### 👨‍💻 开发者（维护和扩展）
1. 阅读 [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) (10分钟)
2. 学习 [TECHNICAL_DETAILS.md](TECHNICAL_DETAILS.md) (20分钟)
3. 查看源码：[backend/rag_backend.py](backend/rag_backend.py) 和 [backend/feedback_handler.py](backend/feedback_handler.py)

### 📊 产品经理（了解功能进度）
1. 查看 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) (10分钟)
2. 阅读 [DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md) (5分钟)

---

## 🎯 项目概览

**RAG系统后端** 是基于UltraRAG框架的高级RAG系统实现，包含：

✅ **多轮对话支持** - 灵活控制每一轮是否使用检索  
✅ **动态查询注入** - 代码驱动，无需手动创建查询文件  
✅ **三层反馈系统** - 点赞、详细反馈、改进建议  
✅ **完整会话管理** - 自动保存和加载会话  
✅ **生产就绪** - 完善的错误处理和资源管理  

**总代码量**: 2000+ 行  
**文档完整性**: 25+ 页  
**项目状态**: ✅ 完成且生产就绪  

---

## 🚀 快速开始（30秒）

```python
from backend import RAGBackend

# 初始化
rag = RAGBackend(ultrarag_path="/path/to/UltraRAG")

# 单轮查询
result = rag.query(
    query_text="如何提交python程序？",
    use_retrieval=True
)
print(result['answer'])

# 保存会话
rag.save_session()
```

更多示例，查看 [QUICK_START.md](QUICK_START.md)

---

## 📁 项目结构

```
RAGWorkProject/
├── backend/                    💻 后端代码
│   ├── rag_backend.py         核心RAG系统
│   ├── feedback_handler.py    反馈处理
│   ├── example_usage.py       使用示例
│   └── README.md              API文档
├── config/
│   ├── logs/                  💾 对话日志（自动生成）
│   ├── feedback/              💬 反馈文件（自动生成）
│   └── better_suggestions/    💡 建议文件（自动生成）
└── UltraRAG/                  框架
```

---

## 📖 核心文档

- **[QUICK_START.md](QUICK_START.md)** - 5分钟快速开始指南
- **[backend/README.md](backend/README.md)** - 完整API文档
- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - 系统架构和数据流
- **[TECHNICAL_DETAILS.md](TECHNICAL_DETAILS.md)** - 技术实现细节
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - 项目总结报告
- **[DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md)** - 交付验证清单

---

版本 created by Lu using UltraRAG.  
改造版本：0.1.0 (Backend) - 2024-01-21


