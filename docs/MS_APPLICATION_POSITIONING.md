# How to Position RepoDoctor in MS Applications

Use this project to signal that you can build serious AI systems, not just demos.

## One-line description

RepoDoctor is a test-verified autonomous software engineering agent that repairs real code repositories from issue descriptions by retrieving relevant code, generating patches, executing tests, and iteratively refining fixes.

## Strong SOP paragraph

One of my independent projects, RepoDoctor, explores autonomous software engineering agents for test-verified bug repair. The system takes a repository and an issue description as input, indexes the codebase, retrieves relevant files, proposes structured edits, executes the repository test suite, and iteratively repairs failures based on test logs. This project strengthened my interest in building AI systems that combine language models with program analysis, retrieval, tool use, and verification, rather than relying on generation alone.

## Resume bullet examples

- Built RepoDoctor, a multi-agent AI system for repository-level bug repair using code retrieval, patch generation, test execution, and iterative verification.
- Implemented agents for issue analysis, codebase indexing, relevant-file retrieval, JSON-based patch editing, test-log feedback, and verifier-based acceptance.
- Designed reproducible evaluation outputs including patch diffs, test logs, iteration reports, and failure cases for benchmark-style analysis.

## Evaluation plan

Start with small open-source Python repositories, then move toward SWE-bench Lite style examples.

Recommended metrics:

- Resolve Rate
- Test Pass Rate
- Patch Apply Rate
- Average Attempts
- Average Runtime
- Failure Category Breakdown

## Advanced extensions

- Add AST-based editing.
- Add Docker sandboxing.
- Add call graph retrieval.
- Add patch critic agent.
- Add PR creation.
- Add benchmark runner.
