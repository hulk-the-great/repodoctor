from __future__ import annotations

from repodoctor.agents.retrieval_agent import RetrievalAgent
from repodoctor.llm.base import BaseLLM
from repodoctor.models import CodeChunk, PatchProposal
from repodoctor.utils import extract_json_object, truncate


class PatchAgent:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def propose_patch(
        self,
        issue_text: str,
        issue_summary: dict,
        chunks: list[CodeChunk],
        test_log: str,
        current_diff: str,
    ) -> PatchProposal:
        context = RetrievalAgent.format_chunks(chunks)
        prompt = f"""
You are PatchAgent in RepoDoctor. Your job is to produce a minimal code fix.

IMPORTANT OUTPUT RULES:
Return only valid JSON. No Markdown. No prose outside JSON.
Use this schema:
{{
  "summary": "short explanation of the fix",
  "confidence": 0.0,
  "edits": [
    {{
      "path": "repo/relative/file/path.py",
      "old": "exact old text copied from the current source file, including indentation and newlines",
      "new": "replacement text, including indentation and newlines"
    }}
  ]
}}

Critical editing rules:
- The `old` text must appear EXACTLY ONCE in the target file.
- Do NOT use tiny ambiguous replacements such as only `return a * b` if that line may appear in more than one function.
- Prefer replacing a full function or a multi-line block containing the function header.
- Do not edit tests unless the issue explicitly says the tests are wrong.
- Keep the patch minimal and fix the root cause.
- If a previous attempt says "old text is ambiguous" or "old text not found", copy a larger exact block from the CURRENT relevant code chunk.
- If tests failed after a previous edit, assume RepoDoctor has reverted that failed edit before this new attempt.
- If unsure, return an empty edits list with low confidence.

Issue summary:
{issue_summary}

Original issue:
{truncate(issue_text, 5000)}

Relevant code chunks from the current clean worktree:
{context}

Latest test / edit feedback:
{truncate(test_log, 8000)}

Current git diff, if any:
{truncate(current_diff, 6000)}
""".strip()
        raw = self.llm.generate(prompt)
        data = extract_json_object(raw)
        return PatchProposal.model_validate(data)
