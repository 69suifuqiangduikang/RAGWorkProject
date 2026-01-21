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
    hier_path: str = ""

def chunk_text(items, chunk_size: int = 600, overlap: int = 120) -> List[ChunkItem]:
    out: List[ChunkItem] = []
    chunk_id = 0

    for it in items:
        s = (getattr(it, "text", "") or "").strip()
        if not s:
            continue

        hier = (getattr(it, "hier_path", "") or "").strip()
        prefix = f"[层级] {hier}\n" if hier else ""

        start = 0
        n = len(s)
        local_idx = 0

        while start < n:
            end = min(n, start + chunk_size)
            chunk = s[start:end].strip()
            if chunk:
                out.append(ChunkItem(
                    doc_name=getattr(it, "doc_name", ""),
                    section=getattr(it, "section", ""),
                    source_id=f"{getattr(it, 'source_id', '')}#c{local_idx}",
                    chunk_id=chunk_id,
                    text=prefix + chunk,
                    hier_path=hier,
                ))
                chunk_id += 1
                local_idx += 1

            if end == n:
                break
            start = max(0, end - overlap)

    return out
