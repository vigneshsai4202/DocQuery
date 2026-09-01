"""
LLM provider interface with streaming support.

complete()        → full response string (used internally / fallback)
stream()          → Generator[str, None, None] of token chunks

Three implementations:
- OllamaProvider      : local Ollama server
- OpenAIProvider      : OpenAI-compatible API (Groq, Azure, etc.)
- HuggingFaceProvider : Hugging Face Inference API
"""
import json
from abc import ABC, abstractmethod
from collections.abc import Generator

import requests

from app.core.config import settings


class BaseLLMProvider(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        """Return the full assistant reply as a string."""

    def stream(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> Generator[str, None, None]:
        """Yield token chunks. Default: yield complete() as one chunk."""
        yield self.complete(system_prompt, user_message, history=history or [])


class OllamaProvider(BaseLLMProvider):
    def _messages(self, system_prompt: str, user_message: str, history: list[dict]) -> list[dict]:
        return [{"role": "system", "content": system_prompt}, *history, {"role": "user", "content": user_message}]

    def complete(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        payload = {"model": settings.OLLAMA_MODEL, "messages": self._messages(system_prompt, user_message, history or []), "stream": False}
        resp = requests.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def stream(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> Generator[str, None, None]:
        payload = {"model": settings.OLLAMA_MODEL, "messages": self._messages(system_prompt, user_message, history or []), "stream": True}
        with requests.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        import openai
        self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)

    def _messages(self, system_prompt: str, user_message: str, history: list[dict]) -> list[dict]:
        return [{"role": "system", "content": system_prompt}, *history, {"role": "user", "content": user_message}]

    def complete(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        resp = self._client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=self._messages(system_prompt, user_message, history or []),
        )
        return resp.choices[0].message.content

    def stream(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> Generator[str, None, None]:
        resp = self._client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=self._messages(system_prompt, user_message, history or []),
            stream=True,
        )
        for chunk in resp:
            token = chunk.choices[0].delta.content
            if token:
                yield token


class HuggingFaceProvider(BaseLLMProvider):
    def complete(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        history_text = "".join(
            f"<s>[INST] {m['content']} [/INST]" if m["role"] == "user" else f"{m['content']} </s>"
            for m in (history or [])
        )
        prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{history_text}{user_message} [/INST]"
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 512, "return_full_text": False},
        }
        url = f"https://api-inference.huggingface.co/models/{settings.HUGGINGFACE_MODEL}"
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data[0].get("generated_text", "") if isinstance(data, list) else str(data)


def get_llm_provider() -> BaseLLMProvider:
    if settings.LLM_PROVIDER == "openai":
        return OpenAIProvider()
    if settings.LLM_PROVIDER == "huggingface":
        return HuggingFaceProvider()
    return OllamaProvider()


_provider: BaseLLMProvider | None = None


def llm_provider() -> BaseLLMProvider:
    global _provider
    if _provider is None:
        _provider = get_llm_provider()
    return _provider
