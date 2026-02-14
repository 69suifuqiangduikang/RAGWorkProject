"""
RAG后端 FastAPI 应用封装

支持多轮对话、流式响应、反馈收集
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from rag_backend import RAGBackend
from feedback_handler import FeedbackHandler

# ==================== Pydantic Models ====================

class MessageInput(BaseModel):
    """用户消息模型"""
    content: str = Field(..., description="消息内容")
    use_retrieval: bool = Field(default=True, description="是否使用检索")
    top_k: int = Field(default=5, description="检索文档数")


class SessionInit(BaseModel):
    """会话初始化响应"""
    session_id: str = Field(..., description="会话ID")
    created_at: str = Field(..., description="创建时间")


class Turn(BaseModel):
    """对话轮次模型"""
    turn_id: int = Field(..., description="轮次ID")
    query: str = Field(..., description="用户查询")
    answer: str = Field(..., description="系统回答")
    use_retrieval: bool = Field(..., description="是否使用检索")
    timestamp: str = Field(..., description="时间戳")
    status: str = Field(..., description="状态（success/error）")
    retrieved_docs: List[Any] = Field(default_factory=list, description="检索到的文档")
    retrieved_images: List[str] = Field(default_factory=list, description="检索到的图片路径")


class ChatResponse(BaseModel):
    """对话响应模型"""
    session_id: str = Field(..., description="会话ID")
    turn_id: int = Field(..., description="当前轮次ID")
    query: str = Field(..., description="用户查询")
    answer: str = Field(..., description="系统回答")
    use_retrieval: bool = Field(..., description="是否使用检索")
    status: str = Field(..., description="状态")
    timestamp: str = Field(..., description="时间戳")
    retrieved_docs: List[Any] = Field(default_factory=list, description="检索到的文档")
    retrieved_images: List[str] = Field(default_factory=list, description="检索到的图片路径")
    conversation_history: List[Turn] = Field(default_factory=list, description="对话历史")


class FeedbackInput(BaseModel):
    """反馈模型"""
    session_id: str = Field(..., description="会话ID")
    turn_id: int = Field(..., description="反馈的轮次ID")
    feedback_text: str = Field(default="", description="反馈文本")
    category: str = Field(default="general", description="反馈类别")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    score: Optional[int] = Field(default=None, ge=1, le=5, description="评分(1-5)")


class SuggestionInput(BaseModel):
    """建议模型"""
    session_id: str = Field(..., description="会话ID")
    turn_id: int = Field(..., description="涉及的轮次ID")
    suggested_answer: str = Field(..., description="建议的答案")
    reason: str = Field(default="", description="建议原因")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    score: Optional[int] = Field(default=None, ge=1, le=5, description="评分(1-5)")


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="RAG多轮对话API",
    description="支持多轮对话、流式响应、反馈收集的RAG系统API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 全局配置和初始化 ====================

RAG_PATH = "/root/workspace/RAGWorkProject/UltraRAG"
LOG_DIR = "/root/workspace/RAGWorkProject/config/logs"
CONFIG_DIR = "/root/workspace/RAGWorkProject/config"
PROJECT_ROOT = "/root/workspace/RAGWorkProject"
ALLOWED_IMAGE_ROOTS = [Path(RAG_PATH).resolve(), Path(PROJECT_ROOT).resolve()]

# 全局单例：RAG Pipeline（所有用户共享同一个知识库）
global_rag_backend: Optional[RAGBackend] = None

# 全局会话存储（生产环境应使用数据库）
# sessions[session_id] = {
#     "conversation_history": [...],
#     "openai_client": OpenAI(...),  # 每个用户独立的OpenAI客户端
#     "created_at": datetime
# }
sessions: Dict[str, Dict[str, Any]] = {}

feedback_handler = FeedbackHandler(
    feedback_dir=str(Path(CONFIG_DIR) / "feedback"),
    suggestions_dir=str(Path(CONFIG_DIR) / "better_suggestions")
)


@app.on_event("startup")
async def startup_event():
    """API启动时初始化全局RAG Pipeline"""
    global global_rag_backend
    print("🚀 初始化全局RAG Pipeline...")
    global_rag_backend = RAGBackend(
        ultrarag_path=RAG_PATH,
        log_dir=LOG_DIR
    )
    print("✅ RAG Pipeline初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """API关闭时清理资源"""
    global global_rag_backend
    if global_rag_backend:
        print("🧹 清理RAG Pipeline资源...")
        global_rag_backend.cleanup()
        print("✅ 资源清理完成")


# ==================== 会话管理 ====================

@app.post("/api/sessions/init", response_model=SessionInit, summary="初始化会话")
async def init_session():
    """
    初始化一个新的对话会话（每个用户独立会话）
    
    Returns:
        SessionInit: 包含session_id和创建时间
    """
    session_id = str(uuid.uuid4())
    
    sessions[session_id] = {
        "conversation_history": [],
        "created_at": datetime.now()
    }
    
    return SessionInit(
        session_id=session_id,
        created_at=datetime.now().isoformat()
    )


def _get_session(session_id: str) -> Dict[str, Any]:
    """获取会话，不存在时抛出404"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
    return sessions[session_id]


