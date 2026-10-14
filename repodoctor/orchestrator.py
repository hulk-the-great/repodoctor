from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repodoctor.agents.issue_agent import IssueAgent
from repodoctor.agents.patch_agent import PatchAgent
from repodoctor.agents.patch_critic_agent import PatchCriticAgent
from repodoctor.agents.retrieval_agent import RetrievalAgent
from repodoctor.agents.test_agent import TestAgent
from repodoctor.agents.verifier_agent import VerifierAgent
from repodoctor.config import Settings
from repodoctor.llm.factory import make_llm
from repodoctor.models import AppliedEditResult, RunReport
from repodoctor.reporting import save_report
from repodoctor.tools.file_editor import apply_edits
from repodoctor.tools.git_ops import git_diff, git_status, prepare_repo, reset_worktree
from repodoctor.tools.indexer import CodebaseIndex
from repodoctor.tools.test_runner import DockerTestRunner, TestRunner
from repodoctor.utils import read_text, truncate


class RepoDoctor:
    def __init__(
        self,
        repo: str,
        issue: str,
        test_command: str,
        provider: str = "mock",
        model: str | None = None,
        max_iterations: int = 3,
        runs_dir: Path | None = None,
        console: Console | None = None,
        test_runner_mode: str = "local",
        docker_image: str = "python:3.11-slim",
        docker_network: str = "none",
        test_timeout: int = 300,
    ):
        self.repo = repo
        self.issue = issue
        self.test_command = test_command
        self.provider = provider
        self.model = model
        self.max_iterations = max_iterations
        self.settings = Settings()
        self.runs_dir = runs_dir or self.settings.runs_dir
        self.console = console or Console()
        self.test_runner_mode = test_runner_mode.lower().strip()
        self.docker_image = docker_image
        self.docker_network = docker_network
        self.test_timeout = test_timeout

    def run(self) -> RunReport:
        self.console.print(Panel.fit("RepoDoctor starting", style="bold cyan"))

        issue_text = self._load_issue(self.issue)
        run_dir, repo_dir = prepare_repo(self.repo, self.runs_dir)
        self.console.print(f"[green]Prepared repository:[/] {repo_dir}")

        llm = make_llm(self.provider, self.model)
        issue_agent = IssueAgent(llm)
        patch_agent = PatchAgent(llm)
        patch_critic = PatchCriticAgent()
        verifier_agent = VerifierAgent()
        if self.test_runner_mode == "docker":
            runner = DockerTestRunner(
                repo_dir,
                self.test_command,
                timeout=self.test_timeout,
                image=self.docker_image,
                network=self.docker_network,
            )
            self.console.print(f"[cyan]Test sandbox:[/] Docker image={self.docker_image}, network={self.docker_network}")
        elif self.test_runner_mode == "local":
            runner = TestRunner(repo_dir, self.test_command, timeout=self.test_timeout)
            self.console.print("[cyan]Test sandbox:[/] local host process")
        else:
            raise ValueError("test_runner_mode must be 'local' or 'docker'")

        test_agent = TestAgent(runner)

        report = RunReport(
            run_dir=run_dir,
            repo_dir=repo_dir,
            issue_text=issue_text,
            provider=self.provider,
            model=self.model,
            test_runner_mode=self.test_runner_mode,
            docker_image=self.docker_image if self.test_runner_mode == "docker" else None,
            docker_network=self.docker_network if self.test_runner_mode == "docker" else None,
            test_timeout=self.test_timeout,
        )

        self.console.print("[cyan]Analyzing issue...[/]")
        issue_summary = issue_agent.analyze(issue_text)
        self.console.print(Panel(str(issue_summary), title="Issue summary", expand=False))

        self.console.print("[cyan]Building AST-aware code index...[/]")
        index = CodebaseIndex(repo_dir, self.settings)
        index.build()
        retrieval_agent = RetrievalAgent(index)
        ast_chunks = sum(1 for c in index.chunks if c.chunk_type in {"function", "class"})
        self.console.print(f"Indexed [bold]{len(index.chunks)}[/] chunks, including [bold]{ast_chunks}[/] AST symbol chunks.")

        self.console.print("[cyan]Running initial tests...[/]")
        initial_test = test_agent.run_tests()
        latest_test_log = initial_test.compact_log()
        self._print_test_result("Initial tests", initial_test.passed, initial_test.duration_seconds)

        if initial_test.passed:
            report.final_status = "initial_tests_passed_no_patch_needed"
            report.final_diff = git_diff(repo_dir)
            save_report(report)
            return report

        for iteration in range(1, self.max_iterations + 1):
            self.console.rule(f"Iteration {iteration}")
            query = IssueAgent.to_query(issue_text, issue_summary, latest_test_log)
            chunks = retrieval_agent.retrieve(query, top_k=8)
            self._print_retrieved(chunks)

            current_diff = git_diff(repo_dir)
            self.console.print("[cyan]Generating patch proposal...[/]")
            try:
                proposal = patch_agent.propose_patch(
                    issue_text=issue_text,
                    issue_summary=issue_summary,
                    chunks=chunks,
                    test_log=latest_test_log,
                    current_diff=current_diff,
                )
            except Exception as exc:
                self.console.print(f"[red]Patch generation failed:[/] {exc}")
                report.iterations.append(
                    {
                        "iteration": iteration,
                        "patch_summary": "patch generation failed",
                        "confidence": 0.0,
                        "critic_accepted": False,
                        "critic_category": "patch_generation_failed",
                        "critic_message": str(exc),
                        "applied_edits": [],
                        "tests_passed": False,
                        "test_duration_seconds": 0.0,
                        "test_log": str(exc),
                        "verifier_message": str(exc),
                    }
                )
                latest_test_log = str(exc)
                continue

            self.console.print(Panel(proposal.summary or "No summary", title="Patch proposal", expand=False))

            critique = patch_critic.critique(repo_dir, proposal, issue_summary)
            critic_color = "green" if critique.accepted else "red"
            self.console.print(f"[bold {critic_color}]PatchCritic:[/] {critique.message}")

            edit_results: list[AppliedEditResult] = []
            test_result = None
            verifier_message = ""
            accepted = False

            if critique.accepted:
                edit_results = apply_edits(repo_dir, proposal.edits)
                for result in edit_results:
                    color = "green" if result.applied else "red"
                    self.console.print(f"[{color}]{result.path}[/]: {result.reason}")

                test_result = test_agent.run_tests()
                accepted, verifier_message = verifier_agent.verify(edit_results, test_result)
                edit_feedback = "\n".join(
                    f"EDIT FEEDBACK: {r.path}: {r.reason} (applied={r.applied})" for r in edit_results
                )
                latest_test_log = edit_feedback + "\n\n" + test_result.compact_log()
                self._print_test_result("Tests after patch", test_result.passed, test_result.duration_seconds)
                self.console.print(f"[bold]{verifier_message}[/]")
            else:
                edit_results = [
                    AppliedEditResult(e.path, False, f"critic rejected patch: {critique.message}")
                    for e in proposal.edits
                ]
                verifier_message = f"PatchCritic rejected patch before execution: {critique.message}"
                latest_test_log = verifier_message + "\n\nPrevious test log:\n" + latest_test_log
                self.console.print(f"[yellow]{verifier_message}[/]")

            reset_message = ""
            if not accepted:
                reset_message = reset_worktree(repo_dir)
                if reset_message and critique.accepted:
                    self.console.print("[yellow]Failed patch reverted; next iteration starts from a clean worktree.[/]")

            report.iterations.append(
                {
                    "iteration": iteration,
                    "patch_summary": proposal.summary,
                    "confidence": proposal.confidence,
                    "critic_accepted": critique.accepted,
                    "critic_category": critique.category,
                    "critic_message": critique.message,
                    "critic_reasons": critique.reasons,
                    "critic_warnings": critique.warnings,
                    "applied_edits": [r.__dict__ for r in edit_results],
                    "tests_passed": bool(test_result.passed) if test_result is not None else False,
                    "test_duration_seconds": round(test_result.duration_seconds, 3) if test_result is not None else 0.0,
                    "test_log": truncate(latest_test_log, 8000),
                    "verifier_message": verifier_message,
                    "git_status": git_status(repo_dir),
                    "git_diff": truncate(git_diff(repo_dir), 12000),
                    "reset_after_failed_patch": bool(reset_message),
                    "reset_message": reset_message,
                }
            )

            if accepted:
                report.final_status = "patched_tests_passed"
                break
        else:
            report.final_status = "failed_after_max_iterations"

        report.final_diff = git_diff(repo_dir)
        save_report(report)
        self.console.print(Panel.fit(f"Final status: {report.final_status}\nReport: {run_dir / 'report.md'}", style="bold green"))
        return report

    def _load_issue(self, issue: str) -> str:
        path = Path(issue)
        if path.exists():
            return read_text(path)
        return issue

    def _print_test_result(self, label: str, passed: bool, duration: float) -> None:
        status = "PASSED" if passed else "FAILED"
        color = "green" if passed else "red"
        self.console.print(f"{label}: [{color}]{status}[/] in {duration:.2f}s")

    def _print_retrieved(self, chunks) -> None:
        table = Table(title="Retrieved code chunks")
        table.add_column("Rank")
        table.add_column("File")
        table.add_column("Lines")
        table.add_column("Type")
        table.add_column("Symbol")
        table.add_column("Score")
        for i, chunk in enumerate(chunks, start=1):
            table.add_row(
                str(i),
                chunk.path,
                f"{chunk.start_line}-{chunk.end_line}",
                chunk.chunk_type,
                chunk.symbol_name or "-",
                f"{chunk.score:.3f}",
            )
        self.console.print(table)
