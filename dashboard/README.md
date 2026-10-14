# RepoDoctor Dashboard

Run the dashboard from the project root:

```powershell
streamlit run dashboard/app.py
```

The dashboard reads files from `runs/`, including:

- single-run `report.json` files
- benchmark `summary.json` files
- benchmark `failure_analysis.md` files

Run at least one RepoDoctor task before opening the dashboard.
