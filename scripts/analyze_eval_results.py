from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repodoctor.analysis.failure_analysis import classify_report, render_failure_analysis, summarize_reports  # noqa: E402


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Rebuild failure_analysis.md for a RepoDoctor eval folder")
    parser.add_argument("eval_dir", help="Path like runs/eval_YYYYMMDD_HHMMSS")
    args = parser.parse_args()

    eval_dir = (ROOT / args.eval_dir).resolve() if not Path(args.eval_dir).is_absolute() else Path(args.eval_dir)
    rows = []
    for report_path in sorted(eval_dir.glob("*/report.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        task_name = report_path.parent.name
        rows.append(
            {
                "task": task_name,
                "returncode": 0,
                "status": report.get("final_status"),
                "resolved": report.get("final_status") == "patched_tests_passed",
                "iterations": len(report.get("iterations", []) or []),
                "failure_category": classify_report(report),
                "report_path": str(report_path.relative_to(ROOT)),
            }
        )
    summary = summarize_reports(rows)
    out = eval_dir / "failure_analysis.md"
    out.write_text(render_failure_analysis(summary, rows), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
