from __future__ import annotations

import requests

from repodoctor.llm.base import BaseLLM


class OllamaLLM(BaseLLM):
    def __init__(self, model: str, base_url: str = "http://localhost:11434", temperature: float = 0.1):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        try:
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Could not call Ollama at {url}. Make sure Ollama is running and the model is pulled. Original error: {exc}"
            ) from exc
        data = response.json()
        return data.get("response", "")
