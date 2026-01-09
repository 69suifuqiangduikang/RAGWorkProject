from __future__ import annotations
import gradio as gr
from .faiss_store import FaissStore
from .embed_client import EmbedClient
from .llm_client import LLMClient
from .rag_chain import RAGChain

def main():
    store = FaissStore()
    store.load()

    rag = RAGChain(store, EmbedClient(), LLMClient())

    def chat_fn(message, history):
        answer = rag.answer(message)
        return answer

    demo = gr.ChatInterface(
        fn=chat_fn,
        title="AIC 平台智能答疑（RAG）",
        description="基于平台手册与FAQ文档检索增强生成。回答附引用，检索不到将拒答。",
    )
    demo.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    main()