@app.get("/api/assets/image", summary="获取检索图片")
def get_image(path: str = Query(..., description="图片文件路径")):
    """通过安全路径校验返回图片文件"""
    image_path = Path(path)
    if not image_path.is_absolute():
        image_path = Path(RAG_PATH) / image_path

    try:
        resolved = image_path.resolve(strict=True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="图片不存在")

    if not any(str(resolved).startswith(str(root)) for root in ALLOWED_IMAGE_ROOTS):
        raise HTTPException(status_code=403, detail="无权限访问该图片")

    return FileResponse(resolved)


# ==================== 对话接口 ====================

@app.post("/api/chat", response_model=ChatResponse, summary="发送对话消息（非流式）")
def chat(session_id: str, message: MessageInput):
    """
    发送对话消息并获取回复
    
    Args:
        session_id: 会话ID
        message: 消息内容和配置
        
    Returns:
        ChatResponse: 包含回复、历史记录等的响应
    """
    session = _get_session(session_id)
    history = session["conversation_history"]
    
    if message.use_retrieval:
        # 检索模式：直接调用全局RAG Pipeline
        result = global_rag_backend.query(
            query_text=message.content,
            use_retrieval=True,
            top_k=message.top_k,
            stream=False
        )
    else:
        # 无检索模式：携带会话历史做多轮对话
        messages = []
        for turn in history:
            messages.append({"role": "user", "content": turn['query']})
            messages.append({"role": "assistant", "content": turn['answer']})
        messages.append({"role": "user", "content": message.content})

        answer = global_rag_backend.chat_no_retrieval(messages)
        timestamp = datetime.now().isoformat()
        result = {
            "query": message.content,
            "answer": answer,
            "retrieved_docs": [],
            "use_retrieval": False,
            "timestamp": timestamp,
            "status": "success"
        }
    
    # 更新当前会话的对话历史
    turn_id = len(history)
    turn = Turn(
        turn_id=turn_id,
        query=result['query'],
        answer=result.get('answer') or '',
        use_retrieval=result['use_retrieval'],
        timestamp=result['timestamp'],
        status=result.get('status', 'unknown'),
        retrieved_docs=result.get('retrieved_docs', []),
        retrieved_images=result.get('retrieved_images', [])
    )
    history.append(turn.model_dump())
    
    # 构建响应
    return ChatResponse(
        session_id=session_id,
        turn_id=turn_id,
        query=result['query'],
        answer=result.get('answer') or '',
        use_retrieval=result['use_retrieval'],
        status=result.get('status', 'unknown'),
        timestamp=result['timestamp'],
        retrieved_docs=result.get('retrieved_docs', []),
        retrieved_images=result.get('retrieved_images', []),
        conversation_history=[Turn(**t) for t in history]
    )


