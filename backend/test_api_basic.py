#!/usr/bin/env python
"""
快速测试API（不调用真实的RAG）
"""

from api import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("="*60)
print("API 快速测试（模拟场景）")
print("="*60)

# 1. 健康检查
print("\n✅ 测试1: 健康检查")
response = client.get('/health')
assert response.status_code == 200
print(f"   状态: {response.json()['status']}")

# 2. 初始化会话
print("\n✅ 测试2: 初始化会话")
response = client.post('/api/sessions/init')
assert response.status_code == 200
session_id = response.json()['session_id']
print(f"   Session ID: {session_id[:12]}...")

# 3. 获取空会话信息
print("\n✅ 测试3: 获取空会话信息")
response = client.get(f'/api/sessions/{session_id}')
assert response.status_code == 200
data = response.json()
print(f"   总轮数: {data['total_turns']}")
print(f"   对话历史长度: {len(data['conversation_history'])}")

# 4. 测试错误处理：对不存在的轮次点赞
print("\n✅ 测试4: 点赞不存在的轮次（预期404）")
response = client.post(
    f'/api/feedback/like?session_id={session_id}&turn_id=0&reason=测试'
)
assert response.status_code == 404
print(f"   状态码: {response.status_code} (符合预期)")

# 5. 测试错误处理：不存在的会话
print("\n✅ 测试5: 访问不存在的会话（预期404）")
response = client.get('/api/sessions/fake-session-id')
assert response.status_code == 404
print(f"   状态码: {response.status_code} (符合预期)")

# 6. 保存会话
print("\n✅ 测试6: 保存会话")
response = client.post(f'/api/sessions/{session_id}/save')
assert response.status_code == 200
print(f"   保存路径: {response.json()['saved_path']}")

print("\n" + "="*60)
print("✅ 所有API基础测试通过！")
print("="*60)
print("\n说明：")
print("- 这些测试不涉及真实的RAG调用")
print("- 如需测试完整的RAG功能，请：")
print("  1. 确保config/backend.yaml配置正确")
print("  2. 启动API: python run_api.py")
print("  3. 运行: python test_api_client.py")
print("="*60)
