from __future__ import annotations

import os

from repodoctor.llm.base import BaseLLM


class OpenAILLM(BaseLLM):
    """OpenAI Responses API provider.

    This keeps RepoDoctor lightweight: your laptop only indexes files and runs tests;
    the model call happens through the API.
    """

    def __init__(self, model: str | None = None, temperature: float = 0.1):
        self.model = model or os.getenv("REPO_DOCTOR_OPENAI_MODEL", "gpt-5.5")
        self.temperature = temperature

    def generate(self, prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI provider requires the official Python SDK. Install it with: pip install openai"
            ) from exc

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set. In PowerShell use: $env:OPENAI_API_KEY='your_key_here'"
            )

        client = OpenAI()
        response = client.responses.create(
            model=self.model,
            input=prompt,
        )
        return getattr(response, "output_text", "") or ""
