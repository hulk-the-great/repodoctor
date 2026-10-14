# RepoDoctor

RepoDoctor is a test-verified software engineering agent for repairing GitHub-style issues. It clones or copies a repository, indexes the codebase, retrieves relevant files, proposes minimal patches, runs tests, and iterates until the patch is accepted or the maximum repair budget is reached.

## Why this project matters

Many coding assistants can generate snippets, but real software maintenance requires repository-level understanding, localized editing, test execution, and failure recovery. RepoDoctor is designed as a complete agentic workflow for issue-to-patch repair.

## Architecture

```text
Issue Agent -> Retrieval Agent -> Patch Agent -> Test Agent -> Verifier Agent
       ^                                                       |
       |---------------- execution feedback loop --------------|
```

## Agents

- Issue Agent: extracts bug symptoms, expected behavior, and search terms.
- Retrieval Agent: finds the most relevant code chunks from the repository.
- Patch Agent: generates minimal structured edits.
- Test Agent: runs the repository test suite.
- Verifier Agent: accepts patches only when edits apply and tests pass.

## Running the demo

```bash
python scripts/create_demo_suite.py
python scripts/evaluate_demo_suite.py --provider mock
```

## Running with a cloud LLM

```bash
export OPENAI_API_KEY="your_key_here"
python scripts/evaluate_demo_suite.py --provider openai --model gpt-5.5 --max-iterations 3
```

On Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your_key_here"
python scripts/evaluate_demo_suite.py --provider openai --model gpt-5.5 --max-iterations 3
```

## Evaluation

Recommended metrics:

| Metric | Meaning |
|---|---|
| Resolve Rate | Percentage of issues where tests pass after patching |
| Patch Apply Rate | Percentage of generated edits that apply cleanly |
| Average Iterations | Number of repair loops required |
| Test Pass Rate | Whether repository tests pass after patching |
| Failure Category | Retrieval failure, bad edit, incomplete fix, test failure |

## MS application positioning

RepoDoctor demonstrates AI agents, software engineering, retrieval, code understanding, program repair, test-based verification, and benchmark-style evaluation.
