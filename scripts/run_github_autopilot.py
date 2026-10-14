from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repodoctor.auto.github_autopilot import GitHubAutopilot  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Clone a GitHub repo and run RepoDoctor automatically")
    parser.add_argument("--github-url", "--url", required=True, help="GitHub repo URL. Local paths also work for testing.")
    parser.add_argument("--issue", default=None, help="Optional issue text or path")
    parser.add_argument("--issue-url", default=None, help="Optional GitHub issue URL")
    parser.add_argument("--tests", default="auto", help="Test command or 'auto'")
    parser.add_argument("--provider", default="mock", help="mock, gemini, ollama, openai")
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--test-runner", choices=["local", "docker"], default="local")
    parser.add_argument("--docker-image", default="python:3.11-slim")
    parser.add_argument("--docker-network", default="bridge")
    parser.add_argument("--test-timeout", type=int, default=600)
    parser.add_argument("--no-install-deps", action="store_true")
    args = parser.parse_args()

    pilot = GitHubAutopilot(
        github_url=args.github_url,
        provider=args.provider,
        model=args.model,
        issue=args.issue,
        issue_url=args.issue_url,
        tests=args.tests,
        max_iterations=args.max_iterations,
        runs_dir=Path(args.runs_dir),
        test_runner_mode=args.test_runner,
        docker_image=args.docker_image,
        docker_network=args.docker_network,
        test_timeout=args.test_timeout,
        install_deps=not args.no_install_deps,
    )
    pilot.run()


if __name__ == "__main__":
    main()
