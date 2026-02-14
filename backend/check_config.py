#!/usr/bin/env python
"""
检查 RAG Backend 配置

帮助诊断配置问题
"""

import os
import sys
from pathlib import Path

def check_config():
    """检查配置文件"""
    print("="*60)
    print("RAG Backend 配置检查")
    print("="*60)
    
    config_path = Path("/root/workspace/RAGWorkProject/config/backend.yaml")
    
    print(f"\n1. 检查配置文件: {config_path}")
    if not config_path.exists():
        print("   ❌ 配置文件不存在")
        print(f"   💡 请创建配置文件: {config_path}")
        return False
    else:
        print("   ✅ 配置文件存在")
    
    # 读取配置
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print("   ✅ 配置文件格式正确")
    except Exception as e:
        print(f"   ❌ 配置文件格式错误: {e}")
        return False
    
    # 检查 RAG 配置
    print("\n2. 检查 RAG 模式配置")
    if 'rag' not in config:
        print("   ❌ 缺少 'rag' 配置")
        return False
    
    rag_config = config['rag']
    model = rag_config.get('model', '')
    base_url = rag_config.get('base_url', '')
    api_key = rag_config.get('api_key', '')
    
    print(f"   模型: {model or '(未设置)'}")
    print(f"   Base URL: {base_url or '(未设置)'}")
    
    if api_key:
        if api_key.startswith('ENV:'):
            env_var = api_key.split(':', 1)[1]
            actual_key = os.environ.get(env_var)
            if actual_key:
                print(f"   API Key: 环境变量 {env_var} (已设置)")
            else:
                print(f"   ❌ API Key: 环境变量 {env_var} 未设置")
                print(f"   💡 请设置环境变量: export {env_var}=your-key")
        else:
            # 显示部分key
            masked = api_key[:10] + "..." + api_key[-8:] if len(api_key) > 20 else api_key
            print(f"   API Key: {masked}")
    else:
        print("   ❌ API Key 未配置")
        return False
    
    # 检查 no_retrieval 配置
    print("\n3. 检查无检索模式配置")
    if 'no_retrieval' not in config:
        print("   ❌ 缺少 'no_retrieval' 配置")
        return False
    
    no_ret_config = config['no_retrieval']
    model = no_ret_config.get('model', '')
    base_url = no_ret_config.get('base_url', '')
    api_key = no_ret_config.get('api_key', '')
    
    print(f"   模型: {model or '(未设置)'}")
    print(f"   Base URL: {base_url or '(未设置)'}")
    
    if api_key:
        if api_key.startswith('ENV:'):
            env_var = api_key.split(':', 1)[1]
            actual_key = os.environ.get(env_var)
            if actual_key:
                print(f"   API Key: 环境变量 {env_var} (已设置)")
            else:
                print(f"   ❌ API Key: 环境变量 {env_var} 未设置")
        else:
            masked = api_key[:10] + "..." + api_key[-8:] if len(api_key) > 20 else api_key
            print(f"   API Key: {masked}")
    else:
        print("   ❌ API Key 未配置")
        return False
    
    # 测试 API 连接
    print("\n4. 测试 API 连接")
    try:
        from openai import OpenAI
        
        # 测试 no_retrieval 配置
        actual_key = api_key
        if api_key.startswith('ENV:'):
            env_var = api_key.split(':', 1)[1]
            actual_key = os.environ.get(env_var)
        
        if not actual_key:
            print("   ⚠️ 跳过连接测试（API Key未设置）")
        else:
            client = OpenAI(
                base_url=base_url or None,
                api_key=actual_key
            )
            print("   ✅ OpenAI 客户端创建成功")
            
            # 尝试简单调用
            print("   🔄 测试简单调用...")
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "hi"}],
                    max_tokens=5
                )
                print("   ✅ API 调用成功")
            except Exception as e:
                print(f"   ❌ API 调用失败: {e}")
                print("   💡 请检查 API Key 和模型名称是否正确")
                return False
            
    except ImportError:
        print("   ⚠️ openai 包未安装，跳过连接测试")
        print("   💡 安装: pip install openai")
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ 配置检查完成！")
    print("="*60)
    return True


if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1)
