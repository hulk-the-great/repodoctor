from __future__ import annotations

import shutil
import time
from pathlib import Path

from repodoctor.utils import run_command


def is_remote_repo(repo: str) -> bool:
    return repo.startswith("http://") or repo.startswith("https://") or repo.startswith("git@")


def prepare_repo(repo: str, runs_dir: Path) -> tuple[Path, Path]:
    """Clone/copy repo into a fresh run directory and return (run_dir, repo_dir)."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = runs_dir / timestamp
    repo_dir = run_dir / "repo"
    run_dir.mkdir(parents=True, exist_ok=True)

    if is_remote_repo(repo):
        result = run_command(["git", "clone", repo, str(repo_dir)], cwd=run_dir, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"git clone failed:\n{result.stderr}")
    else:
        src = Path(repo).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(f"Repository path does not exist: {src}")
        ignore = shutil.ignore_patterns(
            ".git", ".venv", "venv", "env", "node_modules", "dist", "build", "__pycache__", ".pytest_cache"
        )
        shutil.copytree(src, repo_dir, ignore=ignore)

    ensure_git_repo(repo_dir)
    return run_dir, repo_dir


def ensure_git_repo(repo_dir: Path) -> None:
    if (repo_dir / ".git").exists():
        return

    run_command(["git", "init"], cwd=repo_dir, timeout=60)
    run_command(["git", "add", "."], cwd=repo_dir, timeout=60)
    run_command(
        [
            "git",
            "-c",
            "user.email=repodoctor@example.local",
            "-c",
            "user.name=RepoDoctor",
            "commit",
            "-m",
            "initial state before RepoDoctor patch",
        ],
        cwd=repo_dir,
        timeout=60,
    )


def git_diff(repo_dir: Path) -> str:
    result = run_command(["git", "diff", "--", "."], cwd=repo_dir, timeout=60)
    return result.stdout if result.returncode == 0 else result.stdout + result.stderr


def git_status(repo_dir: Path) -> str:
    result = run_command(["git", "status", "--short"], cwd=repo_dir, timeout=60)
    return result.stdout if result.returncode == 0 else result.stdout + result.stderr


def reset_worktree(repo_dir: Path) -> str:
    """Revert failed patch attempts so the next iteration starts clean.

    RepoDoctor accepts a patch only when tests pass. If tests fail after an edit,
    leaving that edit in place can cause later iterations to search/replace stale
    text. We therefore restore tracked files and remove untracked generated files.
    """
    out: list[str] = []
    restore = run_command(["git", "restore", "--source=HEAD", "--", "."], cwd=repo_dir, timeout=60)
    out.append(restore.stdout + restore.stderr)
    clean = run_command(["git", "clean", "-fd", "--", "."], cwd=repo_dir, timeout=60)
    out.append(clean.stdout + clean.stderr)
    return "".join(out).strip()
