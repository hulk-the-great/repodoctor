# RepoDoctor

**An agentic, test-verified repair system for Python repositories.**

RepoDoctor takes a GitHub-style bug report or a failing test, locates relevant code, generates a candidate fix with an LLM, and verifies the change against the repository's tests. It combines AST-aware code retrieval with deterministic patch checks, exact-match file editing, rollback, and structured run reports.

It can work with a local repository or start directly from a GitHub URL. Test execution can run locally or inside a Docker container.

## Features

- **GitHub autopilot:** Clone a repository, identify a likely test command, and start a repair run from an issue URL or failing tests.
- **AST-aware retrieval:** Index Python functions, classes, and text chunks to find code relevant to a reported bug.
- **LLM-generated patches:** Generate structured, machine-applicable edits using Gemini; local LLM mode is available through Ollama.
- **PatchCriticAgent:** Reject candidate edits that are unsafe, ambiguous, overly broad, or attempt to modify tests.
- **Safe edits and rollback:** Apply exact replacements only when the original text has a unique match; revert unsuccessful attempts.
- **Test-based verification:** Run the configured test command and accept a patch only when verification passes.
- **Docker test execution:** Optionally run test commands in a container rather than directly on the host.
- **Evaluation and reporting:** Run a 10-task demo benchmark and inspect results, failure categories, diffs, and logs in generated reports or a Streamlit dashboard.

## How it works

```text
Repository + issue (or detected test failure)
                    |
                    v
           IssueAgent
       Structure the bug report
                    |
                    v
       CodebaseIndex + RetrievalAgent
       Find relevant Python code
                    |
                    v
              PatchAgent
       Generate candidate JSON edits
                    |
                    v
           PatchCriticAgent
       Check patch safety and scope
                    |
                    v
            SafeFileEditor
       Apply unambiguous exact edits
                    |
                    v
       TestAgent / DockerTestRunner
              Run tests
                    |
           +--------+---------+
           |                  |
        Tests pass         Tests fail
           |                  |
           v                  v
      VerifierAgent       Roll back and
       Accept patch       retry if allowed
           |
           v
        Run reports
```

The **Orchestrator** coordinates the workflow. The **FailureAnalyzer** aggregates evaluation results and categorizes unsuccessful attempts.

## Requirements

- Python 3.10+
- Git
- `pytest` and any test dependencies required by the target repository
- A Gemini API key for Gemini-powered patch generation (not needed for mock mode)
- Optional: Ollama for a local LLM provider
- Optional: Docker for containerized test execution

## Installation

Open a terminal in the extracted or cloned RepoDoctor project directory.

**Windows (PowerShell)**

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e . pytest google-genai streamlit
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pytest google-genai streamlit
```

The editable installation makes the `repodoctor` command available in the active environment.

## Quick start: local demo

The included benchmark generator creates 10 small repositories with known defects and corresponding issue descriptions.

```bash
python scripts/create_demo_suite.py
```

This generates files under `demo_repos/`, `examples/issues/`, and `benchmarks/demo_suite_10.json`.

Run the deterministic benchmark without an API key:

```bash
python scripts/evaluate_demo_suite.py --provider mock --max-iterations 3
```

`mock` mode is intended for reproducible workflow checks. It does **not** measure how well a live LLM repairs previously unseen issues. The demo suite is designed for a 10/10 result in mock mode, but actual outcomes should be taken from the generated reports.

To run a smaller batch:

```bash
python scripts/evaluate_demo_suite.py --provider mock --max-iterations 3 --offset 0 --limit 2
```

## Repair a repository with Gemini

Set your Gemini API key in the terminal session.

**Windows (PowerShell)**

```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

**macOS / Linux**

```bash
export GEMINI_API_KEY="your_api_key_here"
```

Check the connection:

```bash
python scripts/test_gemini_connection.py
```

After generating the demo suite, run a single repair:

```bash
repodoctor run --repo demo_repos/calculator_bug --issue examples/issues/calculator_divide_bug.md --tests "python run_tests.py" --provider gemini --model gemini-2.5-flash-lite --max-iterations 5
```

Or evaluate all 10 demo tasks with Gemini:

```bash
python scripts/evaluate_demo_suite.py --provider gemini --model gemini-2.5-flash-lite --max-iterations 5
```

