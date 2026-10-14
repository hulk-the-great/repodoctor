from __future__ import annotations

import re
from pathlib import Path

from repodoctor.models import PatchCritique, PatchProposal
from repodoctor.utils import read_text, safe_relpath

_TEST_PATH_RE = re.compile(r"(^|/)(tests?|test)(_.*)?(/|$)|(^|/)test_[^/]+\.py$|_test\.py$", re.I)


class PatchCriticAgent:
    """Deterministic safety critic for generated patches."""

    def __init__(self, allow_test_edits: bool = False, max_edits: int = 4):
        self.allow_test_edits = allow_test_edits
        self.max_edits = max_edits

    def critique(self, repo_dir: Path, proposal: PatchProposal, issue_summary: dict | None = None) -> PatchCritique:
        reasons: list[str] = []
        warnings: list[str] = []

        if not proposal.edits:
            return PatchCritique(False, ["patch contains no edits"], category="empty_patch")

        if len(proposal.edits) > self.max_edits:
            reasons.append(f"patch contains too many edits ({len(proposal.edits)} > {self.max_edits})")

        likely_files = {Path(p).name.lower() for p in (issue_summary or {}).get("likely_files", []) if isinstance(p, str)}
        edited_basenames: set[str] = set()

        for idx, edit in enumerate(proposal.edits, start=1):
            try:
                rel = safe_relpath(edit.path)
            except Exception as exc:
                reasons.append(f"edit {idx}: unsafe path {edit.path!r}: {exc}")
                continue

            rel_posix = rel.as_posix()
            edited_basenames.add(Path(rel_posix).name.lower())
            path = repo_dir / rel
            if not path.exists():
                reasons.append(f"edit {idx}: target file does not exist: {rel_posix}")
                continue

            if _TEST_PATH_RE.search(rel_posix) and not self.allow_test_edits:
                reasons.append(f"edit {idx}: modifies test file {rel_posix}; RepoDoctor should fix source code, not tests")

            if not edit.old:
                reasons.append(f"edit {idx}: old text is empty")
                continue
            if edit.old == edit.new:
                reasons.append(f"edit {idx}: old and new text are identical")

            text = read_text(path)
            occurrences = text.count(edit.old)
            if occurrences == 0:
                reasons.append(f"edit {idx}: old text not found exactly in {rel_posix}")
            elif occurrences > 1:
                reasons.append(f"edit {idx}: old text is ambiguous in {rel_posix}; appears {occurrences} times")

            old_len = max(1, len(edit.old.strip()))
            new_len = len(edit.new.strip())
            if old_len > 80 and new_len / old_len < 0.35:
                reasons.append(f"edit {idx}: replacement deletes too much code")

            if self._looks_like_hardcoded_test_fix(edit.new):
                reasons.append(f"edit {idx}: replacement appears to hard-code a test-specific output")

            if len(edit.old) < 20:
                warnings.append(f"edit {idx}: old text is very small; function/block-level replacements are safer")

        if likely_files and edited_basenames and edited_basenames.isdisjoint(likely_files):
            warnings.append("edited file basename does not match issue_agent likely_files; inspect retrieval quality")

        if reasons:
            return PatchCritique(False, reasons, warnings, category=self._category_from_reasons(reasons))
        return PatchCritique(True, warnings=warnings, category="accepted")

    def _looks_like_hardcoded_test_fix(self, new_text: str) -> bool:
        literal_if = re.search(r"if\s+[^:\n]*(==|in)\s*['\"0-9]", new_text)
        literal_return = re.search(r"return\s+(['\"][^'\"]+['\"]|\d+(?:\.\d+)?)\s*(#.*)?$", new_text, re.M)
        return bool(literal_if and literal_return)

    def _category_from_reasons(self, reasons: list[str]) -> str:
        joined = " ".join(reasons).lower()
        if "ambiguous" in joined:
            return "ambiguous_edit"
        if "test file" in joined:
            return "test_modification"
        if "not found" in joined:
            return "patch_format_failure"
        if "hard-code" in joined:
            return "hardcoded_patch"
        if "deletes too much" in joined:
            return "overbroad_patch"
        if "unsafe path" in joined:
            return "unsafe_path"
        return "critic_rejected"
