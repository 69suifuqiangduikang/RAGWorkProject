#!/usr/bin/env python
"""
RAG API 客户端示例

演示如何通过API进行多轮对话、反馈收集等操作
"""

import requests
import json
import time
from typing import Optional

BASE_URL = "http://127.0.0.1:8000"


class RAGAPIClient:
    """RAG API 客户端"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session_id: Optional[str] = None
    
    def init_session(self) -> str:
        """初始化一个新会话"""
        response = requests.post(f"{self.base_url}/api/sessions/init")
        response.raise_for_status()
        data = response.json()
        self.session_id = data["session_id"]
        return self.session_id
    
    def chat(self, content: str, use_retrieval: bool = True, top_k: int = 5) -> dict:
        """发送对话（非流式）"""
        if not self.session_id:
            raise ValueError("未初始化会话，请先调用 init_session()")
        
        message = {
            "content": content,
            "use_retrieval": use_retrieval,
            "top_k": top_k
        }
        response = requests.post(
            f"{self.base_url}/api/chat?session_id={self.session_id}",
            json=message
        )
        response.raise_for_status()
        return response.json()
    
    def chat_stream(self, content: str) -> str:
        """发送对话（流式）"""
        if not self.session_id:
            raise ValueError("未初始化会话，请先调用 init_session()")
        
        message = {
            "content": content,
            "use_retrieval": False,
            "top_k": 5
        }
        response = requests.post(
            f"{self.base_url}/api/chat/stream?session_id={self.session_id}",
            json=message,
            stream=True
        )
        response.raise_for_status()
        
        full_answer = ""
        for chunk in response.iter_content(decode_unicode=True):
            if chunk:
                print(chunk, end="", flush=True)
                full_answer += chunk
        print()  # 新行
        return full_answer
    
    def like_feedback(self, turn_id: int, reason: str = "", user_id: str = ""):
        """点赞反馈"""
        if not self.session_id:
            raise ValueError("未初始化会话")
        
        response = requests.post(
            f"{self.base_url}/api/feedback/like",
            params={
                "session_id": self.session_id,
                "turn_id": turn_id,
                "reason": reason,
                "user_id": user_id or None
            }
        )
        response.raise_for_status()
        return response.json()
    
    def detailed_feedback(
        self,
        turn_id: int,
        feedback_text: str,
        category: str = "general",
        user_id: str = "",
        score: Optional[int] = None
    ) -> dict:
        """提交详细反馈"""
        if not self.session_id:
            raise ValueError("未初始化会话")
        
        feedback = {
            "session_id": self.session_id,
            "turn_id": turn_id,
            "feedback_text": feedback_text,
            "category": category,
            "user_id": user_id or None,
            "score": score
        }
        response = requests.post(
            f"{self.base_url}/api/feedback/detailed?session_id={self.session_id}",
            json=feedback
        )
        response.raise_for_status()
        return response.json()
    
    def suggest_better(
        self,
        turn_id: int,
        suggested_answer: str,
        reason: str = "",
        user_id: str = "",
        score: Optional[int] = None
    ) -> dict:
        """提交更好的建议"""
        if not self.session_id:
            raise ValueError("未初始化会话")
        
        suggestion = {
            "session_id": self.session_id,
            "turn_id": turn_id,
            "suggested_answer": suggested_answer,
            "reason": reason,
            "user_id": user_id or None,
            "score": score
        }
        response = requests.post(
            f"{self.base_url}/api/feedback/suggest?session_id={self.session_id}",
            json=suggestion
        )
        response.raise_for_status()
        return response.json()
    
    def get_session_info(self) -> dict:
        """获取会话信息"""
        if not self.session_id:
            raise ValueError("未初始化会话")
        
        response = requests.get(f"{self.base_url}/api/sessions/{self.session_id}")
        response.raise_for_status()
        return response.json()
    
    def save_session(self) -> dict:
        """保存会话"""
        if not self.session_id:
            raise ValueError("未初始化会话")
        
        response = requests.post(f"{self.base_url}/api/sessions/{self.session_id}/save")
        response.raise_for_status()
        return response.json()


def example_1_basic_chat():
    """示例 1: 基础对话"""
    print("\n" + "="*60)
    print("示例 1: 基础对话（检索模式）")
    print("="*60)
    
    client = RAGAPIClient()
    client.init_session()
    print(f"✅ 会话已创建: {client.session_id[:12]}...")
    
    # 发送第一条消息
    print("\n📤 发送消息: 如何提交我写好的python训练程序？")
    result = client.chat(
        "如何提交我写好的python训练程序？",
        use_retrieval=True,
        top_k=5
    )
    
    print(f"\n📥 回答({result['status']}):")
    answer = result['answer']
    if len(answer) > 150:
        print(answer[:150] + "...")
    else:
        print(answer)
    
    print(f"\n📊 对话轮数: {result['turn_id']}")
    print(f"🔍 使用检索: {result['use_retrieval']}")


def example_2_stream_chat():
    """示例 2: 流式对话"""
    print("\n" + "="*60)
    print("示例 2: 流式对话（无检索模式）")
    print("="*60)
    
    client = RAGAPIClient()
    client.init_session()
    print(f"✅ 会话已创建: {client.session_id[:12]}...")
    
    print("\n📤 发送消息: 请简单介绍一下python编程语言")
    print("📥 流式回答:")
    print("-" * 40)
    try:
        client.chat_stream("请简单介绍一下python编程语言")
    except Exception as e:
        print(f"\n⚠️ 流式对话失败: {e}")
        print("💡 提示: 请确保在 config/backend.yaml 中配置了正确的 API key")
    print("-" * 40)


def example_3_feedback():
    """示例 3: 多轮对话与反馈"""
    print("\n" + "="*60)
    print("示例 3: 多轮对话与反馈")
    print("="*60)
    
    client = RAGAPIClient()
    client.init_session()
    print(f"✅ 会话已创建: {client.session_id[:12]}...")
    
    # 第一轮：检索模式
    print("\n📤 轮次1: 如何提交python训练程序？(检索)")
    try:
        result = client.chat(
            "如何提交我写好的python训练程序？",
            use_retrieval=True
        )
        print(f"✅ 收到回答，状态: {result['status']}")
    except Exception as e:
        print(f"⚠️ 请求失败: {e}")
        print("💡 RAG模式可能需要UltraRAG Pipeline正常运行")
        return
    
    # 第二轮：无检索流式
    print("\n📤 轮次2: 有什么注意事项吗？(流式)")
    print("📥 流式回答:")
    print("-" * 40)
    try:
        client.chat_stream("有什么注意事项吗？")
    except Exception as e:
        print(f"\n⚠️ 流式对话失败: {e}")
        print("💡 提示: 请确保在 config/backend.yaml 中配置了正确的 API key")
    print("-" * 40)
    
    # 点赞第一个回答
    print("\n👍 点赞第一个回答...")
    try:
        like_result = client.like_feedback(0, reason="回答很全面", user_id="user_001")
        print(f"✅ {like_result['message']}")
    except Exception as e:
        print(f"⚠️ 点赞失败: {e}")
    
    # 详细反馈
    print("\n💬 为第一个回答提交详细反馈...")
    try:
        feedback_result = client.detailed_feedback(
            turn_id=0,
            feedback_text="回答缺少具体的代码示例",
            category="完整性",
            user_id="user_001",
            score=4
        )
        print(f"✅ {feedback_result['message']}")
    except Exception as e:
        print(f"⚠️ 反馈失败: {e}")
    
    # 查看会话信息
    print("\n📋 会话信息:")
    try:
        session_info = client.get_session_info()
        print(f"   总轮数: {session_info['total_turns']}")
        print(f"   持续时间: {session_info['duration_seconds']:.2f} 秒")
    except Exception as e:
        print(f"⚠️ 获取会话信息失败: {e}")
    
    # 保存会话
    print("\n💾 保存会话...")
    try:
        save_result = client.save_session()
        print(f"✅ {save_result['message']}")
        print(f"   路径: {save_result['saved_path']}")
    except Exception as e:
        print(f"⚠️ 保存失败: {e}")


def example_4_suggestion():
    """示例 4: 提交建议"""
    print("\n" + "="*60)
    print("示例 4: 提交更好的建议")
    print("="*60)
    
    client = RAGAPIClient()
    client.init_session()
    print(f"✅ 会话已创建: {client.session_id[:12]}...")
    
    # 发送一条消息
    print("\n📤 发送消息: Python的优势是什么？")
    result = client.chat(
        "Python的优势是什么？",
        use_retrieval=False
    )
    print(f"✅ 收到回答")
    
    # 建议更好的答案
    print("\n💡 提交更好的建议...")
    suggestion_result = client.suggest_better(
        turn_id=0,
        suggested_answer="Python的主要优势包括：1. 易学易用，语法简洁 2. 库生态丰富 3. 跨平台支持 4. 在数据科学领域应用广泛",
        reason="建议补充具体的优势列表",
        user_id="user_001",
        score=5
    )
    print(f"✅ {suggestion_result['message']}")
    print(f"   路径: {suggestion_result['saved_path']}")


def main():
    """主程序"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║      RAG API 客户端使用示例                             ║
    ╠════════════════════════════════════════════════════════╣
    ║  请先启动API服务:                                       ║
    ║  python run_api.py                                    ║
    ║                                                        ║
    ║  然后在另一个终端运行本脚本                             ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # 检查服务健康
    print("\n🔍 检查服务健康...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ 服务可用 (状态码: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务，请确保 {BASE_URL} 可访问")
        print(f"   运行: python run_api.py")
        return
    except Exception as e:
        print(f"❌ 错误: {e}")
        return
    
    # 运行示例
    try:
        example_1_basic_chat()
        time.sleep(1)
        
        example_2_stream_chat()
        time.sleep(1)
        
        example_3_feedback()
        time.sleep(1)
        
        example_4_suggestion()
        
        print("\n" + "="*60)
        print("✅ 示例运行完成！")
        print("="*60)
        print("\n💡 如有错误，请检查：")
        print("1. config/backend.yaml 中的API配置")
        print("2. UltraRAG Pipeline是否正常运行")
        print("3. 网络连接是否正常")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求错误: {e}")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
