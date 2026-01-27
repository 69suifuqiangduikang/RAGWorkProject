"""
RAG系统后端集成示例

展示如何使用RAGBackend和FeedbackHandler进行多轮对话和反馈收集
"""

import sys
import os
from pathlib import Path

# 添加后端模块到路径
sys.path.insert(0, str(Path(__file__).parent))

from rag_backend import RAGBackend
from feedback_handler import FeedbackHandler, SessionWithFeedback


def example_streaming_rag():
    """流式RAG生成示例"""
    print("\n" + "="*60)
    print("示例0: 流式RAG生成")
    print("="*60)

    rag = RAGBackend(
        ultrarag_path="/root/workspace/RAGWorkProject/UltraRAG",
        log_dir="/root/workspace/RAGWorkProject/config/logs"
    )

    # 若未配置模型则跳过演示，避免报错
    if not (rag.config.get("rag", {}).get("model")):
        print("(跳过: 未配置rag.model，填写config/backend.yaml后再试)")
        return rag

    print("问题: 如何提交我写好的python训练程序？")
    print("回答(流式): ", end="", flush=True)

    def on_token(tok: str):
        print(tok, end="", flush=True)

    result = rag.query(
        query_text="如何提交我写好的python训练程序？",
        use_retrieval=True,
        top_k=5,
        stream=True,
        on_token=on_token
    )

    print("\n\n状态:", result.get('status', 'unknown'))
    return rag


def example_streaming_no_retrieval():
    """无检索流式多轮对话示例"""
    print("\n" + "="*60)
    print("示例0b: 无检索流式多轮对话")
    print("="*60)

    rag = RAGBackend(
        ultrarag_path="/root/workspace/RAGWorkProject/UltraRAG",
        log_dir="/root/workspace/RAGWorkProject/config/logs"
    )

    # 若未配置模型则跳过演示，避免报错
    if not (rag.config.get("no_retrieval", {}).get("model")):
        print("(跳过: 未配置no_retrieval.model，填写config/backend.yaml后再试)")
        return rag

    messages = [
        {"role": "system", "content": "你是一个乐于助人的助理。"},
        {"role": "user", "content": "请给我提交python训练程序的步骤要点。"}
    ]

    print("回答(流式): ", end="", flush=True)
    for tok in rag.chat_no_retrieval_stream(messages):
        print(tok, end="", flush=True)
    print()
    return rag


def example_single_turn_query():
    """单轮查询示例"""
    print("\n" + "="*60)
    print("示例1: 单轮查询")
    print("="*60)
    
    rag = RAGBackend(
        ultrarag_path="/root/workspace/RAGWorkProject/UltraRAG",
        log_dir="/root/workspace/RAGWorkProject/config/logs"
    )
    
    # 执行查询（带检索）
    result = rag.query(
        query_text="如何提交我写好的python训练程序？",
        use_retrieval=True,
        top_k=5
    )
    
    print(f"\n会话ID: {rag.session_id}")
    print(f"查询: {result['query']}")
    print(f"是否使用检索: {result['use_retrieval']}")
    ans = result.get('answer')
    print(f"答案: {str(ans) if ans is not None else 'N/A'}")
    print(f"状态: {result.get('status', 'unknown')}")
    
    # 保存会话
    saved_path = rag.save_session()
    print(f"\n会话已保存到: {saved_path}")
    
    return rag


def example_multi_turn_conversation():
    """多轮对话示例"""
    print("\n" + "="*60)
    print("示例2: 多轮对话（部分使用检索）")
    print("="*60)
    
    rag = RAGBackend(
        ultrarag_path="/root/workspace/RAGWorkProject/UltraRAG",
        log_dir="/root/workspace/RAGWorkProject/config/logs"
    )
    
    # 多轮对话配置
    queries = [
        {
            'text': '如何提交我写好的python训练程序？',
            'use_retrieval': True,
            'top_k': 5
        },
        {
            'text': '有什么注意事项吗？',
            'use_retrieval': False  # 这一轮不使用检索
        },
        {
            'text': '提交后多久会有反馈？',
            'use_retrieval': True,
            'top_k': 3
        }
    ]
    
    conv_result = rag.multi_turn_conversation(queries)
    
    print(f"\n会话ID: {conv_result['session_id']}")
    print(f"总轮次: {conv_result['total_turns']}")
    print(f"会话时长: {conv_result['session_duration']:.2f}秒")
    
    print("\n对话详情:")
    for i, result in enumerate(conv_result['results'], 1):
        print(f"\n轮次 {i}: {result['query']}")
        print(f"  使用检索: {result['use_retrieval']}")
        print(f"  状态: {result.get('status', 'unknown')}")
        ans = result.get('answer')
        short = (str(ans) if ans is not None else 'N/A')
        print(f"  答案: {short[:100]}...")
    
    # 获取对话总结
    summary = rag.get_conversation_summary()
    print(f"\n对话总结:")
    print(f"  总轮数: {summary['total_turns']}")
    print(f"  会话时长: {summary['duration_seconds']:.2f}秒")
    
    # 保存会话
    saved_path = rag.save_session()
    print(f"\n会话已保存到: {saved_path}")
    
    return rag


