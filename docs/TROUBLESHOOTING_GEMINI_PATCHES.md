# Troubleshooting Gemini patch failures

## Symptom

The first Gemini run may show something like:

```text
src/calculator.py: applied
Tests after patch: FAILED
src/calculator.py: old text not found exactly
```

## Why it happens

Gemini may generate an overly small replacement such as:

```json
{"old": "return a * b", "new": "return a / b"}
```

In the calculator demo, `return a * b` appears in both `multiply()` and `divide()`. A naive replacement can edit the first match, which damages `multiply()` instead of fixing `divide()`.

## Fix in this version

This version adds two safety changes:

1. RepoDoctor rejects ambiguous edits when the `old` text appears more than once.
2. RepoDoctor reverts failed patches before the next iteration, so later attempts start from a clean worktree.

If Gemini returns an ambiguous edit, the next iteration receives this feedback:

```text
EDIT FEEDBACK: src/calculator.py: old text is ambiguous; appears 2 times; include the full function/block in old text
```

This encourages the model to replace a larger exact block, such as the whole `divide()` function.
