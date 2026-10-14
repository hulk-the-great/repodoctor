from __future__ import annotations

from repodoctor.llm.base import BaseLLM
from repodoctor.utils import extract_json_object, truncate


class IssueAgent:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def analyze(self, issue_text: str) -> dict:
        prompt = f"""
You are the IssueAgent in RepoDoctor.
Create a structured issue summary as JSON.

Return only JSON with these keys:
- bug_type: short string
- symptoms: list of strings
- expected_behavior: string
- likely_files: list of strings, may be empty
- test_focus: list of strings, may be empty

Issue:
{truncate(issue_text, 5000)}
""".strip()
        raw = self.llm.generate(prompt)
        try:
            return extract_json_object(raw)
        except Exception:
            return {
                "bug_type": "unknown",
                "symptoms": [issue_text[:500]],
                "expected_behavior": "unknown",
                "likely_files": [],
                "test_focus": [],
                "raw_model_output": raw,
            }

    @staticmethod
    def to_query(issue_text: str, issue_summary: dict, test_log: str = "") -> str:
        pieces = [issue_text]
        pieces.extend(issue_summary.get("symptoms", []))
        pieces.append(issue_summary.get("expected_behavior", ""))
        pieces.extend(issue_summary.get("likely_files", []))
        pieces.extend(issue_summary.get("test_focus", []))
        if test_log:
            pieces.append(test_log)
        return "\n".join(str(p) for p in pieces if p)
