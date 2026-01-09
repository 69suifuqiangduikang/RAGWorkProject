from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List

from docx import Document

@dataclass
class DocItem:
    text: str
    doc_name: str
    section: str
    source_id: str

def load_docx_items(path: str | Path) -> List[DocItem]:
    path = Path(path)
    doc = Document(str(path))

    out: List[DocItem] = []
    sec = "body"
    para_id = 0
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if not t:
            continue
        para_id += 1
        out.append(
            DocItem(
                text=t,
                doc_name=path.name,
                section=sec,
                source_id=f"{path.name}#para{para_id}",
            )
        )
    return out