For API quota management, the evaluator supports `--offset` and `--limit`:

```bash
python scripts/evaluate_demo_suite.py --provider gemini --model gemini-2.5-flash-lite --max-iterations 5 --offset 0 --limit 2
```

Gemini results can vary between runs. The chosen model also needs to be available to your account and API configuration.

## GitHub URL autopilot

Autopilot reduces the manual setup needed for a GitHub repository:

```bash
repodoctor autopilot --github-url https://github.com/OWNER/REPO --provider gemini --model gemini-2.5-flash-lite --max-iterations 5
```

It clones the repository, detects the project type and a likely test command, creates a `.repodoctor_auto_test.py` wrapper, and runs the normal repair workflow. If no issue is supplied, it first looks for a test failure from which to build an issue description.

To repair a specific GitHub issue:

```bash
repodoctor autopilot --github-url https://github.com/OWNER/REPO --issue-url https://github.com/OWNER/REPO/issues/123 --provider gemini --model gemini-2.5-flash-lite --max-iterations 5
```

**Expected stopping behavior:** If no issue is provided and the detected tests already pass, autopilot stops with `no_failing_tests_no_issue` instead of inventing a bug.

See [`docs/GITHUB_AUTOPILOT_GUIDE.md`](docs/GITHUB_AUTOPILOT_GUIDE.md) for more details.

## Run against a local repository

You can also choose the repository and issue description explicitly:

```bash
repodoctor run --repo path/to/repository --issue path/to/issue.md --tests "python -m pytest" --provider gemini --model gemini-2.5-flash-lite --max-iterations 5
```

Replace the paths and test command with ones appropriate for your project. RepoDoctor works on a copy of the target repository under `runs/` rather than editing the original checkout.

## Docker test execution

For repositories you did not write yourself, prefer an isolated test environment.

Check Docker connectivity:

```bash
python scripts/test_docker_connection.py
```

Run a demo task with containerized tests:

```bash
repodoctor run --repo demo_repos/calculator_bug --issue examples/issues/calculator_divide_bug.md --tests "python run_tests.py" --provider mock --max-iterations 3 --test-runner docker --docker-image python:3.11-slim --docker-network none
```

Run the full mock benchmark in Docker:

```bash
python scripts/evaluate_demo_suite.py --provider mock --max-iterations 3 --test-runner docker --docker-image python:3.11-slim --docker-network none
```

`--docker-network none` disables container networking and is preferable when dependencies are already installed in the image. Repositories that require dependency downloads may need a prepared image or `--docker-network bridge`; enabling network access reduces isolation.

## Reports and dashboard

Evaluation artifacts are written to a timestamped directory under `runs/`:

```text
runs/
└── eval_<timestamp>/
    ├── summary.csv
    ├── summary.json
    ├── failure_analysis.md
    └── <task-run-directories>/
        └── report.md
```

The failure analysis includes task counts, resolved tasks, resolution rate, average iterations, per-task outcomes, and failure categories. You can regenerate it with:

```bash
python scripts/analyze_eval_results.py runs/eval_<timestamp>
```

After a run, launch the Streamlit dashboard:

```bash
streamlit run dashboard/app.py
```

The dashboard presents evaluation summaries, individual run reports, PatchCritic feedback, test logs, and final diffs.

## Limitations and security

- **Tests are the acceptance signal, not a proof of correctness.** A passing test suite does not guarantee that every bug is fixed.
- **Autopilot relies on test discovery.** It may not identify the correct command or failure for every repository.
- **Patch application is intentionally conservative.** Ambiguous exact-text replacements and some larger refactors may be rejected.
- **LLM results are not deterministic.** A cloud model may produce invalid or unsuccessful patches, and API limits may interrupt a run.
- **Executing tests carries risk.** A target repository can run arbitrary code through its test commands; use repositories you trust and prefer an appropriately hardened sandbox for unknown code.
- **Protect source code and secrets.** Do not commit API keys, `.env` files, virtual environments, or generated run artifacts. Do not send private or proprietary repository content to a cloud model without authorization.

## Project scope

RepoDoctor is a research and engineering prototype focused on **Python repository repair with explicit test verification**. Its demo benchmark demonstrates the repair pipeline; broader claims about real-world resolution rates require evaluation on independent repositories and issues.
