#!/usr/bin/env python
"""
RAG API 简化测试（仅测试RAG检索模式）

此脚本仅测试使用UltraRAG Pipeline的RAG检索模式，
不需要配置OpenAI API Key
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"


def test_rag_only():
    """测试仅使用RAG检索的功能"""
    print("\n" + "="*60)
    print("RAG检索模式测试（不需要OpenAI配置）")
    print("="*60)
    
    # 检查服务
    print("\n🔍 检查服务...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ 服务可用")
    except Exception as e:
        print(f"❌ 服务不可用: {e}")
        print("💡 请先启动服务: python run_api.py")
        return
    
    # 初始化会话
    print("\n📝 初始化会话...")
    response = requests.post(f"{BASE_URL}/api/sessions/init")
    session_id = response.json()['session_id']
    print(f"✅ 会话创建: {session_id[:12]}...")
    
    # 发送RAG查询
    print("\n📤 发送RAG查询: 如何提交python训练程序？")
    message = {
        "content": "如何提交我写好的python训练程序？",
        "use_retrieval": True,
        "top_k": 5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat?session_id={session_id}",
            json=message,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 查询成功")
            print(f"   轮次: {result['turn_id']}")
            print(f"   状态: {result['status']}")
            
            answer = result.get('answer', '')
            if answer:
                preview = answer[:150] + "..." if len(answer) > 150 else answer
                print(f"   答案预览: {preview}")
            else:
                print("   ⚠️ 答案为空")
            
            # 点赞反馈
            print("\n👍 提交点赞反馈...")
            like_response = requests.post(
                f"{BASE_URL}/api/feedback/like",
                params={
                    "session_id": session_id,
                    "turn_id": 0,
                    "reason": "测试反馈",
                    "user_id": "test_user"
                }
            )
            if like_response.status_code == 200:
                print(f"✅ 点赞成功")
            
            # 获取会话信息
            print("\n📋 获取会话信息...")
            info_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
            if info_response.status_code == 200:
                info = info_response.json()
                print(f"   总轮数: {info['total_turns']}")
                print(f"   持续时间: {info['duration_seconds']:.2f}秒")
            
            # 保存会话
            print("\n💾 保存会话...")
            save_response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/save")
            if save_response.status_code == 200:
                save_data = save_response.json()
                print(f"✅ 保存成功: {save_data['saved_path']}")
            
            print("\n" + "="*60)
            print("✅ RAG检索模式测试完成！")
            print("="*60)
            
        else:
            print(f"❌ 查询失败 (状态码: {response.status_code})")
            print(f"   详情: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        print("💡 RAG Pipeline可能正在处理，请等待...")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        print("💡 请确保UltraRAG Pipeline正常运行")


def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║      RAG API 简化测试                                  ║
    ╠════════════════════════════════════════════════════════╣
    ║  仅测试RAG检索模式，不需要OpenAI配置                    ║
    ║                                                        ║
    ║  请先启动API服务:                                       ║
    ║  python run_api.py                                    ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    test_rag_only()
    
    print("\n💡 说明:")
    print("- 此测试仅使用RAG检索模式（UltraRAG Pipeline）")
    print("- 不需要配置OpenAI API Key")
    print("- 如需测试流式对话，请配置 config/backend.yaml")
    print("- 完整测试请运行: python test_api_client.py")


if __name__ == "__main__":
    main()
