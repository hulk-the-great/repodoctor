from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"


st.set_page_config(
    page_title="RepoDoctor Dashboard",
    page_icon="🩺",
    layout="wide",
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def find_eval_dirs() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted([p for p in RUNS_DIR.iterdir() if p.is_dir() and p.name.startswith("eval_")], key=lambda p: p.stat().st_mtime, reverse=True)


def find_run_reports() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    direct = list(RUNS_DIR.glob("*/report.json"))
    autopilot_nested = list(RUNS_DIR.glob("autopilot_*/repairs/*/report.json"))
    return sorted(direct + autopilot_nested, key=lambda p: p.stat().st_mtime, reverse=True)


def find_autopilot_dirs() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted([p for p in RUNS_DIR.iterdir() if p.is_dir() and p.name.startswith("autopilot_")], key=lambda p: p.stat().st_mtime, reverse=True)


def status_badge(status: str) -> str:
    if status == "patched_tests_passed":
        return "✅ patched_tests_passed"
    if status == "initial_tests_passed_no_patch_needed":
        return "ℹ️ initial_tests_passed_no_patch_needed"
    if "failed" in status:
        return "❌ " + status
    return "⚠️ " + status


st.title("🩺 RepoDoctor Dashboard")
st.caption("Visual dashboard for issue-to-patch repair runs, Docker sandbox runs, benchmark summaries, and failure analysis.")

with st.sidebar:
    st.header("Navigation")
    page = st.radio("View", ["Benchmark summary", "GitHub autopilot", "Single run explorer", "How to run"], index=0)
    st.divider()
    st.write("Project root:")
    st.code(str(ROOT))

if page == "Benchmark summary":
    st.subheader("Benchmark summary")
    eval_dirs = find_eval_dirs()
    if not eval_dirs:
        st.warning("No benchmark folders found yet. Run scripts/evaluate_demo_suite.py first.")
        st.code("python scripts/evaluate_demo_suite.py --provider mock --max-iterations 3", language="powershell")
        st.stop()

    selected = st.selectbox("Select benchmark run", eval_dirs, format_func=lambda p: p.name)
    summary = load_json(selected / "summary.json")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Provider", summary.get("provider", "unknown"))
    c2.metric("Model", summary.get("model") or "None")
    c3.metric("Tasks", summary.get("num_tasks", 0))
    c4.metric("Resolve rate", f"{summary.get('resolve_rate', 0.0) * 100:.1f}%")

    c5, c6, c7 = st.columns(3)
    c5.metric("Resolved", summary.get("resolved", 0))
    c6.metric("Avg. iterations", f"{summary.get('avg_iterations', 0.0):.2f}")
    c7.metric("Test runner", summary.get("test_runner", "local"))

    if summary.get("test_runner") == "docker":
        st.info(f"Docker image: `{summary.get('docker_image')}` | network: `{summary.get('docker_network')}`")

    rows = summary.get("rows", [])
    if rows:
        df = pd.DataFrame(rows)
        st.markdown("### Per-task results")
        st.dataframe(df, use_container_width=True)

        st.markdown("### Failure categories")
        cats = summary.get("failure_categories", {})
        if cats:
            cat_df = pd.DataFrame([{"category": k, "count": v} for k, v in cats.items()])
            st.bar_chart(cat_df, x="category", y="count")
        else:
            st.success("No failure categories recorded.")

    fa = selected / "failure_analysis.md"
    if fa.exists():
        st.markdown("### Failure analysis")
        st.markdown(fa.read_text(encoding="utf-8"))

elif page == "GitHub autopilot":
    st.subheader("GitHub autopilot runs")
    autopilot_dirs = find_autopilot_dirs()
    if not autopilot_dirs:
        st.warning("No autopilot folders found yet. Run `repodoctor autopilot` first.")
        st.code('repodoctor autopilot --github-url https://github.com/YOUR_USERNAME/YOUR_REPO --provider gemini --model gemini-2.5-flash-lite --test-runner docker --docker-network bridge', language="powershell")
        st.stop()

    selected = st.selectbox("Select autopilot run", autopilot_dirs, format_func=lambda p: p.name)
    summary = load_json(selected / "autopilot_summary.json")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", summary.get("status", "unknown"))
    c2.metric("Provider", summary.get("provider", "unknown"))
    c3.metric("Model", summary.get("model") or "None")
    c4.metric("Test runner", summary.get("test_runner", "local"))

    st.markdown("### Repository and detection")
    st.write("**URL/path:**", summary.get("github_url", ""))
    st.write("**Project type:**", summary.get("detected_project_type", ""))
    st.write("**Detected test command:**", summary.get("detected_test_command", ""))
    st.write("**Effective test command:**", summary.get("effective_test_command", ""))
    st.write("**Initial tests passed:**", summary.get("initial_tests_passed"))

    if summary.get("message"):
        st.info(summary.get("message"))

    issue_path = summary.get("issue_path")
    if issue_path and Path(issue_path).exists():
        st.markdown("### Issue used by autopilot")
        st.markdown(Path(issue_path).read_text(encoding="utf-8", errors="replace"))

    repair_report_path = summary.get("repair_report_path")
    if repair_report_path and Path(repair_report_path).exists():
        st.markdown("### Repair report")
        report = load_json(Path(repair_report_path).with_suffix(".json")) if Path(repair_report_path).with_suffix(".json").exists() else {}
        if report:
            st.write("**Repair status:**", report.get("final_status"))
            st.code(report.get("final_diff", ""), language="diff")
        st.markdown(f"Report file: `{repair_report_path}`")

elif page == "Single run explorer":
    st.subheader("Single run explorer")
    reports = find_run_reports()
    if not reports:
        st.warning("No run reports found yet.")
        st.code("repodoctor run --repo demo_repos/calculator_bug --issue examples/issues/calculator_divide_bug.md --tests \"python run_tests.py\" --provider mock", language="powershell")
        st.stop()

    selected_report = st.selectbox("Select report", reports, format_func=lambda p: str(p.relative_to(ROOT)))
    report = load_json(selected_report)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", report.get("final_status", "unknown"))
    c2.metric("Provider", report.get("provider", "unknown"))
    c3.metric("Model", report.get("model") or "None")
    c4.metric("Test runner", report.get("test_runner_mode", "local"))

    st.markdown("### Issue")
    st.text_area("Issue text", report.get("issue_text", ""), height=180)

    st.markdown("### Iterations")
    for item in report.get("iterations", []):
        label = f"Iteration {item.get('iteration')} — {status_badge('patched_tests_passed' if item.get('tests_passed') else 'failed')}"
        with st.expander(label, expanded=item.get("tests_passed", False)):
            st.write("**Patch summary:**", item.get("patch_summary", ""))
            st.write("**PatchCritic accepted:**", item.get("critic_accepted"))
            st.write("**PatchCritic category:**", item.get("critic_category", ""))
            st.write("**PatchCritic message:**", item.get("critic_message", ""))
            st.write("**Verifier:**", item.get("verifier_message", ""))

            edits = item.get("applied_edits", [])
            if edits:
                st.markdown("**Applied edits**")
                st.dataframe(pd.DataFrame(edits), use_container_width=True)

            if item.get("test_log"):
                st.markdown("**Test / critic log**")
                st.code(item.get("test_log", ""), language="text")

            if item.get("git_diff"):
                st.markdown("**Iteration diff**")
                st.code(item.get("git_diff", ""), language="diff")

    st.markdown("### Final diff")
    st.code(report.get("final_diff", ""), language="diff")

else:
    st.subheader("How to run")
    st.markdown("### GitHub URL autopilot")
    st.code("""$env:GEMINI_API_KEY="your_key_here"
repodoctor autopilot --github-url https://github.com/YOUR_USERNAME/YOUR_REPO --provider gemini --model gemini-2.5-flash-lite --test-runner docker --docker-image python:3.11-slim --docker-network bridge --max-iterations 5""", language="powershell")

    st.markdown("### Local run")
    st.code("""python scripts/create_demo_suite.py
repodoctor run --repo demo_repos/calculator_bug --issue examples/issues/calculator_divide_bug.md --tests "python run_tests.py" --provider mock --max-iterations 3""", language="powershell")

    st.markdown("### Docker sandbox run")
    st.code("""docker version
repodoctor run --repo demo_repos/calculator_bug --issue examples/issues/calculator_divide_bug.md --tests "python run_tests.py" --provider mock --max-iterations 3 --test-runner docker --docker-image python:3.11-slim --docker-network none""", language="powershell")

    st.markdown("### Gemini + Docker benchmark")
    st.code("""$env:GEMINI_API_KEY="your_key_here"
python scripts/evaluate_demo_suite.py --provider gemini --model gemini-2.5-flash-lite --max-iterations 5 --test-runner docker --docker-image python:3.11-slim --docker-network none --offset 0 --limit 2""", language="powershell")
