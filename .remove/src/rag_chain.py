from __future__ import annotations
from typing import List, Dict, Any, Tuple
import numpy as np
import math
import re
from collections import Counter, defaultdict

from .config import TOP_K
from .faiss_store import FaissStore, l2_normalize
from .embed_client import DoubaoEmbedClient
from .llm_client import LLMClient


def _hit_key(h: Dict[str, Any]) -> Tuple[str, str, int]:
    return (h.get("doc_name", ""), h.get("source_id", ""), int(h.get("chunk_id", -1)))


def _group_key(h: Dict[str, Any]) -> Tuple[str, str]:
    """
    用“从属关系”聚合：优先 hier_path，其次 section。
    """
    doc = h.get("doc_name", "")
    hier = (h.get("hier_path") or "").strip()
    sec = (h.get("section") or "").strip()
    return (doc, hier if hier else sec)


def _format_context_grouped(hits: List[Dict[str, Any]]) -> str:
    """
    把聚合后的 hits 组织成“章节块”，比一堆散片段更容易让模型抽步骤。
    """
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    order: List[Tuple[str, str]] = []
    for h in hits:
        gk = _group_key(h)
        if gk not in groups:
            groups[gk] = []
            order.append(gk)
        groups[gk].append(h)

    lines = []
    frag_id = 1
    for (doc, scope) in order:
        header = f"=== 文档: {doc} | 范围: {scope or 'UNKNOWN'} ==="
        lines.append(header)
        for h in groups[(doc, scope)]:
            src = f"{h.get('doc_name','')} | {h.get('section','')} | {h.get('source_id','')}"
            text = (h.get("text") or "").strip()
            # 片段截断别太短也别太长，作业级即可
            text = text[:1200]
            lines.append(f"【片段{frag_id}】{src}\n{text}")
            frag_id += 1
        lines.append("")  # 空行分隔组

    return "\n".join(lines).strip()


def _tokenize(text: str):
    """
    作业级通用分词：
    - 英文/数字：按词
    - 中文：按单字
    """
    text = (text or "").lower()
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text)


class BM25:
    def __init__(self, docs_tokens, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs = docs_tokens
        self.N = len(docs_tokens)

        self.df = defaultdict(int)
        self.tf = []
        self.dl = []
        total_len = 0

        for toks in docs_tokens:
            c = Counter(toks)
            self.tf.append(c)
            self.dl.append(len(toks))
            total_len += len(toks)
            for t in c.keys():
                self.df[t] += 1

        self.avgdl = total_len / max(1, self.N)

    def score(self, query_tokens, idx: int):
        tf = self.tf[idx]
        dl = self.dl[idx]
        score = 0.0
        for t in query_tokens:
            df = self.df.get(t, 0)
            if df == 0:
                continue
            idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))
            f = tf.get(t, 0)
            if f == 0:
                continue
            denom = f + self.k1 * (1 - self.b + self.b * dl / max(1e-9, self.avgdl))
            score += idf * (f * (self.k1 + 1)) / denom
        return score

    def topk(self, query: str, k: int = 20):
        qtok = _tokenize(query)
        scored = [(self.score(qtok, i), i) for i in range(self.N)]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]



