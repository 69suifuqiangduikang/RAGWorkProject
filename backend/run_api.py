#!/usr/bin/env python
"""
RAG系统API启动脚本
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 检查依赖
try:
    import fastapi
    import uvicorn
except ImportError as e:
    print(f"错误: 缺少依赖 {e}")
    print("请运行: pip install fastapi uvicorn")
    sys.exit(1)

# 导入FastAPI应用
from api import app

def main():
    """启动FastAPI服务器"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║         RAG多轮对话 API服务启动                         ║
    ╠═══════════════════════════════════════════════════════╣
    ║  API文档:        http://127.0.0.1:8000/docs         ║
    ║  交互式文档:      http://127.0.0.1:8000/redoc        ║
    ║  健康检查:       http://127.0.0.1:8000/health       ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # 生产环境关闭自动重载
    )

if __name__ == "__main__":
    main()
