from __future__ import annotations

import os
from typing import List, Optional, Union, Dict, Any

import numpy as np

try:
    from volcenginesdkarkruntime import Ark
except Exception as e:  # pragma: no cover
    raise ImportError(
        "Missing dependency: volcenginesdkarkruntime\n"
        "Install with:\n"
        "  pip install volcenginesdkarkruntime\n"
        "or\n"
        "  uv pip install volcenginesdkarkruntime\n"
    ) from e


class DoubaoEmbedClient:
    """
    豆包（Ark Runtime SDK）Embedding 客户端

    默认用于文本 RAG：embed(texts) -> np.ndarray [n, dim]
    也支持多模态（可选）：embed_multimodal([...]) -> np.ndarray [n, dim]

    环境变量：
      ARK_API_KEY=...
      DOUBAO_EMBED_MODEL=doubao-embedding-vision-250615  (你截图的模型)
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ARK_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("Please set ARK_API_KEY env var.")
        self.model = model or os.environ.get("DOUBAO_EMBED_MODEL", "doubao-embedding-vision-250615")
        self.client = Ark(api_key=self.api_key)

    def embed(self, texts: List[str]) -> np.ndarray:
        """
        纯文本 embedding（用于你的 RAG 建库/检索）
        """
        if not texts:
            return np.zeros((0, 1), dtype="float32")

        # Ark 的 multimodal embeddings 也支持纯 text 输入
        inputs = [{"type": "text", "text": t} for t in texts]

        resp = self.client.multimodal_embeddings.create(
            model=self.model,
            input=inputs,
        )

        vecs = self._extract_vectors(resp)
        arr = np.array(vecs, dtype="float32")
        return arr

    def embed_multimodal(self, items: List[List[Dict[str, Any]]]) -> np.ndarray:
        """
        多模态 embedding：每个 item 是一个 list，包含若干块，比如 text + image_url
        示例：
          [
            [{"type":"text","text":"..."},{"type":"image_url","image_url":{"url":"..."}}],
            [{"type":"text","text":"..."}]
          ]
        注意：你的作业先不用这个；这是给你后面把图片入库留的接口。
        """
        if not items:
            return np.zeros((0, 1), dtype="float32")

        # Ark 接口的 input 通常接受一个“多块列表”（你示例里就是两个块）。
        # 这里我们做一个批处理：逐条请求，稳定优先。
        vecs_all = []
        for blocks in items:
            resp = self.client.multimodal_embeddings.create(model=self.model, input=blocks)
            vecs = self._extract_vectors(resp)
            if len(vecs) != 1:
                raise ValueError("Expected one vector per multimodal_embeddings request.")
            vecs_all.append(vecs[0])

        return np.array(vecs_all, dtype="float32")

    @staticmethod
    def _extract_vectors(resp):
        """
        兼容 Ark SDK 的 embeddings 返回结构：
        - resp.data 可能是 list[Item]，Item.embedding
        - resp.data 可能是 dict，data["embedding"]
        - resp.data 可能是 Item 对象，data.embedding
        - resp 可能支持 model_dump()
        """
        # 1) 先尽量把 resp 变成 dict（pydantic / sdk对象）
        d = None
        if isinstance(resp, dict):
            d = resp
        elif hasattr(resp, "model_dump"):
            d = resp.model_dump()
        elif hasattr(resp, "dict"):
            # 某些 pydantic 版本
            d = resp.dict()
        else:
            d = None

        # 2) 先走“属性风格”（OpenAI/Ark SDK 常见）
        if hasattr(resp, "data"):
            data = resp.data

            # 2.1 data 是 list
            if isinstance(data, list) and data:
                first = data[0]
                if hasattr(first, "embedding"):
                    return [item.embedding for item in data]
                if isinstance(first, dict) and "embedding" in first:
                    return [item["embedding"] for item in data]

            # 2.2 data 是单个对象/单个dict（不是 list）
            if hasattr(data, "embedding"):
                return [data.embedding]
            if isinstance(data, dict) and "embedding" in data:
                return [data["embedding"]]

        # 3) 再走 dict 风格（你现在就是这里写死了 list 才炸）
        if isinstance(d, dict):
            # 常见结构A：{"data":[{"embedding":[...]}]}
            if "data" in d:
                data = d["data"]
                if isinstance(data, list) and data and isinstance(data[0], dict) and "embedding" in data[0]:
                    return [x["embedding"] for x in data]
                # 常见结构B：{"data":{"embedding":[...]}}
                if isinstance(data, dict) and "embedding" in data:
                    return [data["embedding"]]

            # 常见结构C：{"embeddings":[[...],[...]]}
            if "embeddings" in d and isinstance(d["embeddings"], list) and d["embeddings"]:
                return d["embeddings"]

            # 常见结构D：{"embedding":[...]}
            if "embedding" in d and isinstance(d["embedding"], list) and d["embedding"]:
                # 单条向量
                return [d["embedding"]]

        # 4) 实在不行，抛出可读错误（带返回片段）
        preview = None
        try:
            preview = d
        except Exception:
            preview = str(resp)
        raise ValueError(f"Cannot parse embedding response. Preview: {preview}")