class RAGChain:
    def __init__(self):
        self.store = FaissStore.load()
        self.embed = DoubaoEmbedClient()
        self.llm = LLMClient()

        self._bm25_docs = [_tokenize(m.get("text", "")) for m in self.store.meta]
        self.bm25 = BM25(self._bm25_docs)

    def retrieve(self, query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
        vec = self.embed.embed([query])  # (1, dim)
        vec = l2_normalize(np.array(vec, dtype="float32"))

        # ⚠️ 关键：初筛召回要更大一些，不然容易漏掉“真正答案所在章节”
        # 你外面传 top_k=6 之类也没关系，这里先多召回再聚合。
        raw_k = max(top_k * 6, 30)

        scores, idxs = self.store.search(vec, top_k=raw_k)

        hits: List[Dict[str, Any]] = []
        for s, idx in zip(scores, idxs):
            if idx < 0:
                continue
            m = self.store.meta[idx]
            item = dict(m)
            item["score"] = float(s)
            hits.append(item)

        # 按相似度降序（Faiss 有时返回已是降序，但我们显式保证）
        hits.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        print("EMBED_MODEL =", getattr(self.embed, "model", None))
        return hits

    def pack_by_section(
        self,
        hits: List[Dict[str, Any]],
        max_groups: int = 4,
        max_per_group: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        通用“章节打包”：
        - 先按相似度高的 hit 确定哪些章节最可能相关
        - 每个章节取前 max_per_group 个片段
        """
        groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        group_order: List[Tuple[str, str]] = []

        for h in hits:
            gk = _group_key(h)
            if gk not in groups:
                groups[gk] = []
                group_order.append(gk)
            groups[gk].append(h)

        # 组内按 score 排序
        for gk in groups:
            groups[gk].sort(key=lambda x: x.get("score", 0.0), reverse=True)

        packed: List[Dict[str, Any]] = []
        seen = set()

        for gk in group_order[:max_groups]:
            for h in groups[gk][:max_per_group]:
                k = _hit_key(h)
                if k in seen:
                    continue
                seen.add(k)
                packed.append(h)

        return packed

    def lexical_retrieve(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        scored = self.bm25.topk(query, k=top_k)
        hits = []
        for s, idx in scored:
            if s <= 0:
                continue
            m = self.store.meta[idx]
            item = dict(m)
            item["bm25"] = float(s)
            item.setdefault("score", 0.0)  # 兼容打印
            hits.append(item)
        return hits

    def answer(self, query: str, top_k: int = TOP_K) -> str:
        # # 1) 向量召回（多召回）
        # hits = self.retrieve(query, top_k=top_k)
        #
        # # 2) 按从属关系（hier_path/section）打包成少量章节块
        # packed = self.pack_by_section(
        #     hits,
        #     max_groups=4,       # 你可以调 3~6
        #     max_per_group=4,    # 每个章节给 3~6 段一般就够
        # )

        vec_hits = self.retrieve(query, top_k=top_k)
        bm_hits = self.lexical_retrieve(query, top_k=40)

        # 合并去重：BM25 优先（保证“原文命中”不丢）
        seen = set()
        merged = []
        for h in bm_hits + vec_hits:
            key = (h.get("doc_name"), h.get("source_id"), h.get("chunk_id"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(h)
            if len(merged) >= max(top_k, 12):
                break

        hits = merged   # 先别 pack，先确认召回能把 Harbor 段落拉进来


        # 3) 调试打印（确认聚合是否生效）
        print("\n==== RETRIEVAL TOPK (HYBRID) ====")
        for i, h in enumerate(hits, 1):
            print(i,
                  "vec=", round(h.get("score", 0.0), 4),
                  "bm25=", round(h.get("bm25", 0.0), 4),
                  "doc=", h.get("doc_name"),
                  "section=", h.get("section"),
                  "chunk_id=", h.get("chunk_id"))
            print((h.get("text") or "")[:120].replace("\n", " "))
        print("==== END TOPK ====\n")

        context = _format_context_grouped(hits)

        # 4) Prompt 改成“软约束”：鼓励步骤化，但不“卡死严格依据到不敢说”
        system = (
            "你是 AIC 平台智能答疑助手。"
            "请优先依据【资料片段】回答。"
            "如果片段中包含明确步骤/入口/字段/命令，请整理为可执行的步骤。"
            "如果片段信息不完整，请说明缺失点，并给出你基于片段能确定的部分。"
        )

        user = (
            f"用户问题：{query}\n\n"
            f"资料片段（按章节聚合，可能相关）：\n{context}\n\n"
            "请输出：\n"
            "A. 具体操作步骤（尽量步骤化；如果片段里有网址/IP/入口路径/按钮名/命令，请写出来）\n"
            "B. 依据（引用你用到的片段编号，如[片段2][片段3]，并用自己的话概括依据点）\n"
        )

        return self.llm.chat(system=system, user=user)
