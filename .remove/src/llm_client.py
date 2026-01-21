from __future__ import annotations
import os
from openai import OpenAI
from .config import ARK_BASE_URL, ARK_API_KEY, DOUBAO_CHAT_MODEL


class LLMClient:
    def __init__(self):
        api_key = os.environ.get("ARK_API_KEY") or ARK_API_KEY
        if not api_key:
            raise RuntimeError("Please set ARK_API_KEY env var.")
        self.client = OpenAI(base_url=ARK_BASE_URL, api_key=api_key)
        self.model = os.environ.get("DOUBAO_CHAT_MODEL") or DOUBAO_CHAT_MODEL

    def chat(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 800) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
