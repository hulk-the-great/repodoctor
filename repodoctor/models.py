from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class CodeChunk:
    path: str
    start_line: int
    end_line: int
    text: str
    score: float = 0.0
    chunk_type: str = "text"  # text, function, class
    symbol_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float

    @property
    def passed(self) -> bool:
        return self.returncode == 0

    def compact_log(self, max_chars: int = 6000) -> str:
        text = f"STDOUT:\n{self.stdout}\n\nSTDERR:\n{self.stderr}"
        if len(text) > max_chars:
            return text[-max_chars:]
        return text


class FileEdit(BaseModel):
    path: str = Field(..., description="Repository-relative path to edit")
    old: str = Field(..., description="Exact old text to replace")
    new: str = Field(..., description="Replacement text")


class PatchProposal(BaseModel):
    summary: str = ""
    edits: list[FileEdit] = Field(default_factory=list)
    confidence: float = 0.0


@dataclass
class PatchCritique:
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    category: str = "accepted"

    @property
    def message(self) -> str:
        parts: list[str] = []
        if self.reasons:
            parts.append("; ".join(self.reasons))
        if self.warnings:
            parts.append("warnings: " + "; ".join(self.warnings))
        return " | ".join(parts) if parts else "Patch passed critic checks."


@dataclass
class AppliedEditResult:
    path: str
    applied: bool
    reason: str


@dataclass
class RunReport:
    run_dir: Path
    repo_dir: Path
    issue_text: str
    provider: str
    model: str | None
    test_runner_mode: str = "local"
    docker_image: str | None = None
    docker_network: str | None = None
    test_timeout: int | None = None
    iterations: list[dict[str, Any]] = field(default_factory=list)
    final_status: str = "unknown"
    final_diff: str = ""
