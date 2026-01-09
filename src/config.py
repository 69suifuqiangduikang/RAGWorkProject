from __future__ import annotations
import os
from pathlib import Path

# ====== 项目根目录（src 的上一级）======
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ====== 数据与KB路径 ======
DATA_DIR = PROJECT_ROOT / "data"
KB_DIR = PROJECT_ROOT / "kb"
INDEX_PATH = KB_DIR / "faiss.index"
META_PATH = KB_DIR / "meta.jsonl"

# ====== RAG参数 ======
TOP_K = int(os.getenv("TOP_K", "6"))
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.0"))  # 先别卡阈值，跑通后再调

# ====== 豆包 Ark OpenAI 兼容接口（聊天）=====
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
ARK_API_KEY = os.getenv("ARK_API_KEY", "").strip()
DOUBAO_CHAT_MODEL = os.getenv("DOUBAO_CHAT_MODEL", "doubao-seed-1-8-251228")

# ====== 豆包 embedding（多模态/文本都可）=====
DOUBAO_EMBED_MODEL = os.getenv("DOUBAO_EMBED_MODEL", "doubao-embedding-vision-250615")

# ====== 分块参数 ======
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
OVERLAP = int(os.getenv("OVERLAP", "120"))
BATCH = int(os.getenv("EMBED_BATCH", "32"))