def example_with_feedback():
    """带反馈的对话示例"""
    print("\n" + "="*60)
    print("示例3: 带反馈收集的对话")
    print("="*60)
    
    rag = RAGBackend(
        ultrarag_path="/root/workspace/RAGWorkProject/UltraRAG",
        log_dir="/root/workspace/RAGWorkProject/config/logs"
    )
    
    feedback_handler = FeedbackHandler(
        feedback_dir="/root/workspace/RAGWorkProject/config/feedback",
        suggestions_dir="/root/workspace/RAGWorkProject/config/better_suggestions"
    )
    
    # 创建带反馈支持的会话
    session = SessionWithFeedback(rag, feedback_handler)
    
    # 执行查询
    result = session.query_with_feedback_support(
        query_text="如何提交我写好的python训练程序？",
        use_retrieval=True,
        top_k=5
    )
    
    print(f"\n会话ID: {rag.session_id}")
    print(f"查询: {result['query']}")
    print(f"答案: {result.get('answer', 'N/A')[:100]}...")
    
    # 演示反馈功能
    print("\n--- 反馈演示 ---")
    
    # 1. 点赞反馈
    like_feedback = result['feedback_functions']['like'](reason="回答很全面")
    print(f"点赞反馈: {like_feedback}")
    
    # 2. 详细反馈
    detailed_feedback = result['feedback_functions']['submit_feedback'](
        feedback_text="答案缺少具体的代码示例",
        category="完整性",
        user_id="user_001"
    )
    print(f"详细反馈已保存: {detailed_feedback.get('saved_path')}")
    
    # 3. 更好的建议
    suggestion = result['feedback_functions']['suggest_better'](
        suggested_answer="请按以下步骤提交：1. 访问官网提交页面 2. 登录账户 3. 上传Python文件 4. 填写程序描述 5. 点击提交按钮",
        reason="原答案太简洁，需要更详细的步骤",
        user_id="user_001",
        score=4
    )
    print(f"建议已保存: {suggestion.get('saved_path')}")
    
    # 获取该会话的所有反馈
    session_feedback = feedback_handler.get_feedback_by_session(rag.session_id)
    print(f"\n该会话的反馈统计:")
    print(f"  详细反馈数: {len(session_feedback['feedback'])}")
    print(f"  建议数: {len(session_feedback['suggestions'])}")
    
    # 保存会话
    saved_path = rag.save_session()
    print(f"\n会话已保存到: {saved_path}")
    
    return rag, feedback_handler


def example_feedback_statistics():
    """反馈统计示例"""
    print("\n" + "="*60)
    print("示例4: 反馈统计")
    print("="*60)
    
    feedback_handler = FeedbackHandler(
        feedback_dir="/root/workspace/RAGWorkProject/config/feedback",
        suggestions_dir="/root/workspace/RAGWorkProject/config/better_suggestions"
    )
    
    stats = feedback_handler.get_feedback_statistics()
    print(f"\n反馈统计信息:")
    print(f"  详细反馈数: {stats['feedback_count']}")
    print(f"  建议数: {stats['suggestion_count']}")
    print(f"  总计: {stats['total_feedback']}")


def main():
    """主程序"""
    print("\nRAG系统后端使用示例")
    print("="*60)
    
    # 注意：以下示例可能需要实际的UltraRAG环境和配置
    # 如果没有完整的UltraRAG设置，某些示例可能失败
    
    try:
        # 示例0: 流式RAG生成
        example_streaming_rag()

        # 示例0b: 无检索流式多轮对话
        example_streaming_no_retrieval()

        # 示例1: 单轮查询
        example_single_turn_query()
        
        # 示例2: 多轮对话
        example_multi_turn_conversation()
        
        # 示例3: 带反馈的对话
        example_with_feedback()
        
        # 示例4: 反馈统计
        example_feedback_statistics()
        
        print("\n示例运行完成!")
        
    except Exception as e:
        print(f"\n错误: {e}")
        print("提示: 请确保UltraRAG已正确配置并且所有依赖已安装")


if __name__ == "__main__":
    main()
