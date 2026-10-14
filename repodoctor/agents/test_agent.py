from __future__ import annotations

from repodoctor.models import TestResult
from repodoctor.tools.test_runner import TestRunner


class TestAgent:
    def __init__(self, runner: TestRunner):
        self.runner = runner

    def run_tests(self) -> TestResult:
        return self.runner.run()
