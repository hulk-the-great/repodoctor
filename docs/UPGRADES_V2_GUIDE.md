# RepoDoctor V2 Upgrade Guide

This version adds the four major upgrades requested:

## Upgrade 1: PatchCriticAgent

File: `repodoctor/agents/patch_critic_agent.py`

The critic checks each LLM patch before execution. It rejects:

- empty patches
- unsafe paths
- edits to test files
- ambiguous old text that appears multiple times
- old text that cannot be found
- replacements that delete too much code
- likely hard-coded test fixes

This prevents RepoDoctor from blindly applying LLM patches.

## Upgrade 2: AST-based code indexing

File: `repodoctor/tools/indexer.py`

The code index now parses Python files using `ast` and creates chunks for:

- functions
- async functions
- classes
- fallback line chunks

The retrieval table now shows chunk type and symbol name.

## Upgrade 4: 10 repair tasks

File: `scripts/create_demo_suite.py`

Run:

```powershell
python scripts/create_demo_suite.py
```

It creates `benchmarks/demo_suite_10.json` and ten local broken repositories.

## Upgrade 5: Failure analysis

Files:

- `repodoctor/analysis/failure_analysis.py`
- `scripts/evaluate_demo_suite.py`
- `scripts/analyze_eval_results.py`

Every benchmark now produces:

```text
summary.csv
summary.json
failure_analysis.md
```

Use the failure analysis in your GitHub README and MS project explanation.
