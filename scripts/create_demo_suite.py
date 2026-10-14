from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "demo_repos"
ISSUES = ROOT / "examples" / "issues"
BENCH = ROOT / "benchmarks"


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def init_repo(path: Path) -> None:
    write(path / "run_tests.py", '\n    from __future__ import annotations\n\n    import importlib.util\n    import pathlib\n    import traceback\n\n    failures = []\n    for test_file in sorted(pathlib.Path("tests").glob("test_*.py")):\n        spec = importlib.util.spec_from_file_location(test_file.stem, test_file)\n        module = importlib.util.module_from_spec(spec)\n        assert spec.loader is not None\n        spec.loader.exec_module(module)\n        for name in sorted(dir(module)):\n            if not name.startswith("test_"):\n                continue\n            fn = getattr(module, name)\n            if not callable(fn):\n                continue\n            try:\n                fn()\n                print(f"PASS {test_file.name}::{name}")\n            except Exception:\n                failures.append(f"{test_file.name}::{name}")\n                print(f"FAIL {test_file.name}::{name}")\n                traceback.print_exc()\n\n    if failures:\n        print(f"FAILED {len(failures)} test(s): {\', \'.join(failures)}")\n        raise SystemExit(1)\n    print("ALL TESTS PASSED")\n')
    run(["git", "init"], path)
    run(["git", "config", "user.email", "demo@example.com"], path)
    run(["git", "config", "user.name", "RepoDoctor Demo"], path)
    run(["git", "add", "."], path)
    run(["git", "commit", "-m", "Initial broken demo repo"], path)


def task(name: str, repo_dir: str, issue_file: str) -> dict:
    return {
        "name": name,
        "repo": str(BASE / repo_dir),
        "issue": str(ISSUES / issue_file),
        "tests": "python run_tests.py",
    }


