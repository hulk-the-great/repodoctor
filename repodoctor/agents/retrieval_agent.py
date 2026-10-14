from __future__ import annotations

from repodoctor.models import CodeChunk
from repodoctor.tools.indexer import CodebaseIndex
from repodoctor.utils import truncate


class RetrievalAgent:
    def __init__(self, index: CodebaseIndex):
        self.index = index

    def retrieve(self, query: str, top_k: int = 8) -> list[CodeChunk]:
        return self.index.search(query, top_k=top_k)

    @staticmethod
    def format_chunks(chunks: list[CodeChunk], max_chars_per_chunk: int = 3500) -> str:
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            symbol = f" | symbol={chunk.symbol_name}" if chunk.symbol_name else ""
            header = (
                f"--- CHUNK {i}: {chunk.path}:{chunk.start_line}-{chunk.end_line} "
                f"type={chunk.chunk_type}{symbol} score={chunk.score:.3f} ---"
            )
            parts.append(f"{header}\n{truncate(chunk.text, max_chars_per_chunk)}")
        return "\n\n".join(parts)
