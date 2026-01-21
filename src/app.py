# src/ui_gradio.py
from __future__ import annotations
import gradio as gr

from src.rag_chain import RAGChain


_chain = None


def get_chain() -> RAGChain:
    global _chain
    if _chain is None:
        _chain = RAGChain()
    return _chain


def qa(question: str) -> str:
    question = (question or "").strip()
    if not question:
        return "请输入问题。"
    chain = get_chain()
    return chain.answer(question)


def main():
    with gr.Blocks(title="RAG QA Demo (Doubao + FAISS)") as demo:
        gr.Markdown(
            "# 📚 北京师范大学AIC平台技术支持AI助手，有我在没意外~（RAG）\n"
            "- 输入你的问题\n"
            "- 系统会检索知识库并生成答案\n"
        )

        with gr.Row():
            question = gr.Textbox(
                label="问题",
                placeholder="例如：如何登录 AIC 后台？ / 如何手动安装镜像仓库 Harbor？",
                lines=2,
            )

        with gr.Row():
            ask_btn = gr.Button("提问", variant="primary")
            clear_btn = gr.Button("清空")

        answer = gr.Markdown(label="回答")

        ask_btn.click(fn=qa, inputs=[question], outputs=[answer])
        question.submit(fn=qa, inputs=[question], outputs=[answer])
        clear_btn.click(fn=lambda: ("", ""), inputs=None, outputs=[question, answer])

        gr.Markdown(
            "运行方式：\n"
            "- `uv pip install gradio`\n"
            "- `uv run python -m src.app`\n"
            "- `server_port=7860`\n"
        )
    # demo.launch(server_name="127.0.0.1", server_port=7860, root_path="/gradio-demo/")
    # [Lu] Change settings to adapt nginx
    demo.launch(root_path="/gradio-demo/")
    

if __name__ == "__main__":
    main()
