from __future__ import annotations

import json

from repodoctor.llm.base import BaseLLM


def _j(data: dict) -> str:
    return json.dumps(data, indent=2)


class MockLLM(BaseLLM):
    """Deterministic provider for local/offline pipeline validation.

    It is intentionally simple and only knows the bundled demo benchmark tasks.
    Use Gemini for real repositories. Mock mode is useful for verifying that
    the orchestrator, AST indexer, critic, editor, tests, reports, and benchmark
    analysis work without spending API calls.
    """

    def generate(self, prompt: str) -> str:
        lower = prompt.lower()

        if "structured issue summary" in lower:
            return self._issue_summary(lower)
        return self._patch(prompt, lower)

    def _issue_summary(self, lower: str) -> str:
        cases = [
            ("slugify", "wrong string separator", "src/strings.py", ["slugify uses underscores instead of hyphens"]),
            ("discount", "incorrect percentage calculation", "src/cart.py", ["apply_discount returns discount amount instead of final price"]),
            ("average", "incorrect mean calculation", "src/stats_utils.py", ["average returns sum instead of mean"]),
            ("fahrenheit", "wrong temperature conversion", "src/temperature.py", ["celsius_to_fahrenheit uses wrong offset sign"]),
            ("password", "off-by-one validation", "src/passwords.py", ["minimum length is rejected"]),
            ("unique", "order preservation bug", "src/lists.py", ["unique_preserve_order sorts items"]),
            ("withdraw", "boundary condition bug", "src/account.py", ["full balance withdrawal is rejected"]),
            ("leap", "calendar rule bug", "src/dates.py", ["year divisible by 400 is rejected"]),
            ("truncate", "length constraint bug", "src/text_utils.py", ["truncate result exceeds max length"]),
            ("extension", "wrong file extension parsing", "src/files.py", ["get_extension returns prefix instead of suffix"]),
        ]
        for key, bug_type, likely, symptoms in cases:
            if key in lower:
                return _j(
                    {
                        "bug_type": bug_type,
                        "symptoms": symptoms,
                        "expected_behavior": "Fix the root cause described in the issue and make pytest pass.",
                        "likely_files": [likely],
                        "test_focus": ["failing pytest assertions"],
                    }
                )
        return _j(
            {
                "bug_type": "incorrect arithmetic operation",
                "symptoms": ["divide returns multiplication result"],
                "expected_behavior": "divide(a, b) should return a / b",
                "likely_files": ["src/calculator.py"],
                "test_focus": ["test_divide"],
            }
        )

    def _patch(self, prompt: str, lower: str) -> str:
        if "src/calculator.py" in prompt and "def divide" in prompt:
            return _j(
                {
                    "summary": "Fix divide so it performs division instead of multiplication.",
                    "confidence": 0.99,
                    "edits": [
                        {
                            "path": "src/calculator.py",
                            "old": 'def divide(a: float, b: float) -> float:\n    """Return a divided by b."""\n    if b == 0:\n        raise ZeroDivisionError("Cannot divide by zero")\n    return a * b\n',
                            "new": 'def divide(a: float, b: float) -> float:\n    """Return a divided by b."""\n    if b == 0:\n        raise ZeroDivisionError("Cannot divide by zero")\n    return a / b\n',
                        }
                    ],
                }
            )

        if "src/strings.py" in prompt and "slugify" in lower:
            return _j(
                {
                    "summary": "Fix slugify so it uses hyphens instead of underscores.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/strings.py",
                            "old": 'def slugify(text: str) -> str:\n    """Convert text into a lowercase URL slug."""\n    text = text.strip().lower()\n    text = re.sub(r"[^a-z0-9]+", "_", text)\n    return text.strip("_")\n',
                            "new": 'def slugify(text: str) -> str:\n    """Convert text into a lowercase URL slug."""\n    text = text.strip().lower()\n    text = re.sub(r"[^a-z0-9]+", "-", text)\n    return text.strip("-")\n',
                        }
                    ],
                }
            )

        if "src/cart.py" in prompt and "apply_discount" in lower:
            return _j(
                {
                    "summary": "Fix apply_discount so it returns final price after subtracting the discount.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/cart.py",
                            "old": 'def apply_discount(total: float, discount_percent: float) -> float:\n    """Return total after applying percentage discount."""\n    if discount_percent < 0 or discount_percent > 100:\n        raise ValueError("discount_percent must be between 0 and 100")\n    return total * discount_percent / 100\n',
                            "new": 'def apply_discount(total: float, discount_percent: float) -> float:\n    """Return total after applying percentage discount."""\n    if discount_percent < 0 or discount_percent > 100:\n        raise ValueError("discount_percent must be between 0 and 100")\n    return total * (1 - discount_percent / 100)\n',
                        }
                    ],
                }
            )

        if "src/stats_utils.py" in prompt and "average" in lower:
            return _j(
                {
                    "summary": "Fix average by dividing the sum by the number of values.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/stats_utils.py",
                            "old": 'def average(values: list[float]) -> float:\n    """Return the arithmetic mean of a non-empty list."""\n    if not values:\n        raise ValueError("values must not be empty")\n    return sum(values)\n',
                            "new": 'def average(values: list[float]) -> float:\n    """Return the arithmetic mean of a non-empty list."""\n    if not values:\n        raise ValueError("values must not be empty")\n    return sum(values) / len(values)\n',
                        }
                    ],
                }
            )

        if "src/temperature.py" in prompt and "celsius_to_fahrenheit" in lower:
            return _j(
                {
                    "summary": "Fix Celsius to Fahrenheit conversion by adding 32.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/temperature.py",
                            "old": 'def celsius_to_fahrenheit(celsius: float) -> float:\n    """Convert Celsius to Fahrenheit."""\n    return celsius * 9 / 5 - 32\n',
                            "new": 'def celsius_to_fahrenheit(celsius: float) -> float:\n    """Convert Celsius to Fahrenheit."""\n    return celsius * 9 / 5 + 32\n',
                        }
                    ],
                }
            )

        if "src/passwords.py" in prompt and "is_strong_password" in lower:
            return _j(
                {
                    "summary": "Fix minimum password length check to allow exactly min_length characters.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/passwords.py",
                            "old": 'def is_strong_password(password: str, min_length: int = 8) -> bool:\n    """A strong password has at least min_length characters and one digit."""\n    has_digit = any(ch.isdigit() for ch in password)\n    return len(password) > min_length and has_digit\n',
                            "new": 'def is_strong_password(password: str, min_length: int = 8) -> bool:\n    """A strong password has at least min_length characters and one digit."""\n    has_digit = any(ch.isdigit() for ch in password)\n    return len(password) >= min_length and has_digit\n',
                        }
                    ],
                }
            )

        if "src/lists.py" in prompt and "unique_preserve_order" in lower:
            return _j(
                {
                    "summary": "Fix unique_preserve_order by using a seen set while preserving first-seen order.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/lists.py",
                            "old": 'def unique_preserve_order(items: list[str]) -> list[str]:\n    """Return unique items while preserving first-seen order."""\n    return sorted(set(items))\n',
                            "new": 'def unique_preserve_order(items: list[str]) -> list[str]:\n    """Return unique items while preserving first-seen order."""\n    seen = set()\n    result = []\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result\n',
                        }
                    ],
                }
            )

        if "src/account.py" in prompt and "withdraw" in lower:
            return _j(
                {
                    "summary": "Fix withdrawal boundary check so withdrawing the full balance is allowed.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/account.py",
                            "old": '    def withdraw(self, amount: float) -> float:\n        """Withdraw amount and return the new balance."""\n        if amount <= 0:\n            raise ValueError("amount must be positive")\n        if self.balance - amount > 0:\n            self.balance -= amount\n            return self.balance\n        raise ValueError("insufficient funds")\n',
                            "new": '    def withdraw(self, amount: float) -> float:\n        """Withdraw amount and return the new balance."""\n        if amount <= 0:\n            raise ValueError("amount must be positive")\n        if self.balance - amount >= 0:\n            self.balance -= amount\n            return self.balance\n        raise ValueError("insufficient funds")\n',
                        }
                    ],
                }
            )

        if "src/dates.py" in prompt and "is_leap_year" in lower:
            return _j(
                {
                    "summary": "Fix Gregorian leap-year logic for years divisible by 400.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/dates.py",
                            "old": 'def is_leap_year(year: int) -> bool:\n    """Return whether year is a leap year in the Gregorian calendar."""\n    if year % 100 == 0:\n        return False\n    return year % 4 == 0\n',
                            "new": 'def is_leap_year(year: int) -> bool:\n    """Return whether year is a leap year in the Gregorian calendar."""\n    if year % 400 == 0:\n        return True\n    if year % 100 == 0:\n        return False\n    return year % 4 == 0\n',
                        }
                    ],
                }
            )

        if "src/text_utils.py" in prompt and "truncate" in lower:
            return _j(
                {
                    "summary": "Fix truncate so the ellipsis is included within max_length.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/text_utils.py",
                            "old": 'def truncate(text: str, max_length: int) -> str:\n    """Return text shortened to max_length characters, using ... when shortened."""\n    if max_length < 3:\n        raise ValueError("max_length must be at least 3")\n    if len(text) <= max_length:\n        return text\n    return text[:max_length] + "..."\n',
                            "new": 'def truncate(text: str, max_length: int) -> str:\n    """Return text shortened to max_length characters, using ... when shortened."""\n    if max_length < 3:\n        raise ValueError("max_length must be at least 3")\n    if len(text) <= max_length:\n        return text\n    return text[: max_length - 3] + "..."\n',
                        }
                    ],
                }
            )

        if "src/files.py" in prompt and "get_extension" in lower:
            return _j(
                {
                    "summary": "Fix get_extension so it returns the suffix after the final dot.",
                    "confidence": 0.98,
                    "edits": [
                        {
                            "path": "src/files.py",
                            "old": 'def get_extension(filename: str) -> str:\n    """Return the file extension without the dot."""\n    if "." not in filename:\n        return ""\n    return filename.split(".")[0]\n',
                            "new": 'def get_extension(filename: str) -> str:\n    """Return the file extension without the dot."""\n    if "." not in filename:\n        return ""\n    return filename.rsplit(".", 1)[1]\n',
                        }
                    ],
                }
            )

        return _j({"summary": "No deterministic mock edit available for this issue.", "confidence": 0.0, "edits": []})
