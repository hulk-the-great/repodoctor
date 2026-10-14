# RepoDoctor V3: Docker Sandbox and Dashboard Guide

This version adds two major upgrades:

1. Docker sandbox execution for tests
2. Streamlit dashboard for visual inspection of repair runs

## Is Docker free?

Docker Desktop is generally free for personal use, education, non-commercial open-source projects, and small businesses below Docker's stated employee/revenue limits. Larger commercial organizations may need a paid Docker subscription. Check Docker's current license terms before using it in a company environment.

## Why Docker sandboxing matters

Without Docker, RepoDoctor runs tests directly on your machine. With Docker, tests run inside a container, which gives a cleaner and safer execution environment.

RepoDoctor still modifies only the copied repository inside `runs/.../repo`, not your original repository.

## Install Docker on Windows

1. Install Docker Desktop for Windows.
2. Start Docker Desktop.
3. Wait until it says Docker is running.
4. Reopen PowerShell.
5. Test:

```powershell
docker version
python scripts/test_docker_connection.py
```

## Run one sandboxed repair

```powershell
python scripts/create_demo_suite.py
repodoctor run --repo demo_repos/calculator_bug --issue examples/issues/calculator_divide_bug.md --tests "python run_tests.py" --provider mock --max-iterations 3 --test-runner docker --docker-image python:3.11-slim --docker-network none
```

## Run a Docker benchmark

```powershell
python scripts/evaluate_demo_suite.py --provider mock --max-iterations 3 --test-runner docker --docker-image python:3.11-slim --docker-network none
```

## Gemini + Docker

```powershell
$env:GEMINI_API_KEY="your_key_here"
python scripts/evaluate_demo_suite.py --provider gemini --model gemini-2.5-flash-lite --max-iterations 5 --test-runner docker --docker-image python:3.11-slim --docker-network none --offset 0 --limit 2
```

Use batches with Gemini to avoid free-tier rate limits.

## Dashboard

Install dependencies through the project install:

```powershell
pip install -e .
```

Then run:

```powershell
streamlit run dashboard/app.py
```

The dashboard reads `runs/` and displays benchmark summaries, failure analysis, and individual repair reports.

## Custom Docker image

The default image is `python:3.11-slim`. The local demo suite works with it.

For real repositories, build a custom image:

```powershell
docker build -t repodoctor-python-sandbox -f .repodoctor/Dockerfile .
```

Then run:

```powershell
repodoctor run --repo path\to\repo --issue path\to\issue.md --tests "python -m pytest -q" --provider gemini --model gemini-2.5-flash-lite --test-runner docker --docker-image repodoctor-python-sandbox --docker-network none
```
