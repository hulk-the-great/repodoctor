from __future__ import annotations

from collections import Counter
from typing import Any


def classify_report(report: dict[str, Any]) -> str:
    """Return a compact failure/success category for a RepoDoctor run report."""
    status = report.get("final_status")
    if status == "patched_tests_passed":
        return "resolved"
    if status == "initial_tests_passed_no_patch_needed":
        return "no_patch_needed"

    iterations = report.get("iterations", []) or []
    if not iterations:
        return "no_iterations"

    last = iterations[-1]
    critic_category = last.get("critic_category")
    if critic_category and critic_category != "accepted":
        return str(critic_category)

    verifier = str(last.get("verifier_message", "")).lower()
    test_log = str(last.get("test_log", "")).lower()
    applied_edits = last.get("applied_edits", []) or []

    if "patch generation failed" in verifier or "json" in test_log:
        return "patch_generation_failure"
    if applied_edits and not any(e.get("applied") for e in applied_edits):
        return "patch_apply_failure"
    if "no edits" in verifier or "no edit" in verifier:
        return "empty_patch"
    if "tests failed" in verifier or "failed" in test_log:
        return "tests_still_failing"
    return "unclassified_failure"


def summarize_reports(rows: list[dict[str, Any]]) -> dict[str, Any]:
    categories = Counter(row.get("failure_category", "unknown") for row in rows)
    resolved = sum(1 for r in rows if r.get("resolved"))
    total = len(rows)
    iterations = [r.get("iterations", 0) for r in rows if isinstance(r.get("iterations"), int)]
    return {
        "total_tasks": total,
        "resolved": resolved,
        "resolve_rate": resolved / max(1, total),
        "avg_iterations": sum(iterations) / max(1, len(iterations)),
        "failure_categories": dict(categories),
    }


def render_failure_analysis(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("# RepoDoctor Benchmark and Failure Analysis")
    lines.append("")
    lines.append(f"**Tasks:** {summary['total_tasks']}")
    lines.append(f"**Resolved:** {summary['resolved']}")
    lines.append(f"**Resolve rate:** {summary['resolve_rate']:.2%}")
    lines.append(f"**Average iterations:** {summary['avg_iterations']:.2f}")
    lines.append("")
    lines.append("## Outcome Categories")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---:|")
    for category, count in sorted(summary["failure_categories"].items()):
        lines.append(f"| {category} | {count} |")
    lines.append("")
    lines.append("## Per-Task Results")
    lines.append("")
    lines.append("| Task | Status | Resolved | Iterations | Category | Report |")
    lines.append("|---|---|---:|---:|---|---|")
    for row in rows:
        report_path = row.get("report_path") or ""
        lines.append(
            f"| {row.get('task')} | {row.get('status')} | {row.get('resolved')} | "
            f"{row.get('iterations')} | {row.get('failure_category')} | `{report_path}` |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    if summary["resolved"] == summary["total_tasks"]:
        lines.append(
            "All benchmark tasks were resolved. This indicates that the current repair loop, AST-aware retrieval, "
            "PatchCritic safety checks, exact edit application, test execution, and verifier acceptance path work "
            "correctly on the bundled local benchmark."
        )
    else:
        lines.append(
            "Not all tasks were resolved. The category table above identifies whether failures came from patch generation, "
            "critic rejection, edit application, or tests that remained failing. These categories should guide the next "
            "engineering upgrade rather than being hidden."
        )
    lines.append("")
    lines.append("## Current Limitations")
    lines.append("")
    lines.append("- The bundled benchmark is local and synthetic; real GitHub repositories may have harder dependency and environment issues.")
    lines.append("- Test-based verification can only prove behavior covered by the available tests.")
    lines.append("- The PatchCritic is deterministic and conservative; future versions can add an LLM critic or AST-level patch validation.")
    lines.append("- Multi-file repairs and dependency-aware fixes are future work.")
    lines.append("")
    return "\n".join(lines)
