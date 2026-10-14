from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any


def run_command(cmd: list[str] | str, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Run a command safely with captured output.

    RepoDoctor normally receives test commands as strings, e.g.
    `python -m pytest -q tests --rootdir=.`. Earlier versions used shell=True
    for string commands. This version tokenizes strings and runs without a shell,
    which is safer and avoids shell/grandchild timeout issues during repeated
    benchmark execution.
    """
    if isinstance(cmd, str):
        args = shlex.split(cmd, posix=os.name != "nt")
    else:
        args = cmd

    env = os.environ.copy()
    # Makes pytest startup more deterministic on machines with many auto-loaded plugins.
    if any("pytest" in str(part) for part in args):
        env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    return subprocess.run(
        args,
        cwd=str(cwd),
        shell=False,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=env,
    )


def safe_relpath(path: str) -> Path:
    p = Path(path)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"Unsafe repository path: {path}")
    return p


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract the first JSON object from model output."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text.strip()).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model output")

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])

    raise ValueError("Could not parse JSON object from model output")


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n...[truncated]...\n" + text[-half:]
