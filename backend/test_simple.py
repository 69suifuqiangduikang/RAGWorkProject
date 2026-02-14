#!/usr/bin/env python
"""
简化的API测试 - 单个3轮对话测试

测试场景：
- 第1轮：使用RAG检索模式
- 第2轮：使用无检索对话模式
- 第3轮：使用RAG检索模式
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000"


def test_three_turn_conversation():
    """测试3轮对话（混合使用检索和无检索模式）"""
    print("\n" + "="*70)
    print("3轮对话测试（第1、3轮用检索，第2轮不用）")
    print("="*70)
    
    # 检查服务
    print("\n🔍 检查服务状态...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ 服务可用 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 服务不可用: {e}")
        print("💡 请先启动服务: python run_api.py")
        return
    
    # 初始化会话
    print("\n📝 初始化新会话...")
    response = requests.post(f"{BASE_URL}/api/sessions/init")
    if response.status_code != 200:
        print(f"❌ 初始化失败: {response.text}")
        return
    
    session_id = response.json()['session_id']
    print(f"✅ 会话创建成功")
    print(f"   会话ID: {session_id[:16]}...")
    
    # ==================== 第1轮：RAG检索模式 ====================
    print("\n" + "-"*70)
    print("第1轮对话 - RAG检索模式")
    print("-"*70)
    print("📤 用户: 如何提交我写好的python训练程序？")
    
    message1 = {
        "content": "如何提交我写好的python训练程序？",
        "use_retrieval": True,
        "top_k": 5
    }
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/chat?session_id={session_id}",
        json=message1,
        timeout=60
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"📥 助手回答 (耗时: {elapsed:.2f}秒, 状态: {result['status']}):")
        answer = result.get('answer', '')
        if answer:
            preview = answer[:200] + "..." if len(answer) > 200 else answer
            print(f"   {preview}")
        else:
            print("   ⚠️ 答案为空")
        
        if result.get('retrieved_docs'):
            print(f"   📚 检索到 {len(result['retrieved_docs'])} 个相关文档")
    else:
        print(f"❌ 请求失败 (状态码: {response.status_code})")
        print(f"   详情: {response.text[:300]}")
        return
    
    # ==================== 第2轮：无检索模式 ====================
    print("\n" + "-"*70)
    print("第2轮对话 - 无检索模式")
    print("-"*70)
    print("📤 用户: 再详细解释一下第一步")
    
    message2 = {
        "content": "再详细解释一下第一步",
        "use_retrieval": False
    }
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/chat?session_id={session_id}",
        json=message2,
        timeout=60
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"📥 助手回答 (耗时: {elapsed:.2f}秒, 状态: {result['status']}):")
        answer = result.get('answer', '')
        if answer:
            preview = answer[:200] + "..." if len(answer) > 200 else answer
            print(f"   {preview}")
        else:
            print("   ⚠️ 答案为空")
    else:
        print(f"❌ 请求失败 (状态码: {response.status_code})")
        print(f"   详情: {response.text[:300]}")
        return
    
    # ==================== 第3轮：RAG检索模式 ====================
    print("\n" + "-"*70)
    print("第3轮对话 - RAG检索模式")
    print("-"*70)
    print("📤 用户: 提交任务后如何查看日志？")
    
    message3 = {
        "content": "提交任务后如何查看日志？",
        "use_retrieval": True,
        "top_k": 3
    }
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/chat?session_id={session_id}",
        json=message3,
        timeout=60
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"📥 助手回答 (耗时: {elapsed:.2f}秒, 状态: {result['status']}):")
        answer = result.get('answer', '')
        if answer:
            preview = answer[:200] + "..." if len(answer) > 200 else answer
            print(f"   {preview}")
        else:
            print("   ⚠️ 答案为空")
        
        if result.get('retrieved_docs'):
            print(f"   📚 检索到 {len(result['retrieved_docs'])} 个相关文档")
    else:
        print(f"❌ 请求失败 (状态码: {response.status_code})")
        print(f"   详情: {response.text[:300]}")
        return
    
    # ==================== 查看会话信息 ====================
    print("\n" + "-"*70)
    print("会话总结")
    print("-"*70)
    
    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
    if response.status_code == 200:
        info = response.json()
        print(f"   📊 总轮数: {info['total_turns']}")
        print(f"   ⏱️  持续时间: {info['duration_seconds']:.2f}秒")
        print(f"   📅 开始时间: {info['start_time']}")
    
    # ==================== 保存会话 ====================
    print("\n💾 保存会话...")
    response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/save")
    if response.status_code == 200:
        save_data = response.json()
        print(f"✅ 会话已保存到: {save_data['saved_path']}")
    
    print("\n" + "="*70)
    print("✅ 3轮对话测试完成！")
    print("="*70)
    
    print("\n📝 总结:")
    print("- 第1轮：RAG检索模式 - 查询'如何提交python训练程序'")
    print("- 第2轮：无检索模式 - 追问'再详细解释一下第一步'")
    print("- 第3轮：RAG检索模式 - 查询'如何查看日志'")
    print("- 所有对话都在同一个会话中，每个用户的会话是独立的")
    print("- RAG Pipeline在所有用户间共享（全局单例）")


def main():
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║      RAG API 简化测试                                  ║
    ╠═══════════════════════════════════════════════════════╣
    ║  测试场景: 单个3轮对话                                 ║
    ║  - 第1轮: RAG检索模式                                 ║
    ║  - 第2轮: 无检索模式                                  ║
    ║  - 第3轮: RAG检索模式                                 ║
    ║                                                       ║
    ║  请先启动API服务:                                      ║
    ║  python run_api.py                                   ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    test_three_turn_conversation()


if __name__ == "__main__":
    main()