@app.post("/api/chat/stream", summary="发送对话消息（流式）")
def chat_stream(session_id: str, message: MessageInput):
    """
    发送对话消息并流式返回回复（仅对无检索模式）
    
    对于有检索的RAG模式，请使用/api/chat端点。
    
    Args:
        session_id: 会话ID
        message: 消息内容
        
    Returns:
        StreamingResponse: 流式返回文本
    """
    session = _get_session(session_id)
    history = session["conversation_history"]
    
    if message.use_retrieval:
        raise HTTPException(
            status_code=400,
            detail="流式接口仅支持无检索模式。检索模式请使用/api/chat端点"
        )
    
    # 获取当前会话的消息历史供多轮对话
    messages = []
    for turn in history:
        messages.append({"role": "user", "content": turn['query']})
        messages.append({"role": "assistant", "content": turn['answer']})
    messages.append({"role": "user", "content": message.content})
    
    # 收集答案用于记录
    full_answer = []
    
    def generate():
        """生成流式响应"""
        for token in global_rag_backend.chat_no_retrieval_stream(messages):
            full_answer.append(token)
            yield token.encode('utf-8')
        
        # 流式结束后，保存到当前会话历史
        answer_text = ''.join(full_answer)
        turn = Turn(
            turn_id=len(history),
            query=message.content,
            answer=answer_text,
            use_retrieval=False,
            timestamp=datetime.now().isoformat(),
            status='success',
            retrieved_docs=[],
            retrieved_images=[]
            )
        history.append(turn.model_dump())
    
    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# ==================== 反馈接口 ====================

