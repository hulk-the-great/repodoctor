from pathlib import Path
import shutil
import subprocess


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    root = Path("demo_repos/calculator_bug").resolve()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    write(
        root / "src" / "calculator.py",
        '''"""Tiny calculator module used to test RepoDoctor."""


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    """Return a divided by b."""
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a * b
''',
    )

    write(
        root / "tests" / "test_calculator.py",
        '''import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from calculator import add, divide, multiply, subtract


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(10, 4) == 6


def test_multiply():
    assert multiply(3, 4) == 12


def test_divide():
    assert divide(10, 2) == 5
''',
    )

    write(root / "README.md", "# Calculator Bug Demo\n\nThis repo intentionally contains a divide bug.\n")

    try:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial broken calculator"], cwd=root, check=True, capture_output=True)
    except Exception:
        # Git commit can fail if user.name/user.email is not configured.
        # RepoDoctor can still run because it will initialize a temporary repo copy.
        pass

    print(f"Created demo repository at: {root}")
    print("Run:")
    print('repodoctor run --repo demo_repos/calculator_bug --issue examples/issues/demo_bug.md --tests "python -m pytest -q" --provider mock --max-iterations 2')


if __name__ == "__main__":
    main()
