# RepoDoctor GitHub Autopilot Guide

This version adds a full `repodoctor autopilot` command.

## What autopilot does

You provide a GitHub repository URL. RepoDoctor then:

1. Clones the repository into `runs/autopilot_<timestamp>/source_repo`.
2. Detects the project type and likely test command.
3. Writes `.repodoctor_auto_test.py`, a portable test wrapper.
4. If you provide an issue or GitHub issue URL, it uses that as repair context.
5. If you do not provide an issue, it runs the detected tests.
6. If tests fail, it creates an issue automatically from the failing test log.
7. Runs the full RepoDoctor repair loop.
8. Saves `autopilot_summary.md`, `autopilot_summary.json`, and the normal repair report.

## Important limitation

If the repository tests already pass and you do not provide an issue, RepoDoctor will stop with:

```text
no_failing_tests_no_issue
```

This is correct behavior. RepoDoctor needs either:

- a failing test suite, or
- an issue / issue URL describing what should be fixed.

It should not invent bugs in a healthy repository.

## Local test using generated demo repo

```powershell
python scripts/create_demo_suite.py
repodoctor autopilot --github-url demo_repos/calculator_bug --provider mock --max-iterations 3
```

This tests the automation flow without internet.

## Run on a public GitHub repo with Gemini

```powershell
$env:GEMINI_API_KEY="your_key_here"
repodoctor autopilot --github-url https://github.com/YOUR_USERNAME/YOUR_REPO --provider gemini --model gemini-2.5-flash-lite --max-iterations 5
```

## Run on a public GitHub repo with Docker sandbox

For real public GitHub repos, use `--docker-network bridge` when dependencies must be installed.

```powershell
$env:GEMINI_API_KEY="your_key_here"
repodoctor autopilot --github-url https://github.com/YOUR_USERNAME/YOUR_REPO --provider gemini --model gemini-2.5-flash-lite --max-iterations 5 --test-runner docker --docker-image python:3.11-slim --docker-network bridge
```

Use `--docker-network none` only when the repo does not need dependency downloads.

## Run with a GitHub issue URL

```powershell
$env:GEMINI_API_KEY="your_key_here"
repodoctor autopilot --github-url https://github.com/OWNER/REPO --issue-url https://github.com/OWNER/REPO/issues/123 --provider gemini --model gemini-2.5-flash-lite --max-iterations 5
```

## Run with your own issue text file

```powershell
repodoctor autopilot --github-url https://github.com/OWNER/REPO --issue examples/real_issues/my_bug.md --provider gemini --model gemini-2.5-flash-lite --max-iterations 5
```

## Outputs

After each autopilot run, check:

```text
runs/autopilot_<timestamp>/autopilot_summary.md
runs/autopilot_<timestamp>/autopilot_summary.json
runs/autopilot_<timestamp>/repairs/<timestamp>/report.md
runs/autopilot_<timestamp>/repairs/<timestamp>/report.json
```

## Dashboard

```powershell
streamlit run dashboard/app.py
```

Open the **GitHub autopilot** tab.