def calculator_divide_bug() -> dict:
    repo = BASE / "calculator_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "calculator.py", '''
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
    ''')
    write(repo / "tests" / "test_calculator.py", '''
    import pytest
    from src.calculator import add, subtract, multiply, divide

    def test_add():
        assert add(2, 3) == 5

    def test_subtract():
        assert subtract(10, 4) == 6

    def test_multiply():
        assert multiply(6, 7) == 42

    def test_divide():
        assert divide(10, 2) == 5
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)
    ''')
    write(ISSUES / "calculator_divide_bug.md", '''
    # Bug: divide returns the wrong result

    The calculator package has a bug in the `divide` function.
    `divide(10, 2)` should return `5`, but the result looks like multiplication.
    Fix the bug and make the tests pass.
    ''')
    init_repo(repo)
    return task("calculator_divide_bug", "calculator_bug", "calculator_divide_bug.md")


def string_slug_bug() -> dict:
    repo = BASE / "string_utils_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "strings.py", '''
    import re

    def slugify(text: str) -> str:
        """Convert text into a lowercase URL slug."""
        text = text.strip().lower()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        return text.strip("_")
    ''')
    write(repo / "tests" / "test_strings.py", '''
    from src.strings import slugify

    def test_slugify_spaces():
        assert slugify("Hello World") == "hello-world"

    def test_slugify_punctuation():
        assert slugify(" RepoDoctor: Agent Repair! ") == "repodoctor-agent-repair"
    ''')
    write(ISSUES / "string_slug_bug.md", '''
    # Bug: slugify uses the wrong separator

    The `slugify` helper should create URL slugs with hyphens, not underscores.
    Example: `slugify("Hello World")` should return `hello-world`.
    ''')
    init_repo(repo)
    return task("string_slug_bug", "string_utils_bug", "string_slug_bug.md")


def cart_discount_bug() -> dict:
    repo = BASE / "cart_discount_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "cart.py", '''
    def apply_discount(total: float, discount_percent: float) -> float:
        """Return total after applying percentage discount."""
        if discount_percent < 0 or discount_percent > 100:
            raise ValueError("discount_percent must be between 0 and 100")
        return total * discount_percent / 100

    def final_price(total: float, discount_percent: float, tax_percent: float) -> float:
        discounted = apply_discount(total, discount_percent)
        return discounted * (1 + tax_percent / 100)
    ''')
    write(repo / "tests" / "test_cart.py", '''
    import pytest
    from src.cart import apply_discount, final_price

    def test_apply_discount():
        assert apply_discount(100, 20) == 80
        assert apply_discount(250, 10) == 225

    def test_final_price_after_discount_and_tax():
        assert final_price(100, 20, 10) == 88

    def test_bad_discount():
        with pytest.raises(ValueError):
            apply_discount(100, -1)
    ''')
    write(ISSUES / "cart_discount_bug.md", '''
    # Bug: discount calculation returns only the discount amount

    `apply_discount(total, discount_percent)` should return the price after discount.
    For example, `apply_discount(100, 20)` should return `80`, not `20`.
    ''')
    init_repo(repo)
    return task("cart_discount_bug", "cart_discount_bug", "cart_discount_bug.md")


def stats_average_bug() -> dict:
    repo = BASE / "stats_average_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "stats_utils.py", '''
    def average(values: list[float]) -> float:
        """Return the arithmetic mean of a non-empty list."""
        if not values:
            raise ValueError("values must not be empty")
        return sum(values)
    ''')
    write(repo / "tests" / "test_stats_utils.py", '''
    import pytest
    from src.stats_utils import average

    def test_average_values():
        assert average([2, 4, 6]) == 4
        assert average([10, 20]) == 15

    def test_average_empty():
        with pytest.raises(ValueError):
            average([])
    ''')
    write(ISSUES / "stats_average_bug.md", '''
    # Bug: average returns the sum instead of the mean

    The `average` function should divide the sum by the number of values.
    `average([2, 4, 6])` should return `4`, not `12`.
    ''')
    init_repo(repo)
    return task("stats_average_bug", "stats_average_bug", "stats_average_bug.md")


def temperature_conversion_bug() -> dict:
    repo = BASE / "temperature_conversion_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "temperature.py", '''
    def celsius_to_fahrenheit(celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return celsius * 9 / 5 - 32

    def fahrenheit_to_celsius(fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius."""
        return (fahrenheit - 32) * 5 / 9
    ''')
    write(repo / "tests" / "test_temperature.py", '''
    from src.temperature import celsius_to_fahrenheit, fahrenheit_to_celsius

    def test_celsius_to_fahrenheit():
        assert celsius_to_fahrenheit(0) == 32
        assert celsius_to_fahrenheit(100) == 212

    def test_fahrenheit_to_celsius():
        assert fahrenheit_to_celsius(32) == 0
    ''')
    write(ISSUES / "temperature_conversion_bug.md", '''
    # Bug: Celsius conversion subtracts instead of adding offset

    `celsius_to_fahrenheit(0)` should be `32`, and `celsius_to_fahrenheit(100)` should be `212`.
    The current conversion uses the wrong sign for the Fahrenheit offset.
    ''')
    init_repo(repo)
    return task("temperature_conversion_bug", "temperature_conversion_bug", "temperature_conversion_bug.md")


def password_length_bug() -> dict:
    repo = BASE / "password_length_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "passwords.py", '''
    def is_strong_password(password: str, min_length: int = 8) -> bool:
        """A strong password has at least min_length characters and one digit."""
        has_digit = any(ch.isdigit() for ch in password)
        return len(password) > min_length and has_digit
    ''')
    write(repo / "tests" / "test_passwords.py", '''
    from src.passwords import is_strong_password

    def test_min_length_is_allowed():
        assert is_strong_password("abcde1gh") is True

    def test_too_short_is_rejected():
        assert is_strong_password("abc1") is False

    def test_missing_digit_is_rejected():
        assert is_strong_password("abcdefgh") is False
    ''')
    write(ISSUES / "password_length_bug.md", '''
    # Bug: password validator rejects passwords at the minimum length

    `is_strong_password("abcde1gh")` has exactly 8 characters and a digit, so it should be accepted.
    The function currently requires the length to be greater than the minimum instead of at least the minimum.
    ''')
    init_repo(repo)
    return task("password_length_bug", "password_length_bug", "password_length_bug.md")


def unique_order_bug() -> dict:
    repo = BASE / "unique_order_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "lists.py", '''
    def unique_preserve_order(items: list[str]) -> list[str]:
        """Return unique items while preserving first-seen order."""
        return sorted(set(items))
    ''')
    write(repo / "tests" / "test_lists.py", '''
    from src.lists import unique_preserve_order

    def test_preserves_first_seen_order():
        assert unique_preserve_order(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]

    def test_empty_list():
        assert unique_preserve_order([]) == []
    ''')
    write(ISSUES / "unique_order_bug.md", '''
    # Bug: unique list helper sorts items instead of preserving order

    `unique_preserve_order(["b", "a", "b", "c", "a"])` should return `["b", "a", "c"]`.
    The function should keep the first occurrence order.
    ''')
    init_repo(repo)
    return task("unique_order_bug", "unique_order_bug", "unique_order_bug.md")


def bank_withdraw_bug() -> dict:
    repo = BASE / "bank_withdraw_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "account.py", '''
    class Account:
        def __init__(self, balance: float = 0):
            self.balance = balance

        def withdraw(self, amount: float) -> float:
            """Withdraw amount and return the new balance."""
            if amount <= 0:
                raise ValueError("amount must be positive")
            if self.balance - amount > 0:
                self.balance -= amount
                return self.balance
            raise ValueError("insufficient funds")
    ''')
    write(repo / "tests" / "test_account.py", '''
    import pytest
    from src.account import Account

    def test_withdraw_can_empty_account():
        account = Account(50)
        assert account.withdraw(50) == 0
        assert account.balance == 0

    def test_withdraw_rejects_overdraft():
        account = Account(50)
        with pytest.raises(ValueError):
            account.withdraw(51)
    ''')
    write(ISSUES / "bank_withdraw_bug.md", '''
    # Bug: withdrawing the full balance is incorrectly rejected

    An account with balance 50 should allow withdrawing 50 and leave balance 0.
    The overdraft check should reject negative balances, not zero balances.
    ''')
    init_repo(repo)
    return task("bank_withdraw_bug", "bank_withdraw_bug", "bank_withdraw_bug.md")


def leap_year_bug() -> dict:
    repo = BASE / "leap_year_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "dates.py", '''
    def is_leap_year(year: int) -> bool:
        """Return whether year is a leap year in the Gregorian calendar."""
        if year % 100 == 0:
            return False
        return year % 4 == 0
    ''')
    write(repo / "tests" / "test_dates.py", '''
    from src.dates import is_leap_year

    def test_regular_leap_year():
        assert is_leap_year(2024) is True

    def test_century_not_leap():
        assert is_leap_year(1900) is False

    def test_century_divisible_by_400_is_leap():
        assert is_leap_year(2000) is True
    ''')
    write(ISSUES / "leap_year_bug.md", '''
    # Bug: leap-year logic rejects years divisible by 400

    In the Gregorian calendar, years divisible by 400 are leap years.
    `is_leap_year(2000)` should return True, while `is_leap_year(1900)` should return False.
    ''')
    init_repo(repo)
    return task("leap_year_bug", "leap_year_bug", "leap_year_bug.md")


def text_truncate_bug() -> dict:
    repo = BASE / "text_truncate_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "text_utils.py", '''
    def truncate(text: str, max_length: int) -> str:
        """Return text shortened to max_length characters, using ... when shortened."""
        if max_length < 3:
            raise ValueError("max_length must be at least 3")
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    ''')
    write(repo / "tests" / "test_text_utils.py", '''
    import pytest
    from src.text_utils import truncate

    def test_truncate_keeps_total_length_under_limit():
        assert truncate("abcdefghij", 7) == "abcd..."
        assert len(truncate("abcdefghij", 7)) == 7

    def test_short_text_unchanged():
        assert truncate("abc", 7) == "abc"

    def test_min_length():
        with pytest.raises(ValueError):
            truncate("abcdef", 2)
    ''')
    write(ISSUES / "text_truncate_bug.md", '''
    # Bug: truncate returns strings longer than the requested maximum length

    `truncate("abcdefghij", 7)` should return `"abcd..."` with total length 7.
    The current function appends the ellipsis after taking `max_length` characters.
    ''')
    init_repo(repo)
    return task("text_truncate_bug", "text_truncate_bug", "text_truncate_bug.md")


def filename_extension_bug() -> dict:
    repo = BASE / "filename_extension_bug"
    shutil.rmtree(repo, ignore_errors=True)
    write(repo / "src" / "files.py", '''
    def get_extension(filename: str) -> str:
        """Return the file extension without the dot."""
        if "." not in filename:
            return ""
        return filename.split(".")[0]
    ''')
    write(repo / "tests" / "test_files.py", '''
    from src.files import get_extension

    def test_get_extension():
        assert get_extension("report.pdf") == "pdf"
        assert get_extension("archive.tar.gz") == "gz"

    def test_no_extension():
        assert get_extension("README") == ""
    ''')
    write(ISSUES / "filename_extension_bug.md", '''
    # Bug: file extension helper returns the name prefix

    `get_extension("report.pdf")` should return `"pdf"`, and `get_extension("archive.tar.gz")` should return `"gz"`.
    The helper currently returns the part before the first dot.
    ''')
    init_repo(repo)
    return task("filename_extension_bug", "filename_extension_bug", "filename_extension_bug.md")


def main() -> None:
    BASE.mkdir(exist_ok=True)
    ISSUES.mkdir(parents=True, exist_ok=True)
    BENCH.mkdir(exist_ok=True)
    tasks = [
        calculator_divide_bug(),
        string_slug_bug(),
        cart_discount_bug(),
        stats_average_bug(),
        temperature_conversion_bug(),
        password_length_bug(),
        unique_order_bug(),
        bank_withdraw_bug(),
        leap_year_bug(),
        text_truncate_bug(),
        filename_extension_bug(),
    ]
    # Keep first ten for the required benchmark. The extra task is useful for quick extension.
    tasks_10 = tasks[:10]
    (BENCH / "demo_suite_10.json").write_text(json.dumps(tasks_10, indent=2), encoding="utf-8")
    (BENCH / "demo_suite.json").write_text(json.dumps(tasks_10, indent=2), encoding="utf-8")
    print(f"Created {len(tasks_10)} demo tasks")
    print(f"Benchmark file: {BENCH / 'demo_suite_10.json'}")


if __name__ == "__main__":
    main()
