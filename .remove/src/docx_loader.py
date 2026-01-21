from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import re
from docx import Document

# 通用标题识别：1. / 1.1 / 一、 / （1） / 第X章 等
HEADING_RE = re.compile(
    r"^\s*(("
    r"\d+(\.\d+){0,4}[\.、]?"          # 1 / 1.1 / 1.1.1
    r"|[一二三四五六七八九十]+、"        # 一、二、
    r"|[（(]\d+[）)]"                  # （1）
    r"|第[一二三四五六七八九十\d]+[章节篇]"  # 第1章
    r"))\s*(.+)\s*$"
)

def guess_level(prefix: str) -> int:
    # 1 / 1.1 / 1.1.1 => level = 点的个数+1
    if re.match(r"^\d+(\.\d+)+", prefix):
        return prefix.count(".") + 1
    # 一、 或 第X章 之类：粗略当 level=1
    return 1

@dataclass
class DocItem:
    text: str
    doc_name: str
    section: str
    source_id: str
    is_heading: bool = False
    heading_level: int = 0
    heading_text: str = ""
    hier_path: str = ""  # 例如：1 登录AIC后台 > 1.1 ...

def load_docx_items(path: str | Path) -> List[DocItem]:
    path = Path(path)
    doc = Document(str(path))

    out: List[DocItem] = []
    sec = "body"
    para_id = 0

    # 用栈维护层级路径
    stack: List[str] = []

    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if not t:
            continue
        para_id += 1

        m = HEADING_RE.match(t)
        if m:
            prefix = m.group(1)
            title = m.group(6) if m.lastindex and m.lastindex >= 6 else t
            lvl = guess_level(prefix)

            # 调整栈到对应层级
            while len(stack) >= lvl:
                stack.pop()
            stack.append(t)

            hier = " > ".join(stack)

            out.append(DocItem(
                text=t,
                doc_name=path.name,
                section=sec,
                source_id=f"{path.name}#para{para_id}",
                is_heading=True,
                heading_level=lvl,
                heading_text=t,
                hier_path=hier,
            ))
        else:
            hier = " > ".join(stack) if stack else ""
            out.append(DocItem(
                text=t,
                doc_name=path.name,
                section=sec,
                source_id=f"{path.name}#para{para_id}",
                is_heading=False,
                heading_level=0,
                heading_text="",
                hier_path=hier,
            ))

    return out
