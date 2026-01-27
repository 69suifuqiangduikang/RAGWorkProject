"""
RAG系统后端模块

包含：
- RAGBackend: 核心RAG系统，支持多轮对话和灵活的检索控制
- FeedbackHandler: 反馈处理系统，支持点赞、详细反馈和建议
- SessionWithFeedback: 集成反馈功能的会话管理
"""

from .rag_backend import RAGBackend
from .feedback_handler import FeedbackHandler, SessionWithFeedback

__all__ = [
    'RAGBackend',
    'FeedbackHandler',
    'SessionWithFeedback'
]

__version__ = '0.1.0'
