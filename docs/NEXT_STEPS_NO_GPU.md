# Next Steps When You Cannot Run a Local LLM

Your laptop can still run RepoDoctor. The only part that needs a strong model is patch generation, and that can use a cloud API.

## Recommended path

1. Validate the full system locally using `--provider mock`.
2. Use Gemini API with `--provider gemini` for real patch generation.
3. Collect reports on demo repos and small public repos.
4. Add Docker sandboxing and AST-based editing.
5. Convert the results into a polished GitHub README and MS application project story.

## Commands

```powershell
python scripts/create_demo_suite.py
python scripts/evaluate_demo_suite.py --provider mock --max-iterations 2
$env:GEMINI_API_KEY="your_gemini_api_key_here"
python scripts/test_gemini_connection.py
python scripts/evaluate_demo_suite.py --provider gemini --model gemini-2.5-flash-lite --max-iterations 3
```

## Portfolio target

Collect at least 10 repair reports:

- 3 bundled demo tasks
- 3 bugs from your own older projects
- 4 bugs from small public repositories or cloned practice repos

Report metrics:

- Resolve Rate
- Patch Apply Rate
- Test Pass Rate
- Average Iterations
- Retrieval Accuracy
- Failure Type