@app.post("/api/feedback/like", summary="点赞反馈")
async def like_feedback(
    session_id: str,
    turn_id: int,
    reason: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    对某个对话轮次进行点赞
    
    Args:
        session_id: 会话ID
        turn_id: 轮次ID
        reason: 点赞原因
        user_id: 用户ID
        
    Returns:
        反馈保存状态
    """
    session = _get_session(session_id)
    history = session["conversation_history"]
    
    # 验证turn_id有效
    if turn_id >= len(history):
        raise HTTPException(status_code=404, detail=f"轮次不存在: {turn_id}")
    
    turn = history[turn_id]
    
    # 调用反馈处理器保存
    feedback_data = {
        "session_id": session_id,
        "turn_id": turn_id,
        "feedback_type": "like",
        "reason": reason,
        "user_id": user_id,
        "query": turn['query'],
        "answer": turn['answer'],
        "timestamp": datetime.now().isoformat()
    }
    
    feedback_file = Path(feedback_handler.feedback_dir) / f"{session_id}_{turn_id}_like_{uuid.uuid4()}.json"
    feedback_file.parent.mkdir(parents=True, exist_ok=True)
    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump(feedback_data, f, ensure_ascii=False, indent=2)
    
    return {
        "status": "success",
        "message": "点赞反馈已保存",
        "saved_path": str(feedback_file)
    }


@app.post("/api/feedback/detailed", summary="详细反馈")
async def detailed_feedback(session_id: str, feedback: FeedbackInput):
    """
    提交对某个对话轮次的详细反馈
    
    Args:
        session_id: 会话ID
        feedback: 反馈内容
        
    Returns:
        反馈保存状态
    """
    session = _get_session(session_id)
    history = session["conversation_history"]
    
    # 验证turn_id有效
    if feedback.turn_id >= len(history):
        raise HTTPException(status_code=404, detail=f"轮次不存在: {feedback.turn_id}")
    
    turn = history[feedback.turn_id]
    
    # 保存反馈
    feedback_data = {
        "session_id": feedback.session_id,
        "turn_id": feedback.turn_id,
        "feedback_type": "detailed",
        "feedback_text": feedback.feedback_text,
        "category": feedback.category,
        "user_id": feedback.user_id,
        "score": feedback.score,
        "query": turn['query'],
        "answer": turn['answer'],
        "timestamp": datetime.now().isoformat()
    }
    
    feedback_file = Path(feedback_handler.feedback_dir) / f"{session_id}_{feedback.turn_id}_detailed_{uuid.uuid4().hex[:8]}.json"
    feedback_file.parent.mkdir(parents=True, exist_ok=True)
    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump(feedback_data, f, ensure_ascii=False, indent=2)
    
    return {
        "status": "success",
        "message": "详细反馈已保存",
        "saved_path": str(feedback_file)
    }


@app.post("/api/feedback/suggest", summary="提交更好的建议")
async def suggest_better(session_id: str, suggestion: SuggestionInput):
    """
    提交对某个对话轮次的更好答案建议
    
    Args:
        session_id: 会话ID
        suggestion: 建议内容
        
    Returns:
        建议保存状态
    """
    session = _get_session(session_id)
    history = session["conversation_history"]
    
    # 验证turn_id有效
    if suggestion.turn_id >= len(history):
        raise HTTPException(status_code=404, detail=f"轮次不存在: {suggestion.turn_id}")
    
    turn = history[suggestion.turn_id]
    
    # 保存建议
    suggestion_data = {
        "session_id": suggestion.session_id,
        "turn_id": suggestion.turn_id,
        "suggested_answer": suggestion.suggested_answer,
        "reason": suggestion.reason,
        "user_id": suggestion.user_id,
        "score": suggestion.score,
        "original_query": turn['query'],
        "original_answer": turn['answer'],
        "timestamp": datetime.now().isoformat()
    }
    
    suggestion_file = Path(feedback_handler.suggestions_dir) / f"{session_id}_{suggestion.turn_id}_suggestion_{uuid.uuid4().hex[:8]}.json"
    suggestion_file.parent.mkdir(parents=True, exist_ok=True)
    with open(suggestion_file, 'w', encoding='utf-8') as f:
        json.dump(suggestion_data, f, ensure_ascii=False, indent=2)
    
    return {
        "status": "success",
        "message": "建议已保存",
        "saved_path": str(suggestion_file)
    }


# ==================== 会话管理接口 ====================

@app.get("/api/sessions/{session_id}", summary="获取会话信息")
async def get_session_info(session_id: str):
    """
    获取会话的对话历史和信息
    
    Args:
        session_id: 会话ID
        
    Returns:
        会话信息和对话历史
    """
    session = _get_session(session_id)
    history = session["conversation_history"]
    created_at = session.get("created_at")
    return {
        "session_id": session_id,
        "created_at": created_at.isoformat() if created_at else None,
        "start_time": created_at.isoformat() if created_at else None,
        "total_turns": len(history),
        "duration_seconds": (datetime.now() - created_at).total_seconds() if created_at else None,
        "conversation_history": [Turn(**t) for t in history]
    }


@app.post("/api/sessions/{session_id}/save", summary="保存会话到文件")
async def save_session(session_id: str):
    """
    将会话保存到文件
    
    Args:
        session_id: 会话ID
        
    Returns:
        保存路径
    """
    session = _get_session(session_id)
    history = session["conversation_history"]
    created_at = session.get("created_at")

    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    saved_path = Path(LOG_DIR) / f"session_{session_id}.json"

    data = {
        "session_id": session_id,
        "created_at": created_at.isoformat() if created_at else None,
        "history": history
    }
    with open(saved_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "status": "success",
        "message": "会话已保存",
        "saved_path": str(saved_path)
    }


@app.delete("/api/sessions/{session_id}", summary="删除会话")
async def delete_session(session_id: str):
    """
    删除内存中的会话（会话日志文件不删除）
    
    Args:
        session_id: 会话ID
        
    Returns:
        删除状态
    """
    session = _get_session(session_id)
    history = session["conversation_history"]
    created_at = session.get("created_at")

    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    saved_path = Path(LOG_DIR) / f"session_{session_id}.json"

    data = {
        "session_id": session_id,
        "created_at": created_at.isoformat() if created_at else None,
        "history": history
    }
    with open(saved_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    del sessions[session_id]
    
    return {
        "status": "success",
        "message": "会话已删除，数据已保存",
        "saved_path": str(saved_path)
    }


# ==================== 健康检查 ====================

@app.get("/health", summary="健康检查")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
