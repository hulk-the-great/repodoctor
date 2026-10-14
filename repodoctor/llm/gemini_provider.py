from __future__ import annotations

import os

from repodoctor.llm.base import BaseLLM


class GeminiLLM(BaseLLM):
    """Google Gemini Developer API provider for RepoDoctor.

    Use this when your laptop cannot run a local LLM. RepoDoctor still runs the
    code indexing, file editing, and tests locally; only the language-model call
    goes through Gemini.
    """

    def __init__(self, model: str | None = None, temperature: float = 0.1):
        self.model = model or os.getenv("REPO_DOCTOR_GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.temperature = temperature

    def generate(self, prompt: str) -> str:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "Gemini provider requires the Google Gen AI SDK. "
                "Install it with: pip install google-genai"
            ) from exc

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. In PowerShell use: "
                "$env:GEMINI_API_KEY='your_key_here'"
            )

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=4096,
                # RepoDoctor agents ask for strict JSON. This makes Gemini much
                # more reliable for IssueAgent and PatchAgent outputs.
                response_mime_type="application/json",
            ),
        )

        return response.text or ""
