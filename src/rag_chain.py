from __future__ import annotations
from typing import List, Dict, Any
import numpy as np
import re

from .config import TOP_K
from .faiss_store import FaissStore, l2_normalize
from .embed_client import DoubaoEmbedClient
from .llm_client import LLMClient


def _format_context(hits: List[Dict[str, Any]]) -> str:
    # 把检索到的片段拼成上下文，并带来源信息，方便“可解释”
    lines = []
    for i, h in enumerate(hits, start=1):
        src = f"{h.get('doc_name','')} | {h.get('section','')} | {h.get('source_id','')}"
        text = h.get("text", "").strip()
        text = text[:800]
        lines.append(f"【片段{i}】{src}\n{text}")
    return "\n\n".join(lines)


class RAGChain:
    def __init__(self):
        self.store = FaissStore.load()
        self.embed = DoubaoEmbedClient()
        self.llm = LLMClient()

    def retrieve(self, query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
        vec = self.embed.embed([query])  # shape (1, dim)
        vec = l2_normalize(np.array(vec, dtype="float32"))
        scores, idxs = self.store.search(vec, top_k=top_k)

        hits = []
        for s, idx in zip(scores, idxs):
            if idx < 0:
                continue
            m = self.store.meta[idx]
            item = dict(m)
            item["score"] = float(s)
            hits.append(item)
        return hits

    def _keyword_hits(self, query: str, limit: int = 4):
        # 根据问题生成几个简单关键词（你也可以手动写）
        keys = []
        if "登录" in query or "后台" in query:
            keys += ["登录", "后台", "aic.", "IP", "172."]
        # 兜底：从问题里抽2~3个词
        keys += [query.strip()]

        pat = re.compile("|".join([re.escape(k) for k in keys if k]), re.IGNORECASE)

        hits = []
        for m in self.store.meta:
            t = m.get("text", "")
            if t and pat.search(t):
                hits.append(m)
        # 简单去重 & 截断
        # 优先包含网址/IP的
        hits.sort(key=lambda x: (
            ("aic." not in x.get("text", "").lower()),
            ("172." not in x.get("text", "")),
            -len(x.get("text", ""))
        ))
        return hits[:limit]

    def _merge_hits(self, vec_hits, kw_hits, limit: int = 10):
        seen = set()
        merged = []
        for h in vec_hits + kw_hits:
            # 用 chunk_id + doc_name 去重
            key = (h.get("doc_name"), h.get("chunk_id"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(h)
            if len(merged) >= limit:
                break
        return merged

    def answer(self, query: str, top_k: int = TOP_K) -> str:
        vec_hits = self.retrieve(query, top_k=top_k)
        kw_hits = self._keyword_hits(query, limit=4)
        hits = self._merge_hits(vec_hits, kw_hits, limit=max(top_k, 10))

        # print("\n==== RETRIEVAL TOPK ====")
        # for i, h in enumerate(hits, 1):
        #     print(i, "score=", round(h.get("score", 0.0), 4),
        #           "doc=", h.get("doc_name"),
        #           "section=", h.get("section"),
        #           "chunk_id=", h.get("chunk_id"))
        #     print(h.get("text", "")[:120].replace("\n", " "))
        # print("==== END TOPK ====\n")

        context = _format_context(hits)

        system = (
            "你是 AIC 平台智能答疑助手。"
            "你必须严格依据【资料片段】作答，禁止编造。"
            "当资料片段包含可执行信息时，你必须把信息改写成具体步骤/操作指引。"
            "禁止只回答“去看手册/FAQ/联系支持”这种泛化回复（除非资料片段确实没有给出任何操作细节）。"
            "回答必须清晰、步骤化、可操作。"
        )

        user = (
            f"用户问题：{query}\n\n"
            f"资料片段（可能相关）：\n{context}\n\n"
            "请按以下格式输出：\n"
            "A. 具体操作步骤（必须写出，至少3条；若资料片段提供了按钮/入口/路径/字段名，请逐条写明）\n"
            "B. 关键依据（从资料片段中摘取1~3条要点，用自己的话转述，不要只说“见[3]”）\n"
            "C. 引用编号（如[1][3]）\n"
            "注意：如果资料片段没有提供任何具体步骤，才允许回答“资料中未找到具体操作步骤”，并说明你缺少哪类信息。"
        )

        return self.llm.chat(system=system, user=user)
