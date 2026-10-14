from __future__ import annotations

from repodoctor.models import AppliedEditResult, TestResult


class VerifierAgent:
    def verify(self, edit_results: list[AppliedEditResult], test_result: TestResult) -> tuple[bool, str]:
        applied_count = sum(1 for r in edit_results if r.applied)
        if applied_count == 0:
            return False, "No edits were applied."
        if test_result.passed:
            return True, "Patch accepted. Tests passed."
        return False, "Patch rejected. Tests failed."
