# Documentation

This directory is the single home for maintained project documentation. The root [README](../README.md) remains the short repository landing page.

## Guides

| Document | Purpose |
|---|---|
| [Setup](setup.md) | Local installation, environment variables, Streamlit deployment, and troubleshooting |
| [Architecture](architecture.md) | Active runtime components, data flow, scoring, caching, and API usage |
| [Diagnostics](diagnostics.md) | Manual ASU API and scraper checks that may use external services |

## Source of truth

- Runtime behavior and defaults come from `config.py` and the application code.
- `.env.example` is the canonical configuration template.
- Markdown files in this directory are the maintained documentation.
- `archive/` is for local historical snapshots only; archived files are not authoritative.

When behavior changes, update the relevant guide in the same pull request.
