from __future__ import annotations
from tqdm import tqdm
import numpy as np

from .config import DATA_DIR, CHUNK_SIZE, OVERLAP, BATCH
from .docx_loader import load_docx_items
from .pdf_loader import load_pdf
from .chunker import chunk_text
from .embed_client import DoubaoEmbedClient
from .faiss_store import FaissStore, l2_normalize


def main():
    items = []

    # docx
    for p in DATA_DIR.glob("*.docx"):
        items.extend(load_docx_items(p))

    # pdf
    for p in DATA_DIR.glob("*.pdf"):
        items.extend(load_pdf(p))

    if not items:
        raise RuntimeError(f"No docx/pdf found in {DATA_DIR}")

    chunks = chunk_text(items, chunk_size=CHUNK_SIZE, overlap=OVERLAP)
    if not chunks:
        raise RuntimeError("No chunks produced.")

    embed = DoubaoEmbedClient()
    texts = [c.text for c in chunks]

    vecs = []
    for i in tqdm(range(0, len(texts), BATCH), desc="Embedding"):
        vecs.append(embed.embed(texts[i:i + BATCH]))

    vectors = l2_normalize(np.vstack(vecs))

    meta = []
    for c in chunks:
        meta.append({
            "doc_name": c.doc_name,
            "section": c.section,
            "source_id": c.source_id,
            "chunk_id": c.chunk_id,
            "text": c.text,
        })

    store = FaissStore()
    store.build(vectors, meta)
    store.save()
    print("✅ Knowledge base built and saved.")


if __name__ == "__main__":
    main()
