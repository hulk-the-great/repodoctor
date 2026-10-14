from __future__ import annotations

import json
from pathlib import Path


def detect_project_type(repo_dir: Path) -> str:
    if (repo_dir / "package.json").exists():
        return "node"
    if any((repo_dir / name).exists() for name in ["pyproject.toml", "setup.py", "requirements.txt", "run_tests.py"]):
        return "python"
    if (repo_dir / "tests").exists() or any(repo_dir.glob("test_*.py")):
        return "python"
    return "unknown"


def detect_test_command(repo_dir: Path) -> str:
    """Best-effort test-command detection for public GitHub repos.

    RepoDoctor is Python-first. Node detection is included only so the autopilot
    can fail clearly instead of pretending every repository is Python.
    """
    if (repo_dir / "run_tests.py").exists():
        return "python run_tests.py"

    if (repo_dir / "pytest.ini").exists() or (repo_dir / "tests").exists() or list(repo_dir.glob("test_*.py")):
        return "python -m pytest -q"

    pyproject = repo_dir / "pyproject.toml"
    if pyproject.exists():
        # Keep this simple and stable. Even if the project uses a different test
        # runner, pytest is the safest first assumption for this MS project MVP.
        return "python -m pytest -q"

    package_json = repo_dir / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8", errors="replace"))
            scripts = data.get("scripts") or {}
            if "test" in scripts:
                return "npm test"
        except Exception:
            return "npm test"

    return "python -m pytest -q"


def write_auto_test_script(repo_dir: Path, detected_command: str, install_deps: bool = True) -> Path:
    """Write a portable Python wrapper that can install deps and run tests.

    The main RepoDoctor TestRunner deliberately avoids shell=True. For real
    GitHub repos, however, we often need a multi-step command such as installing
    requirements before pytest. This wrapper keeps the external test command
    simple: `python .repodoctor_auto_test.py`.
    """
    script_path = repo_dir / ".repodoctor_auto_test.py"
    install_flag = "True" if install_deps else "False"
    command_literal = repr(detected_command)
    script = f'''from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INSTALL_DEPS = {install_flag}
TEST_COMMAND = {command_literal}


def run(cmd: list[str] | str, *, allow_fail: bool = False) -> int:
    print(f"[RepoDoctor auto-test] $ {{cmd}}", flush=True)
    if isinstance(cmd, list):
        proc = subprocess.run(cmd, cwd=ROOT, text=True)
    else:
        proc = subprocess.run(cmd, cwd=ROOT, text=True, shell=True)
    if proc.returncode != 0 and not allow_fail:
        print(f"[RepoDoctor auto-test] command failed with code {{proc.returncode}}", flush=True)
    return proc.returncode


def install_python_dependencies() -> None:
    # Ensure pytest exists for small Python repos.
    run([sys.executable, "-m", "pip", "install", "-q", "pytest"], allow_fail=True)

    req = ROOT / "requirements.txt"
    if req.exists():
        run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)], allow_fail=True)

    # Try editable install when packaging metadata is present. This is useful for
    # source-layout repos where tests import the package.
    if (ROOT / "pyproject.toml").exists() or (ROOT / "setup.py").exists():
        run([sys.executable, "-m", "pip", "install", "-q", "-e", "."], allow_fail=True)


def install_node_dependencies() -> None:
    if (ROOT / "package.json").exists() and not (ROOT / "node_modules").exists():
        run("npm install", allow_fail=True)


if __name__ == "__main__":
    if INSTALL_DEPS:
        if (ROOT / "package.json").exists() and TEST_COMMAND.startswith("npm"):
            install_node_dependencies()
        else:
            install_python_dependencies()

    code = run(TEST_COMMAND, allow_fail=True)
    sys.exit(code)
'''
    script_path.write_text(script, encoding="utf-8")
    return script_path
