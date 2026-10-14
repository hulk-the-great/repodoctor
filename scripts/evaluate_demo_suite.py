from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repodoctor.analysis.failure_analysis import classify_report, render_failure_analysis, summarize_reports  # noqa: E402


def _load_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _find_new_report(out_dir: Path, before: set[Path]) -> Path | None:
    after = {p for p in out_dir.glob("*/report.json")}
    new_reports = sorted(after - before, key=lambda p: p.stat().st_mtime, reverse=True)
    if new_reports:
        return new_reports[0]
    reports = sorted(after, key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0] if reports else None


def run_task(
    task: dict,
    provider: str,
    model: str | None,
    max_iterations: int,
    out_dir: Path,
    test_runner: str = "local",
    docker_image: str = "python:3.11-slim",
    docker_network: str = "none",
    test_timeout: int = 300,
) -> dict[str, Any]:
    before_reports = {p for p in out_dir.glob("*/report.json")}
    cmd = [
        sys.executable,
        "-m",
        "repodoctor.cli",
        "run",
        "--repo",
        task["repo"],
        "--issue",
        task["issue"],
        "--tests",
        task["tests"],
        "--provider",
        provider,
        "--max-iterations",
        str(max_iterations),
        "--runs-dir",
        str(out_dir),
        "--test-runner",
        test_runner,
        "--docker-image",
        docker_image,
        "--docker-network",
        docker_network,
        "--test-timeout",
        str(test_timeout),
    ]
    if model:
        cmd.extend(["--model", model])

    task_log = out_dir / f"{task['name']}_console.log"
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            timeout=max(test_timeout + 60, max_iterations * (test_timeout + 30)),
        )
        output = ""
        task_log.write_text("Console output was streamed directly to the terminal. See the individual report.md file.\n", encoding="utf-8")
    except subprocess.TimeoutExpired as exc:
        output = f"Task timed out after {exc.timeout} seconds"
        task_log.write_text(output, encoding="utf-8")
        proc = subprocess.CompletedProcess(cmd, returncode=124)

    report_path = _find_new_report(out_dir, before_reports)
    report = _load_report(report_path) if report_path else {}
    status = report.get("final_status", "unknown")
    if status == "unknown":
        for line in output.splitlines():
            if "Final status:" in line:
                status = line.split("Final status:", 1)[-1].strip()

    return {
        "task": task["name"],
        "returncode": proc.returncode,
        "status": status,
        "resolved": status == "patched_tests_passed",
        "iterations": len(report.get("iterations", []) or []),
        "failure_category": classify_report(report) if report else "missing_report",
        "report_path": str(report_path.relative_to(ROOT)) if report_path else "",
        "console_log": str(task_log.relative_to(ROOT)),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate RepoDoctor on the local demo suite")
    parser.add_argument("--suite", default="benchmarks/demo_suite_10.json")
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--offset", type=int, default=0, help="Start index for batch evaluation")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of tasks to run")
    parser.add_argument("--test-runner", choices=["local", "docker"], default="local", help="Run tests locally or in Docker")
    parser.add_argument("--docker-image", default="python:3.11-slim", help="Docker image for sandboxed tests")
    parser.add_argument("--docker-network", default="none", help="Docker network mode: none or bridge")
    parser.add_argument("--test-timeout", type=int, default=300, help="Timeout in seconds for each test run")
    args = parser.parse_args()

    suite_path = ROOT / args.suite
    all_tasks = json.loads(suite_path.read_text(encoding="utf-8"))
    tasks = all_tasks[args.offset : args.offset + args.limit if args.limit is not None else None]
    out_dir = ROOT / "runs" / f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for task in tasks:
        print(f"\n=== Running {task['name']} ===", flush=True)
        row = run_task(
            task,
            args.provider,
            args.model,
            args.max_iterations,
            out_dir,
            test_runner=args.test_runner,
            docker_image=args.docker_image,
            docker_network=args.docker_network,
            test_timeout=args.test_timeout,
        )
        print(f"{task['name']}: {row['status']} | category={row['failure_category']} | iterations={row['iterations']}", flush=True)
        rows.append(row)

    analysis_summary = summarize_reports(rows)
    summary = {
        "provider": args.provider,
        "model": args.model,
        "test_runner": args.test_runner,
        "docker_image": args.docker_image if args.test_runner == "docker" else None,
        "docker_network": args.docker_network if args.test_runner == "docker" else None,
        "num_tasks": len(rows),
        "resolved": analysis_summary["resolved"],
        "resolve_rate": analysis_summary["resolve_rate"],
        "avg_iterations": analysis_summary["avg_iterations"],
        "failure_categories": analysis_summary["failure_categories"],
        "rows": rows,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "failure_analysis.md").write_text(render_failure_analysis(analysis_summary, rows), encoding="utf-8")

    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["task", "returncode", "status", "resolved", "iterations", "failure_category", "report_path", "console_log"],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in writer.fieldnames})

    print("\n=== Summary ===")
    print(f"Resolved: {summary['resolved']}/{len(rows)} = {summary['resolve_rate']:.2%}")
    print(f"Average iterations: {summary['avg_iterations']:.2f}")
    print(f"Saved to: {out_dir}")
    print(f"Failure analysis: {out_dir / 'failure_analysis.md'}")


if __name__ == "__main__":
    main()
