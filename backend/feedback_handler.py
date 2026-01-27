"""
反馈处理模块

支持三种类型的反馈：
1. 点赞/点踩 - 伴随对话记录保存
2. 详细反馈 - 保存到单独文件夹
3. 更好的建议 - 保存到单独文件夹
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List


class FeedbackHandler:
    """反馈处理系统"""
    
    def __init__(
        self,
        feedback_dir: str = "config/feedback",
        suggestions_dir: str = "config/better_suggestions"
    ):
        """
        初始化反馈处理器
        
        Args:
            feedback_dir: 详细反馈保存目录
            suggestions_dir: 更好建议保存目录
        """
        self.feedback_dir = feedback_dir
        self.suggestions_dir = suggestions_dir
        
        # 创建必要的目录
        Path(self.feedback_dir).mkdir(parents=True, exist_ok=True)
        Path(self.suggestions_dir).mkdir(parents=True, exist_ok=True)
    
    def add_like_dislike(
        self,
        session_id: str,
        turn_id: int,
        is_like: bool,
        query: str,
        answer: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        记录点赞/点踩反馈
        
        这种反馈直接伴随对话记录保存，应该在RAGBackend中调用。
        本函数返回反馈数据结构供外部使用。
        
        Args:
            session_id: 会话ID
            turn_id: 对话轮次ID
            is_like: True表示点赞，False表示点踩
            query: 查询文本
            answer: 答案文本
            reason: 反馈原因（可选）
            
        Returns:
            反馈数据字典
        """
        feedback_data = {
            'feedback_type': 'like_dislike',
            'session_id': session_id,
            'turn_id': turn_id,
            'is_like': is_like,
            'feedback_value': 'like' if is_like else 'dislike',
            'query': query,
            'answer': answer,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        return feedback_data
    
    def submit_feedback(
        self,
        session_id: str,
        turn_id: int,
        query: str,
        answer: str,
        feedback_text: str,
        feedback_category: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交详细反馈
        
        反馈内容会保存到独立文件夹中，用于后续分析和改进。
        
        Args:
            session_id: 会话ID
            turn_id: 对话轮次ID
            query: 查询文本
            answer: 回复文本
            feedback_text: 详细反馈内容
            feedback_category: 反馈类别（如'准确性', '完整性', '清晰度'等）
            user_id: 用户ID（可选）
            
        Returns:
            反馈数据字典及保存路径
        """
        feedback_id = f"{session_id}_{turn_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        feedback_data = {
            'feedback_id': feedback_id,
            'feedback_type': 'detailed_feedback',
            'session_id': session_id,
            'turn_id': turn_id,
            'user_id': user_id,
            'query': query,
            'answer': answer,
            'feedback_text': feedback_text,
            'feedback_category': feedback_category,
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存到文件
        filename = f"{feedback_id}.json"
        filepath = os.path.join(self.feedback_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)
        
        feedback_data['saved_path'] = filepath
        
        return feedback_data
    
    def submit_better_suggestion(
        self,
        session_id: str,
        turn_id: int,
        query: str,
        original_answer: str,
        suggested_answer: str,
        improvement_reason: str,
        user_id: Optional[str] = None,
        quality_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        提交更好的建议（用户认为AI应该这样回答）
        
        这些建议可用于微调模型或改进提示词。
        
        Args:
            session_id: 会话ID
            turn_id: 对话轮次ID
            query: 原始查询
            original_answer: 原始答案
            suggested_answer: 用户建议的答案
            improvement_reason: 改进原因说明
            user_id: 用户ID（可选）
            quality_score: 建议质量评分（1-5，可选）
            
        Returns:
            建议数据字典及保存路径
        """
        suggestion_id = f"{session_id}_{turn_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        suggestion_data = {
            'suggestion_id': suggestion_id,
            'feedback_type': 'better_suggestion',
            'session_id': session_id,
            'turn_id': turn_id,
            'user_id': user_id,
            'query': query,
            'original_answer': original_answer,
            'suggested_answer': suggested_answer,
            'improvement_reason': improvement_reason,
            'quality_score': quality_score,
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存到文件
        filename = f"{suggestion_id}.json"
        filepath = os.path.join(self.suggestions_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(suggestion_data, f, ensure_ascii=False, indent=2)
        
        suggestion_data['saved_path'] = filepath
        
        return suggestion_data
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """获取反馈统计信息"""
        feedback_files = Path(self.feedback_dir).glob('*.json')
        suggestion_files = Path(self.suggestions_dir).glob('*.json')
        
        feedback_count = len(list(feedback_files))
        suggestion_count = len(list(suggestion_files))
        
        return {
            'feedback_count': feedback_count,
            'suggestion_count': suggestion_count,
            'total_feedback': feedback_count + suggestion_count,
            'feedback_dir': self.feedback_dir,
            'suggestions_dir': self.suggestions_dir
        }
    
    def get_feedback_by_session(self, session_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取某个会话的所有反馈
        
        Args:
            session_id: 会话ID
            
        Returns:
            包含该会话所有反馈和建议的字典
        """
        feedback_list = []
        suggestion_list = []
        
        # 搜索反馈文件
        for filepath in Path(self.feedback_dir).glob('*.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('session_id') == session_id:
                    feedback_list.append(data)
        
        # 搜索建议文件
        for filepath in Path(self.suggestions_dir).glob('*.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('session_id') == session_id:
                    suggestion_list.append(data)
        
        return {
            'session_id': session_id,
            'feedback': feedback_list,
            'suggestions': suggestion_list,
            'total_count': len(feedback_list) + len(suggestion_list)
        }
    
    def export_all_feedback(self, export_path: str) -> str:
        """
        导出所有反馈为CSV或JSON文件
        
        Args:
            export_path: 导出文件路径
            
        Returns:
            导出的文件路径
        """
        all_data = {
            'feedback': [],
            'suggestions': [],
            'export_time': datetime.now().isoformat()
        }
        
        # 收集所有反馈
        for filepath in Path(self.feedback_dir).glob('*.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                all_data['feedback'].append(json.load(f))
        
        # 收集所有建议
        for filepath in Path(self.suggestions_dir).glob('*.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                all_data['suggestions'].append(json.load(f))
        
        # 保存导出文件
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        return export_path


class SessionWithFeedback:
    """
    增强的会话管理类，集成反馈功能
    
    此类用于在RAGBackend的结果中自动添加反馈能力
    """
    
    def __init__(self, backend, feedback_handler: FeedbackHandler):
        """
        初始化带反馈的会话
        
        Args:
            backend: RAGBackend实例
            feedback_handler: FeedbackHandler实例
        """
        self.backend = backend
        self.feedback_handler = feedback_handler
    
    def query_with_feedback_support(
        self,
        query_text: str,
        use_retrieval: bool = True,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        执行查询并返回支持反馈的结果
        
        Args:
            query_text: 查询文本
            use_retrieval: 是否使用检索
            top_k: 检索返回数量
            
        Returns:
            包含反馈功能的结果
        """
        result = self.backend.query(
            query_text=query_text,
            use_retrieval=use_retrieval,
            top_k=top_k
        )
        
        # 添加反馈函数引用
        result['feedback_functions'] = {
            'like': lambda reason=None: self.feedback_handler.add_like_dislike(
                session_id=self.backend.session_id,
                turn_id=result['turn_id'],
                is_like=True,
                query=result['query'],
                answer=result.get('answer', ''),
                reason=reason
            ),
            'dislike': lambda reason=None: self.feedback_handler.add_like_dislike(
                session_id=self.backend.session_id,
                turn_id=result['turn_id'],
                is_like=False,
                query=result['query'],
                answer=result.get('answer', ''),
                reason=reason
            ),
            'submit_feedback': lambda feedback_text, category=None, user_id=None: \
                self.feedback_handler.submit_feedback(
                    session_id=self.backend.session_id,
                    turn_id=result['turn_id'],
                    query=result['query'],
                    answer=result.get('answer', ''),
                    feedback_text=feedback_text,
                    feedback_category=category,
                    user_id=user_id
                ),
            'suggest_better': lambda suggested_answer, reason, user_id=None, score=None: \
                self.feedback_handler.submit_better_suggestion(
                    session_id=self.backend.session_id,
                    turn_id=result['turn_id'],
                    query=result['query'],
                    original_answer=result.get('answer', ''),
                    suggested_answer=suggested_answer,
                    improvement_reason=reason,
                    user_id=user_id,
                    quality_score=score
                )
        }
        
        return result


if __name__ == "__main__":
    # 使用示例
    handler = FeedbackHandler()
    
    # 提交详细反馈示例
    feedback = handler.submit_feedback(
        session_id="sess_123",
        turn_id=0,
        query="如何提交python程序？",
        answer="通过官网提交表单...",
        feedback_text="答案太简洁，需要更多具体的步骤说明",
        feedback_category="完整性",
        user_id="user_456"
    )
    print("反馈已保存:", feedback)
    
    # 提交更好的建议示例
    suggestion = handler.submit_better_suggestion(
        session_id="sess_123",
        turn_id=0,
        query="如何提交python程序？",
        original_answer="通过官网提交表单...",
        suggested_answer="请按以下步骤提交：1. 访问官网 2. 登录账户 3. 点击提交按钮 4. 选择文件并填写信息...",
        improvement_reason="原答案缺少具体的分步指导",
        user_id="user_456",
        quality_score=4
    )
    print("建议已保存:", suggestion)
    
    # 获取统计信息
    stats = handler.get_feedback_statistics()
    print("反馈统计:", stats)
