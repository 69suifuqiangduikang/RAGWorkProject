from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class ChunkItem:
    doc_name: str
    section: str
    source_id: str
    chunk_id: int
    text: str

def chunk_text(items, chunk_size: int = 600, overlap: int = 120) -> List[ChunkItem]:
    out: List[ChunkItem] = []
    chunk_id = 0

    for it in items:
        s = (it.text or "").strip()
        if not s:
            continue

        # 简单滑窗切分
        start = 0
        n = len(s)
        while start < n:
            end = min(n, start + chunk_size)
            chunk = s[start:end].strip()
            if chunk:
                out.append(ChunkItem(it.doc_name, it.section, it.source_id, chunk_id, chunk))
                chunk_id += 1
            if end == n:
                break
            start = max(0, end - overlap)

    return out
