from __future__ import annotations
import json
import os
from typing import List, Dict, Any

import faiss
import numpy as np

from .config import KB_DIR, INDEX_PATH, META_PATH

def l2_normalize(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norms

class FaissStore:
    def __init__(self):
        self.index = None
        self.meta: List[Dict[str, Any]] = []

    def build(self, vectors: np.ndarray, meta: List[Dict[str, Any]]):
        dim = vectors.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # 余弦相似度（配合l2_normalize）
        self.index.add(vectors.astype("float32"))
        self.meta = meta

    def save(self):
        os.makedirs(str(KB_DIR), exist_ok=True)
        faiss.write_index(self.index, str(INDEX_PATH))
        with open(str(META_PATH), "w", encoding="utf-8") as f:
            for row in self.meta:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    @classmethod
    def load(cls):
        inst = cls()
        inst.index = faiss.read_index(str(INDEX_PATH))
        meta = []
        with open(str(META_PATH), "r", encoding="utf-8") as f:
            for line in f:
                meta.append(json.loads(line))
        inst.meta = meta
        return inst

    def search(self, query_vec: np.ndarray, top_k: int = 6):
        q = query_vec.astype("float32")
        D, I = self.index.search(q, top_k)
        return D[0].tolist(), I[0].tolist()
