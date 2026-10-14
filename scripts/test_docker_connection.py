from __future__ import annotations

import subprocess


def main() -> None:
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            text=True,
            capture_output=True,
            timeout=20,
        )
    except FileNotFoundError:
        print("Docker command was not found. Install Docker Desktop and reopen PowerShell.")
        raise SystemExit(1)
    except subprocess.TimeoutExpired:
        print("Docker command timed out. Docker Desktop may not be running yet.")
        raise SystemExit(1)

    if result.returncode != 0:
        print("Docker is installed but not running properly.")
        print(result.stderr)
        raise SystemExit(result.returncode)

    print(f"Docker is available. Server version: {result.stdout.strip()}")


if __name__ == "__main__":
    main()
