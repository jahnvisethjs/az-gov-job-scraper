# Setup, Configuration, and Deployment

## Prerequisites

- Python 3.10 or newer
- An ASU AIML API key

## Local installation

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` and copy the template with `cp .env.example .env`.

Add the ASU key to `.env`, then start the app:

```powershell
streamlit run streamlit_app.py
```

## Configuration

`.env.example` contains every supported deployment setting:

```dotenv
ASU_AI_ENABLED=true
ASU_AI_API_KEY=
ASU_AI_BASE_URL=https://api-main.aiml.asu.edu
ASU_AI_MODEL=claude-opus-4-7

ASU_AI_EMBEDDINGS_PROVIDER=openai
ASU_AI_EMBEDDINGS_MODEL=te3s
ASU_AI_EMBEDDINGS_DIMENSIONS=1024

JOB_CACHE_HOURS=6
CACHE_DIR=./data/cache
EMBEDDING_BATCH_WORKERS=2
DATABASE_URL=
```

`config.py` loads the repository-root `.env` without overriding variables already present in the process environment. This lets deployment secrets take precedence over local values.

Do not commit `.env`, `.streamlit/secrets.toml`, resumes, or API keys. These paths and uploaded PDF/DOCX files are ignored by Git.

## Streamlit Community Cloud

1. Deploy the repository with `streamlit_app.py` as the entry point.
2. Open the app's **Advanced settings** and add the following root-level secrets:

```toml
ASU_AI_ENABLED = "true"
ASU_AI_API_KEY = "your-key"
ASU_AI_BASE_URL = "https://api-main.aiml.asu.edu"
ASU_AI_MODEL = "claude-opus-4-7"
ASU_AI_EMBEDDINGS_PROVIDER = "openai"
ASU_AI_EMBEDDINGS_MODEL = "te3s"
ASU_AI_EMBEDDINGS_DIMENSIONS = "1024"
JOB_CACHE_HOURS = "6"
CACHE_DIR = "./data/cache"
EMBEDDING_BATCH_WORKERS = "2"
DATABASE_URL = "postgresql://user:password@host:5432/database"
```

Streamlit exposes root-level secrets as environment variables, which matches the configuration code. See Streamlit's [Community Cloud secrets guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) and [secrets management reference](https://docs.streamlit.io/develop/concepts/connections/secrets-management).

`DATABASE_URL` is optional for local development but recommended for deployment. When set, the app automatically creates PostgreSQL tables for city snapshots and reusable embedding vectors. Without it, job snapshots remain in local JSON files and vectors remain in local ChromaDB; those files may disappear when a hosted instance restarts.

## Scheduled catalog refresh

The `Refresh job catalog` GitHub Actions workflow refreshes and pre-indexes all supported cities every four hours. Add `ASU_AI_API_KEY` and `DATABASE_URL` as GitHub Actions repository secrets, then run the workflow manually once to verify the deployment. Scheduled workflows run from the repository's default branch, so merge the workflow there before relying on its schedule.

The same maintenance command can be run locally:

```powershell
python scripts/refresh_job_catalog.py
python scripts/refresh_job_catalog.py --city Phoenix --city Tempe
```

The command makes live portal and ASU AIML requests. With `DATABASE_URL` configured, refreshed listings and their job embeddings become available to all application instances.

The app calls the ASU AIML production base URL with a bearer token. ASU documents the supported query and embedding interfaces in its [OpenAI-compatible API guide](https://docs.aiml.asu.edu/openai-compatible).

## Verification

Run the local, network-free test suite:

```powershell
python -m pytest
```

For live service checks, follow [Manual diagnostics](diagnostics.md). Those commands may consume API quota or contact public job portals.

## Troubleshooting

- **Missing API key:** confirm `ASU_AI_API_KEY` is set in the root `.env` or deployment environment.
- **401 or 403 response:** verify that the ASU token is valid and authorized for the selected model.
- **Model request fails:** confirm `ASU_AI_MODEL=claude-opus-4-7` is available to the token.
- **Old job results:** run the catalog-refresh workflow, clear the configured store, or wait for `JOB_CACHE_HOURS` to expire.
- **Embedding errors:** keep the provider, model, and dimensions aligned as `openai`, `te3s`, and `1024` unless the ASU configuration is intentionally changed.
