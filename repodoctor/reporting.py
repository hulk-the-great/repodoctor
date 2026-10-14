from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from repodoctor.models import RunReport
from repodoctor.utils import write_text


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dataclass_fields__"):
        return _json_safe(asdict(obj))
    if isinstance(obj, list):
        return [_json_safe(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    return obj


def save_report(report: RunReport) -> None:
    report_json = _json_safe(report)
    write_text(report.run_dir / "report.json", json.dumps(report_json, indent=2))
    write_text(report.run_dir / "report.md", render_markdown(report_json))


def render_markdown(report: dict[str, Any]) -> str:
    lines = []
    lines.append("# RepoDoctor Run Report")
    lines.append("")
    lines.append(f"**Final status:** `{report.get('final_status')}`")
    lines.append(f"**Provider:** `{report.get('provider')}`")
    lines.append(f"**Model:** `{report.get('model')}`")
    lines.append(f"**Repo directory:** `{report.get('repo_dir')}`")
    lines.append(f"**Test runner:** `{report.get('test_runner_mode', 'local')}`")
    if report.get("docker_image"):
        lines.append(f"**Docker image:** `{report.get('docker_image')}`")
        lines.append(f"**Docker network:** `{report.get('docker_network')}`")
    lines.append("")
    lines.append("## Issue")
    lines.append("")
    lines.append(report.get("issue_text", ""))
    lines.append("")
    lines.append("## Iterations")
    lines.append("")

    for item in report.get("iterations", []):
        i = item.get("iteration")
        lines.append(f"### Iteration {i}")
        lines.append("")
        lines.append(f"**Patch summary:** {item.get('patch_summary', '')}")
        lines.append(f"**Confidence:** {item.get('confidence', '')}")
        lines.append(f"**PatchCritic accepted:** `{item.get('critic_accepted')}`")
        lines.append(f"**PatchCritic category:** `{item.get('critic_category', '')}`")
        lines.append(f"**PatchCritic message:** {item.get('critic_message', '')}")
        lines.append(f"**Verifier:** {item.get('verifier_message', '')}")
        lines.append(f"**Tests passed:** `{item.get('tests_passed')}`")
        lines.append(f"**Test duration:** `{item.get('test_duration_seconds')}` seconds")
        lines.append("")
        lines.append("Applied edits:")
        lines.append("")
        for edit in item.get("applied_edits", []):
            lines.append(f"- `{edit.get('path')}`: {edit.get('reason')} | applied={edit.get('applied')}")
        lines.append("")
        if item.get("test_log"):
            lines.append("<details><summary>Test / critic log</summary>")
            lines.append("")
            lines.append("```text")
            lines.append(item.get("test_log", ""))
            lines.append("```")
            lines.append("</details>")
            lines.append("")

    lines.append("## Final Diff")
    lines.append("")
    lines.append("```diff")
    lines.append(report.get("final_diff", ""))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)
