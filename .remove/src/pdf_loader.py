from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List
from pypdf import PdfReader

@dataclass
class DocItem:
    text: str
    doc_name: str
    section: str
    source_id: str
    is_heading: bool = False
    heading_level: int = 0
    heading_text: str = ""
    hier_path: str = ""

def load_pdf(path: str | Path) -> List[DocItem]:
    path = Path(path)
    reader = PdfReader(str(path))

    out: List[DocItem] = []
    for i, page in enumerate(reader.pages, start=1):
        txt = (page.extract_text() or "").strip()
        if not txt:
            continue

        # 先把每页当作一个“章节块”，hier_path = Page i
        out.append(DocItem(
            text=txt,
            doc_name=path.name,
            section=f"page_{i}",
            source_id=f"{path.name}#p{i}",
            is_heading=False,
            hier_path=f"Page {i}",
        ))
    return out
