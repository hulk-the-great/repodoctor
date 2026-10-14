from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from repodoctor.auto.github_autopilot import GitHubAutopilot
from repodoctor.orchestrator import RepoDoctor

app = typer.Typer(help="RepoDoctor: a test-verified AI issue repair agent")
console = Console()


@app.command()
def run(
    repo: str = typer.Option(..., help="Local repo path or Git URL"),
    issue: str = typer.Option(..., help="Issue text or path to issue markdown file"),
    tests: str = typer.Option(..., help="Test command to run inside the repo"),
    provider: str = typer.Option("mock", help="LLM provider: mock, gemini, ollama, or openai"),
    model: Optional[str] = typer.Option(None, help="Model name, e.g. gemini-2.5-flash-lite, gemini-2.5-flash, or qwen2.5-coder:7b"),
    max_iterations: int = typer.Option(3, help="Maximum patch/test repair attempts"),
    runs_dir: Path = typer.Option(Path("runs"), help="Directory where run outputs are saved"),
    test_runner: str = typer.Option("local", help="Test runner mode: local or docker"),
    docker_image: str = typer.Option("python:3.11-slim", help="Docker image used when --test-runner docker"),
    docker_network: str = typer.Option("none", help="Docker network mode: none or bridge"),
    test_timeout: int = typer.Option(300, help="Timeout in seconds for each test run"),
):
    """Run RepoDoctor on a repository and issue."""
    doctor = RepoDoctor(
        repo=repo,
        issue=issue,
        test_command=tests,
        provider=provider,
        model=model,
        max_iterations=max_iterations,
        runs_dir=runs_dir,
        console=console,
        test_runner_mode=test_runner,
        docker_image=docker_image,
        docker_network=docker_network,
        test_timeout=test_timeout,
    )
    report = doctor.run()
    console.print(f"\n[bold green]Run complete.[/] Final status: {report.final_status}")
    console.print(f"Report: {report.run_dir / 'report.md'}")
    console.print(f"Patched repo copy: {report.repo_dir}")


@app.command()
def autopilot(
    github_url: str = typer.Option(..., "--github-url", "--url", help="GitHub repository URL. Local paths also work for testing."),
    issue: Optional[str] = typer.Option(None, help="Optional issue text or path to issue markdown file. If omitted, autopilot uses failing tests."),
    issue_url: Optional[str] = typer.Option(None, help="Optional GitHub issue URL to fetch as repair context."),
    tests: str = typer.Option("auto", help="Test command, or 'auto' to detect automatically"),
    provider: str = typer.Option("mock", help="LLM provider: mock, gemini, ollama, or openai"),
    model: Optional[str] = typer.Option(None, help="Model name, e.g. gemini-2.5-flash-lite"),
    max_iterations: int = typer.Option(5, help="Maximum patch/test repair attempts"),
    runs_dir: Path = typer.Option(Path("runs"), help="Directory where autopilot outputs are saved"),
    test_runner: str = typer.Option("local", help="Test runner mode: local or docker"),
    docker_image: str = typer.Option("python:3.11-slim", help="Docker image used when --test-runner docker"),
    docker_network: str = typer.Option("bridge", help="Docker network mode: bridge for dependency install, none for stricter sandbox"),
    test_timeout: int = typer.Option(600, help="Timeout in seconds for each test run"),
    install_deps: bool = typer.Option(True, help="Install Python/Node dependencies before running detected tests"),
):
    """Clone a GitHub repo and automatically run the full repair pipeline.

    If --issue or --issue-url is omitted, autopilot runs the detected test suite.
    If tests fail, it creates an issue from the failure log and repairs it. If
    tests pass, autopilot stops because there is no verified bug target.
    """
    pilot = GitHubAutopilot(
        github_url=github_url,
        provider=provider,
        model=model,
        issue=issue,
        issue_url=issue_url,
        tests=tests,
        max_iterations=max_iterations,
        runs_dir=runs_dir,
        test_runner_mode=test_runner,
        docker_image=docker_image,
        docker_network=docker_network,
        test_timeout=test_timeout,
        install_deps=install_deps,
        console=console,
    )
    result = pilot.run()
    console.print(f"\n[bold green]Autopilot complete.[/] Status: {result.status}")
    console.print(f"Summary: {Path(result.run_dir) / 'autopilot_summary.md'}")
    if result.repair_report_path:
        console.print(f"Repair report: {result.repair_report_path}")


@app.command("version")
def version():
    from repodoctor import __version__

    console.print(__version__)


if __name__ == "__main__":
    app()
