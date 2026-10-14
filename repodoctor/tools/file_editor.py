from __future__ import annotations

from pathlib import Path

from repodoctor.models import AppliedEditResult, FileEdit
from repodoctor.utils import read_text, safe_relpath, write_text


def apply_edits(repo_dir: Path, edits: list[FileEdit]) -> list[AppliedEditResult]:
    """Apply exact text replacements safely.

    The first Gemini run showed a common LLM editing failure: the model may emit
    an overly small old-text pattern such as "return a * b". If that text appears
    more than once, replacing the first occurrence can corrupt the wrong function.

    To avoid that, RepoDoctor only applies an edit when the old text appears
    exactly once. If it appears multiple times, the edit is rejected and the next
    repair iteration asks the model for a larger function-level replacement block.
    """
    results: list[AppliedEditResult] = []
    for edit in edits:
        try:
            rel = safe_relpath(edit.path)
            path = repo_dir / rel
            if not path.exists():
                results.append(AppliedEditResult(edit.path, False, "file does not exist"))
                continue

            text = read_text(path)
            occurrences = text.count(edit.old)

            if occurrences == 0:
                results.append(
                    AppliedEditResult(
                        edit.path,
                        False,
                        "old text not found exactly; copy a larger exact block from the current file",
                    )
                )
                continue

            if occurrences > 1:
                results.append(
                    AppliedEditResult(
                        edit.path,
                        False,
                        f"old text is ambiguous; appears {occurrences} times; include the full function/block in old text",
                    )
                )
                continue

            new_text = text.replace(edit.old, edit.new, 1)
            write_text(path, new_text)
            results.append(AppliedEditResult(edit.path, True, "applied"))
        except Exception as exc:
            results.append(AppliedEditResult(edit.path, False, f"error: {exc}"))
    return results
