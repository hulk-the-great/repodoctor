from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repodoctor.auto.test_detection import detect_project_type, detect_test_command, write_auto_test_script
from repodoctor.orchestrator import RepoDoctor
from repodoctor.tools.git_ops import is_remote_repo
from repodoctor.tools.test_runner import DockerTestRunner, TestRunner
from repodoctor.utils import read_text, run_command, truncate, write_text


@dataclass
class AutopilotResult:
    status: str
    github_url: str
    source_dir: str
    run_dir: str
    issue_path: str | None
    detected_project_type: str
    detected_test_command: str
    effective_test_command: str
    test_runner: str
    provider: str
    model: str | None
    initial_tests_passed: bool | None
    repair_status: str | None
    repair_report_path: str | None
    message: str


class GitHubAutopilot:
    """End-to-end GitHub URL automation for RepoDoctor.

    The autopilot is intentionally conservative:
    - It clones/copies the repository into a run directory.
    - It detects a test command and writes a portable auto-test wrapper.
    - If no issue is provided, it creates an issue from failing tests.
    - It calls the existing RepoDoctor repair loop and saves a summary.

    Important: if a repo's tests already pass and no issue/issue-url is given,
    there is no verified bug target. In that case the autopilot stops with a
    clear `no_failing_tests_no_issue` status instead of inventing a bug.
    """

    def __init__(
        self,
        github_url: str,
        provider: str = "mock",
        model: str | None = None,
        issue: str | None = None,
        issue_url: str | None = None,
        tests: str = "auto",
        max_iterations: int = 5,
        runs_dir: Path = Path("runs"),
        test_runner_mode: str = "local",
        docker_image: str = "python:3.11-slim",
        docker_network: str = "bridge",
        test_timeout: int = 600,
        install_deps: bool = True,
        console: Console | None = None,
    ) -> None:
        self.github_url = github_url
        self.provider = provider
        self.model = model
        self.issue = issue
        self.issue_url = issue_url
        self.tests = tests
        self.max_iterations = max_iterations
        self.runs_dir = runs_dir
        self.test_runner_mode = test_runner_mode
        self.docker_image = docker_image
        self.docker_network = docker_network
        self.test_timeout = test_timeout
        self.install_deps = install_deps
        self.console = console or Console()

    def run(self) -> AutopilotResult:
        self.console.print(Panel.fit("RepoDoctor GitHub Autopilot starting", style="bold cyan"))
        autopilot_dir = self.runs_dir / f"autopilot_{time.strftime('%Y%m%d_%H%M%S')}"
        source_dir = autopilot_dir / "source_repo"
        autopilot_dir.mkdir(parents=True, exist_ok=True)

        self.console.print(f"[cyan]Preparing repository from URL/path:[/] {self.github_url}")
        self._prepare_source_repo(self.github_url, source_dir)
        self.console.print(f"[green]Source repository prepared:[/] {source_dir}")

        project_type = detect_project_type(source_dir)
        detected_command = self.tests if self.tests != "auto" else detect_test_command(source_dir)
        auto_test_script = write_auto_test_script(source_dir, detected_command, install_deps=self.install_deps)
        effective_command = f"python {auto_test_script.name}"

        self._print_detection(project_type, detected_command, effective_command)

        issue_text = self._resolve_issue_text(autopilot_dir)
        initial_passed: bool | None = None

        if not issue_text:
            self.console.print("[cyan]No issue provided. Running detected tests to discover a failing behavior...[/]")
            initial = self._run_initial_tests(source_dir, effective_command)
            initial_passed = initial.passed
            (autopilot_dir / "initial_test_log.txt").write_text(initial.compact_log(12000), encoding="utf-8")
            if initial.passed:
                result = AutopilotResult(
                    status="no_failing_tests_no_issue",
                    github_url=self.github_url,
                    source_dir=str(source_dir),
                    run_dir=str(autopilot_dir),
                    issue_path=None,
                    detected_project_type=project_type,
                    detected_test_command=detected_command,
                    effective_test_command=effective_command,
                    test_runner=self.test_runner_mode,
                    provider=self.provider,
                    model=self.model,
                    initial_tests_passed=True,
                    repair_status=None,
                    repair_report_path=None,
                    message=(
                        "The repository tests passed and no issue was provided. "
                        "RepoDoctor needs either failing tests or an issue/issue-url to create a verified repair target."
                    ),
                )
                self._save_summary(result)
                self.console.print(Panel.fit(result.message, style="yellow"))
                return result

            issue_text = self._issue_from_failing_tests(initial.compact_log(12000), detected_command)
            self.console.print("[yellow]Created an automatic issue from failing tests.[/]")

        issue_path = autopilot_dir / "autogenerated_issue.md"
        issue_path.write_text(issue_text, encoding="utf-8")
        self.console.print(f"[green]Issue file:[/] {issue_path}")

        repair_runs_dir = autopilot_dir / "repairs"
        doctor = RepoDoctor(
            repo=str(source_dir),
            issue=str(issue_path),
            test_command=effective_command,
            provider=self.provider,
            model=self.model,
            max_iterations=self.max_iterations,
            runs_dir=repair_runs_dir,
            console=self.console,
            test_runner_mode=self.test_runner_mode,
            docker_image=self.docker_image,
            docker_network=self.docker_network,
            test_timeout=self.test_timeout,
        )
        report = doctor.run()
        report_path = report.run_dir / "report.md"

        status = "repair_completed" if report.final_status == "patched_tests_passed" else "repair_attempted_not_resolved"
        message = f"RepoDoctor finished. Repair status: {report.final_status}. Report: {report_path}"
        result = AutopilotResult(
            status=status,
            github_url=self.github_url,
            source_dir=str(source_dir),
            run_dir=str(autopilot_dir),
            issue_path=str(issue_path),
            detected_project_type=project_type,
            detected_test_command=detected_command,
            effective_test_command=effective_command,
            test_runner=self.test_runner_mode,
            provider=self.provider,
            model=self.model,
            initial_tests_passed=initial_passed,
            repair_status=report.final_status,
            repair_report_path=str(report_path),
            message=message,
        )
        self._save_summary(result)
        self.console.print(Panel.fit(message, style="bold green" if report.final_status == "patched_tests_passed" else "bold yellow"))
        return result

    def _prepare_source_repo(self, url_or_path: str, dest: Path) -> None:
        if dest.exists():
            shutil.rmtree(dest)
        if is_remote_repo(url_or_path):
            result = run_command(["git", "clone", "--depth", "1", url_or_path, str(dest)], cwd=dest.parent, timeout=600)
            if result.returncode != 0:
                # Some Git servers do not support shallow clone. Retry normal clone.
                result = run_command(["git", "clone", url_or_path, str(dest)], cwd=dest.parent, timeout=900)
            if result.returncode != 0:
                raise RuntimeError(f"git clone failed:\n{result.stdout}\n{result.stderr}")
        else:
            src = Path(url_or_path).expanduser().resolve()
            if not src.exists():
                raise FileNotFoundError(f"Repository path does not exist: {src}")
            ignore = shutil.ignore_patterns(
                ".git", ".venv", "venv", "env", "node_modules", "dist", "build", "__pycache__", ".pytest_cache"
            )
            shutil.copytree(src, dest, ignore=ignore)

    def _resolve_issue_text(self, run_dir: Path) -> str:
        if self.issue_url:
            return self._fetch_github_issue(self.issue_url)
        if self.issue:
            path = Path(self.issue)
            if path.exists():
                return read_text(path)
            return self.issue
        return ""

    def _fetch_github_issue(self, issue_url: str) -> str:
        parsed = _parse_github_issue_url(issue_url)
        if not parsed:
            return f"# GitHub issue\n\nUnable to parse issue URL. Use this issue URL as context:\n{issue_url}\n"
        owner, repo, number = parsed
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
        try:
            response = requests.get(api_url, timeout=30, headers={"Accept": "application/vnd.github+json"})
            if response.status_code == 200:
                data = response.json()
                title = data.get("title") or f"GitHub issue #{number}"
                body = data.get("body") or ""
                return f"# {title}\n\nSource: {issue_url}\n\n{body}\n"
            return f"# GitHub issue #{number}\n\nSource: {issue_url}\n\nGitHub API returned {response.status_code}: {response.text[:1000]}\n"
        except Exception as exc:
            return f"# GitHub issue #{number}\n\nSource: {issue_url}\n\nFailed to fetch issue body: {exc}\n"

    def _run_initial_tests(self, repo_dir: Path, command: str):
        if self.test_runner_mode == "docker":
            runner = DockerTestRunner(
                repo_dir,
                command,
                timeout=self.test_timeout,
                image=self.docker_image,
                network=self.docker_network,
            )
            self.console.print(f"[cyan]Autopilot test sandbox:[/] Docker image={self.docker_image}, network={self.docker_network}")
        else:
            runner = TestRunner(repo_dir, command, timeout=self.test_timeout)
            self.console.print("[cyan]Autopilot test sandbox:[/] local host process")
        result = runner.run()
        color = "green" if result.passed else "red"
        self.console.print(f"Initial auto-detected tests: [{color}]{'PASSED' if result.passed else 'FAILED'}[/] in {result.duration_seconds:.2f}s")
        return result

    def _issue_from_failing_tests(self, log: str, detected_command: str) -> str:
        return f"""# Autogenerated issue from failing test suite

RepoDoctor Autopilot detected that the repository test suite fails when running:

```text
{detected_command}
```

Expected behavior:

The repository test suite should pass without failures.

Actual behavior:

The test suite failed. Use the failure log below to identify the root cause, make the minimal source-code fix, and make the tests pass.

```text
{truncate(log, 10000)}
```
"""

    def _print_detection(self, project_type: str, detected_command: str, effective_command: str) -> None:
        table = Table(title="Autopilot detection")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("Project type", project_type)
        table.add_row("Detected test command", detected_command)
        table.add_row("Effective test command", effective_command)
        table.add_row("Dependency install", "enabled" if self.install_deps else "disabled")
        table.add_row("Test runner", self.test_runner_mode)
        self.console.print(table)

    def _save_summary(self, result: AutopilotResult) -> None:
        run_dir = Path(result.run_dir)
        data = asdict(result)
        (run_dir / "autopilot_summary.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        lines = [
            "# RepoDoctor GitHub Autopilot Summary",
            "",
            f"**Status:** `{result.status}`",
            f"**GitHub URL/path:** `{result.github_url}`",
            f"**Provider:** `{result.provider}`",
            f"**Model:** `{result.model}`",
            f"**Test runner:** `{result.test_runner}`",
            f"**Detected project type:** `{result.detected_project_type}`",
            f"**Detected test command:** `{result.detected_test_command}`",
            f"**Effective test command:** `{result.effective_test_command}`",
            f"**Initial tests passed:** `{result.initial_tests_passed}`",
            f"**Repair status:** `{result.repair_status}`",
            f"**Issue path:** `{result.issue_path}`",
            f"**Repair report:** `{result.repair_report_path}`",
            "",
            "## Message",
            "",
            result.message,
            "",
        ]
        (run_dir / "autopilot_summary.md").write_text("\n".join(lines), encoding="utf-8")


def _parse_github_issue_url(issue_url: str) -> tuple[str, str, str] | None:
    m = re.search(r"github\.com/([^/]+)/([^/]+)/(?:issues|pull)/(\d+)", issue_url)
    if not m:
        return None
    owner, repo, number = m.group(1), m.group(2), m.group(3)
    repo = repo.removesuffix(".git")
    return owner, repo, number
