from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    provider: str = os.getenv("REPO_DOCTOR_LLM_PROVIDER", "mock")
    ollama_url: str = os.getenv("REPO_DOCTOR_OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("REPO_DOCTOR_OLLAMA_MODEL", "qwen2.5-coder:7b")
    openai_model: str = os.getenv("REPO_DOCTOR_OPENAI_MODEL", "gpt-5.5")
    gemini_model: str = os.getenv("REPO_DOCTOR_GEMINI_MODEL", "gemini-2.5-flash-lite")
    runs_dir: Path = Path(os.getenv("REPO_DOCTOR_RUNS_DIR", "runs"))
    max_file_bytes: int = int(os.getenv("REPO_DOCTOR_MAX_FILE_BYTES", "200000"))
    chunk_lines: int = int(os.getenv("REPO_DOCTOR_CHUNK_LINES", "160"))
    chunk_overlap: int = int(os.getenv("REPO_DOCTOR_CHUNK_OVERLAP", "30"))


DEFAULT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".rb", ".php", ".md",
    ".toml", ".yaml", ".yml", ".json",
}

IGNORE_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "dist", "build", "target", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".next", ".turbo",
}
