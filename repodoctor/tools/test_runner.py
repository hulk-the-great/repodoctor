from __future__ import annotations

import shlex
import time
from pathlib import Path

from repodoctor.models import TestResult
from repodoctor.utils import run_command


class TestRunner:
    def __init__(self, repo_dir: Path, command: str, timeout: int = 180):
        self.repo_dir = repo_dir
        self.command = command
        self.timeout = timeout

    def run(self) -> TestResult:
        start = time.time()
        try:
            result = run_command(self.command, cwd=self.repo_dir, timeout=self.timeout)
            duration = time.time() - start
            return TestResult(
                command=self.command,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_seconds=duration,
            )
        except Exception as exc:
            duration = time.time() - start
            return TestResult(
                command=self.command,
                returncode=999,
                stdout="",
                stderr=f"Test command failed to execute: {exc}",
                duration_seconds=duration,
            )


class DockerTestRunner(TestRunner):
    """Run repository tests inside a Docker container.

    This is intended as a safety/professionalism upgrade for RepoDoctor. The
    repository copy in the current run directory is mounted at /workspace. The
    default network mode is "none", which is safest and works for the local demo
    benchmark because those repos have no external dependencies.

    For real GitHub repos that need dependency installation, either:
    1. build a custom image with dependencies already installed and pass it using
       --docker-image, or
    2. use --docker-network bridge if you are comfortable allowing dependency
       downloads during the test run.
    """

    def __init__(
        self,
        repo_dir: Path,
        command: str,
        timeout: int = 300,
        image: str = "python:3.11-slim",
        network: str = "none",
    ):
        super().__init__(repo_dir=repo_dir, command=command, timeout=timeout)
        self.image = image
        self.network = network

    def run(self) -> TestResult:
        start = time.time()
        try:
            # Fail early with a helpful error if Docker is not installed/running.
            docker_check = run_command(["docker", "version", "--format", "{{.Server.Version}}"], cwd=self.repo_dir, timeout=20)
            if docker_check.returncode != 0:
                return TestResult(
                    command=self._display_command(),
                    returncode=998,
                    stdout=docker_check.stdout,
                    stderr=(
                        "Docker is not available or the Docker daemon is not running.\n"
                        + docker_check.stderr
                    ),
                    duration_seconds=time.time() - start,
                )

            # The command runs inside Linux shell because most Python project test
            # commands are shell-style strings. The repo is mounted read/write so
            # generated test artifacts, if any, remain in the run copy.
            repo_mount = str(self.repo_dir.resolve())
            inner_command = self.command
            docker_cmd = [
                "docker",
                "run",
                "--rm",
                "--network",
                self.network,
                "-v",
                f"{repo_mount}:/workspace",
                "-w",
                "/workspace",
                self.image,
                "sh",
                "-lc",
                inner_command,
            ]
            result = run_command(docker_cmd, cwd=self.repo_dir, timeout=self.timeout)
            return TestResult(
                command=self._display_command(),
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_seconds=time.time() - start,
            )
        except Exception as exc:
            return TestResult(
                command=self._display_command(),
                returncode=999,
                stdout="",
                stderr=f"Docker test command failed to execute: {exc}",
                duration_seconds=time.time() - start,
            )

    def _display_command(self) -> str:
        return (
            f"docker run --rm --network {self.network} "
            f"-v {shlex.quote(str(self.repo_dir.resolve()))}:/workspace "
            f"-w /workspace {self.image} sh -lc {shlex.quote(self.command)}"
        )
