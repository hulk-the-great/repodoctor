from __future__ import annotations

import ast
import math
import re
from collections import Counter
from pathlib import Path

from repodoctor.config import DEFAULT_EXTENSIONS, IGNORE_DIRS, Settings
from repodoctor.models import CodeChunk
from repodoctor.utils import read_text

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(text):
        t = raw.lower()
        tokens.append(t)
        # Code identifiers often use underscores. Splitting test_divide into
        # test + divide helps retrieval connect failing tests to source symbols.
        if "_" in t:
            tokens.extend(part for part in t.split("_") if part)
    return tokens


def _line_span(lines: list[str], start_line: int, end_line: int) -> str:
    start = max(1, start_line)
    end = min(len(lines), end_line)
    return "".join(lines[start - 1:end])


class CodebaseIndex:
    """Hybrid code index with AST-aware chunks for Python source files."""

    def __init__(self, repo_dir: Path, settings: Settings | None = None):
        self.repo_dir = repo_dir
        self.settings = settings or Settings()
        self.chunks: list[CodeChunk] = []
        self._chunk_tokens: list[Counter[str]] = []
        self._doc_freq: Counter[str] = Counter()

    def build(self) -> None:
        self.chunks.clear()
        self._chunk_tokens.clear()
        self._doc_freq.clear()

        for file_path in self._iter_files():
            rel = file_path.relative_to(self.repo_dir).as_posix()
            text = read_text(file_path)
            lines = text.splitlines(keepends=True)

            if file_path.suffix.lower() == ".py":
                self._add_python_ast_chunks(rel, text, lines)

            self._add_line_chunks(rel, lines)

    def search(self, query: str, top_k: int = 8) -> list[CodeChunk]:
        if not self.chunks:
            self.build()
        q_tokens = tokenize(query)
        if not q_tokens:
            return self.chunks[:top_k]

        q_counts = Counter(q_tokens)
        n_docs = max(1, len(self.chunks))
        scored: list[CodeChunk] = []

        query_lower = query.lower()

        for chunk, counts in zip(self.chunks, self._chunk_tokens):
            score = 0.0
            length_norm = 1.0 / math.sqrt(max(1, sum(counts.values())))
            for tok, q_tf in q_counts.items():
                tf = counts.get(tok, 0)
                if not tf:
                    continue
                idf = math.log((n_docs + 1) / (1 + self._doc_freq.get(tok, 0))) + 1.0
                score += q_tf * (1 + math.log(tf)) * idf * length_norm

            lowered_path = chunk.path.lower()
            if lowered_path in query_lower:
                score += 150.0
            if lowered_path.startswith(".repodoctor"):
                score -= 50.0
            if lowered_path.startswith("tests/") or "/tests/" in lowered_path:
                score -= 15.0
            if lowered_path.startswith("src/") or "/src/" in lowered_path:
                score += 8.0
            for tok in q_tokens:
                if tok in lowered_path:
                    score += 0.35

            if chunk.symbol_name:
                symbol_tokens = set(tokenize(chunk.symbol_name))
                exact_symbol = chunk.symbol_name.lower() in query.lower()
                overlap = sum(1 for tok in q_tokens if tok in symbol_tokens)
                score += overlap * 1.5
                if exact_symbol:
                    score += 4.0
                if not (lowered_path.startswith("tests/") or "/tests/" in lowered_path) and chunk.symbol_name.lower() in query_lower:
                    score += 40.0

            if chunk.chunk_type in {"function", "class"}:
                score += 0.35

            if score > 0:
                scored.append(
                    CodeChunk(
                        path=chunk.path,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        text=chunk.text,
                        score=score,
                        chunk_type=chunk.chunk_type,
                        symbol_name=chunk.symbol_name,
                        metadata=dict(chunk.metadata),
                    )
                )

        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]

    def _add_python_ast_chunks(self, rel: str, text: str, lines: list[str]) -> None:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
                continue
            chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
            start = int(node.lineno)
            end = int(node.end_lineno or node.lineno)
            symbol_text = _line_span(lines, start, end)
            if not symbol_text.strip():
                continue
            metadata = {"ast_type": type(node).__name__}
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metadata["args"] = [arg.arg for arg in node.args.args]
            self._add_chunk(
                CodeChunk(
                    path=rel,
                    start_line=start,
                    end_line=end,
                    text=symbol_text,
                    chunk_type=chunk_type,
                    symbol_name=node.name,
                    metadata=metadata,
                )
            )

    def _add_line_chunks(self, rel: str, lines: list[str]) -> None:
        chunk_lines = self.settings.chunk_lines
        overlap = self.settings.chunk_overlap
        start = 0
        while start < len(lines):
            end = min(start + chunk_lines, len(lines))
            chunk_text = "".join(lines[start:end])
            self._add_chunk(CodeChunk(path=rel, start_line=start + 1, end_line=end, text=chunk_text))
            if end == len(lines):
                break
            start = max(end - overlap, start + 1)

    def _add_chunk(self, chunk: CodeChunk) -> None:
        self.chunks.append(chunk)
        token_source = f"{chunk.path}\n{chunk.chunk_type}\n{chunk.symbol_name or ''}\n{chunk.text}"
        counts = Counter(tokenize(token_source))
        self._chunk_tokens.append(counts)
        for tok in counts:
            self._doc_freq[tok] += 1

    def _iter_files(self):
        for path in self.repo_dir.rglob("*"):
            if not path.is_file():
                continue
            rel_parts = path.relative_to(self.repo_dir).parts
            if any(part in IGNORE_DIRS for part in rel_parts):
                continue
            if path.suffix.lower() not in DEFAULT_EXTENSIONS:
                continue
            try:
                if path.stat().st_size > self.settings.max_file_bytes:
                    continue
            except OSError:
                continue
            yield path
