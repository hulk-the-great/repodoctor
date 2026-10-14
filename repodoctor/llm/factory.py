from __future__ import annotations

from repodoctor.config import Settings
from repodoctor.llm.base import BaseLLM
from repodoctor.llm.gemini_provider import GeminiLLM
from repodoctor.llm.mock import MockLLM
from repodoctor.llm.ollama import OllamaLLM
from repodoctor.llm.openai_provider import OpenAILLM


SUPPORTED_PROVIDERS = ("mock", "gemini", "ollama", "openai")


def make_llm(provider: str | None = None, model: str | None = None) -> BaseLLM:
    settings = Settings()
    provider = (provider or settings.provider).lower().strip()

    if provider == "mock":
        return MockLLM()

    if provider == "gemini":
        return GeminiLLM(model=model or settings.gemini_model)

    if provider == "ollama":
        return OllamaLLM(model=model or settings.ollama_model, base_url=settings.ollama_url)

    if provider == "openai":
        return OpenAILLM(model=model or settings.openai_model)

    raise ValueError(
        f"Unsupported provider '{provider}'. "
        f"Use one of: {', '.join(SUPPORTED_PROVIDERS)}."
    )
