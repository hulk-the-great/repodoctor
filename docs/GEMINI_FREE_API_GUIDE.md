# Gemini Free API Guide for RepoDoctor

Use this guide when your laptop cannot run a local LLM.

## Recommended provider

```text
Provider: gemini
Default model: gemini-2.5-flash-lite
Stronger model: gemini-2.5-flash
```

## Windows setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e . pytest
$env:GEMINI_API_KEY="your_gemini_api_key_here"
python scripts/test_gemini_connection.py
```

## Run one task

```powershell
python scripts/create_demo_suite.py
repodoctor run --repo demo_repos/calculator_bug --issue examples/issues/calculator_divide_bug.md --tests "python -m pytest -q" --provider gemini --model gemini-2.5-flash-lite --max-iterations 3
```

## Run benchmark

```powershell
python scripts/evaluate_demo_suite.py --provider gemini --model gemini-2.5-flash-lite --max-iterations 3
```

## If you get rate limit errors

Use fewer tasks, reduce max iterations, or wait and retry later.

## If the patch fails to apply

Open the latest `runs/.../report.md`. The common reason is:

```text
old text not found exactly
```

This means the model found the right idea but did not copy the exact old text. The next upgrade is AST-based editing or unified-diff patch application.
