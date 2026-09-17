# Manual diagnostics

These scripts are operator-run checks, not automated tests. They may contact the
ASU AI API or external job portals and can consume quota or take time.

Run them from the repository root:

```bash
python scripts/diagnostics/check_asu_query.py
python scripts/diagnostics/check_asu_embeddings.py
python scripts/diagnostics/check_scraper.py Tempe
```

The ASU checks load `ASU_AI_API_KEY` from the process environment or the local
`.env` file. They report only configuration names and validation results; they
never print the API key or embedding contents.

Automated, network-free tests remain under `tests/` and run with:

```bash
python -m pytest
```
