# Project Handoff

Last updated: October 8, 2026

## Current state

- Repository: `az-gov-job-scraper`
- Active development branch: `asu-exp`
- Prior implementation commit: `359eae4`
- Commit message: `feat: add durable job refresh and cancellation`
- This revision adds the item 4/item 5 changes below on `asu-exp`, on top of
  `359eae4`. Hosted deployment and default-branch merge are not verified.
- The latest automated validation passed 84 tests, Python compilation, Git's
  diff check, and a Streamlit smoke test with zero page exceptions.
- This handoff file was created after that commit and is not included in
  `359eae4`.

The P1 and P2 implementation is ready for review and a pull request from
`asu-exp` into the default branch. The scheduled workflow will not run from its
schedule until the workflow is merged into the default branch.

## Local item 4/item 5 changes — October 8, 2026

This revision includes the following implementation and evaluation work:

- **Item 4 complete:** one private session resume embedding cache is passed
  through the UI, search service, matcher and RAG engine. Saved-results ranking
  and background refresh reuse the same vector. Profile/search/model changes
  invalidate it; same-input concurrent requests coalesce, and failed/cancelled
  generation or clearing during a request cannot populate the cache.
- **Item 5 evaluation tooling implemented:** shared runtime/evaluation scoring,
  a synthetic 6-profile/12-job/72-pair relevance fixture, ranking metrics,
  opt-in ASU feature collection, offline replay and a weight sweep.
- The network-free keyword diagnostic ran successfully. Live ASU feature
  collection reached the service after network approval but failed with a
  server HTTP error after provider retries. No real-model hybrid measurement
  was produced.
- Independent label review, representative held-out examples, and measured
  hybrid evaluation remain required for calibration. Runtime weights stay 70/30.
- Latest validation: **84 network-free tests passed**, Python compilation and
  Git diff checks passed, and Streamlit smoke testing had zero page exceptions.

See [docs/scoring-evaluation.md](docs/scoring-evaluation.md) for behavior,
baseline results, reproducible commands and the remaining evaluation work.

## What the application does

This is a Streamlit application that:

1. Accepts a PDF, DOCX, or TXT resume.
2. Extracts and structures the candidate's experience through the ASU AIML
   API.
3. Collects current jobs from 15 Arizona municipal and county portals.
4. Embeds jobs and the candidate profile through the ASU embeddings endpoint.
5. Ranks eligible jobs using semantic similarity and keyword overlap.
6. Generates resume-tailoring advice for a selected job on demand.

ASU AIML is the only active AI gateway. Text generation currently uses
`claude-opus-4-7`. Embeddings use `te3s` at 1,024 dimensions.

## Runtime architecture

```text
streamlit_app.py
  -> ui/sections.py
      -> services/resume_service.py
      -> services/job_search_service.py
          -> services/background_search.py
          -> rag/job_matcher.py
              -> utils/job_cache.py
                  -> storage/job_store.py
                      -> PostgreSQL when DATABASE_URL is set
                      -> atomic JSON files otherwise
              -> scrapers/neogov_scraper.py
              -> scrapers/peoplesoft_scraper.py
              -> rag/rag_engine.py
                  -> ASU embeddings
                  -> local ChromaDB query index
      -> services/tailoring_service.py
          -> ASU text-generation model
```

There is no agent framework in the running application.

For the complete maintained design, see [docs/architecture.md](docs/architecture.md).

## Search behavior

Search uses two passes:

```text
Read cached catalog -> rank and display saved results immediately
                    -> start live background refresh
                    -> publish each completed city's unranked listings
                    -> incrementally update embeddings
                    -> replace results with the final fresh ranking
```

The user can cancel a live refresh. Cancellation is cooperative and propagates
through the background manager, matcher, scrapers, and embedding batches.
Already completed city listings are retained and clearly shown as unranked.
An HTTP request already in progress may continue until its 30-second timeout.

## Scoring

The application does not use an LLM as the scoring judge. The score is:

```text
semantic_similarity = 1 - cosine_distance
keyword_score = matched_profile_keywords / total_profile_keywords
match_score = (0.70 * semantic_similarity + 0.30 * keyword_score) * 100
```

The score is a retrieval heuristic, not a calibrated probability of receiving
an interview or offer.

## Completed work

### Reliability and data identity

- Stable job IDs are derived from platform, city, and canonical source
  identity.
- Dismissal, deduplication, and tailoring-advice caches use stable IDs rather
  than job titles.
- User-controlled scraped fields are escaped before HTML rendering.
- Uploaded resumes and parsed candidate profiles remain in Streamlit session
  state and are not written to shared job storage.

### Incremental indexing

- Unchanged jobs reuse their existing embeddings.
- Only new or content-changed jobs call the embeddings API.
- Expired jobs are removed only for cities that refreshed successfully.
- Index mutations occur after cancellable embedding work finishes, preventing
  a cancelled search from leaving ChromaDB half-synchronized.
- Matching shared vectors can be restored from PostgreSQL into local ChromaDB.

### Responsive search

- Saved matches appear before live scraping finishes.
- The UI shows live phase, city, job-count, indexing, and matching progress.
- Completed-city partial listings appear during a refresh.
- The user can cancel a refresh without losing saved matches.
- Background work is bounded and no longer blocks ordinary Streamlit reruns.

### Scheduled refresh and durable storage

- `storage/job_store.py` provides PostgreSQL and local JSON implementations.
- PostgreSQL stores city snapshots and content-hash-keyed reusable embeddings.
- `.github/workflows/refresh-job-catalog.yml` refreshes the catalog every four
  hours once it is present on the default branch.
- `scripts/refresh_job_catalog.py` can perform the same maintenance locally.
- Scheduled refresh uses a catalog-only path and does not create a synthetic
  resume embedding or personalized ranking.

### Browser removal

- All NeoGov portals use direct `aiohttp` requests and HTML parsing.
- Phoenix uses direct `requests` calls against the server-rendered PeopleSoft
  list and `SiteId=10` Candidate Gateway detail pages.
- Playwright, Chromium installation, and deferred browser provisioning were
  removed from the code, requirements, workflow, and documentation.
- The live Phoenix verification returned 37 jobs. All 37 had descriptions and
  36 exposed separate qualification sections.
- Phoenix currently rejects the browser-like user-agent header tested during
  development with HTTP 403 but accepts the default Python `requests` client.
  Re-run the live scraper diagnostic if changing this adapter's HTTP headers.

### Cleanup already present in the codebase

- Legacy diagnostics are organized under `scripts/diagnostics/` and excluded
  from ordinary pytest collection.
- Documentation is consolidated under `docs/`.
- Streamlit UI responsibilities are split between `streamlit_app.py`, `ui/`,
  and `services/`.
- PDF and DOCX files, local secrets, caches, virtual environments, and local AI
  context are ignored by Git.

## Important files

| Area | File |
|---|---|
| Streamlit entry point | `streamlit_app.py` |
| UI workflow and partial results | `ui/sections.py` |
| Session state | `utils/session_manager.py` |
| Background tasks and cancellation | `services/background_search.py` |
| Sync/async search boundary | `services/job_search_service.py` |
| Search orchestration | `rag/job_matcher.py` |
| Incremental vector index and scoring | `rag/rag_engine.py` |
| ASU API integration | `rag/asu_ai_provider.py` |
| NeoGov collection | `scrapers/neogov_scraper.py` |
| Phoenix PeopleSoft collection | `scrapers/peoplesoft_scraper.py` |
| Durable job/vector storage | `storage/job_store.py` |
| Scheduled maintenance | `.github/workflows/refresh-job-catalog.yml` |
| Manual maintenance | `scripts/refresh_job_catalog.py` |
| Setup and deployment | `docs/setup.md` |
| Architecture and scoring | `docs/architecture.md` |

## Configuration and secrets

Supported settings are documented in `.env.example`. The important deployment
secrets are:

- `ASU_AI_API_KEY`
- `DATABASE_URL`

Never place their values in tracked files. Local development reads the ignored
root `.env`. Streamlit Cloud and GitHub Actions require their own separately
configured secret values.

A database password was previously pasted into a chat. It is not present in
the committed source, documentation, or tests, but it must be rotated before
production use. After rotation, update the ignored local `.env`, Streamlit
Cloud secrets, and GitHub Actions repository secrets.

The configured Supabase connection was tested successfully: the application
selected `PostgresJobStore`, initialized/read the intended schema, and found
zero city snapshots. The verification did not write catalog rows.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the required values in the ignored `.env`, then run:

```powershell
streamlit run streamlit_app.py
```

Playwright and Chromium are no longer required.

## Validation

Run the network-free suite:

```powershell
python -m pytest -q
python -m compileall -q .
```

Latest result:

```text
84 passed
Streamlit application exceptions: 0
Python compilation: passed
git diff --check: passed
```

Live commands contact external services and may consume ASU quota:

```powershell
python scripts/refresh_job_catalog.py --city Phoenix
python scripts/diagnostics/check_scraper.py Tempe
python scripts/diagnostics/check_asu_query.py
python scripts/diagnostics/check_asu_embeddings.py
```

## Deployment checklist

1. Rotate the previously exposed database password.
2. Configure the rotated `DATABASE_URL` and `ASU_AI_API_KEY` in Streamlit
   Cloud.
3. Configure the same two secrets in GitHub Actions.
4. Open and review a pull request from `asu-exp` into the default branch.
5. Merge the workflow into the default branch.
6. Manually run `Refresh job catalog` once and verify that PostgreSQL contains
   current city snapshots and reusable embeddings.
7. Deploy/restart Streamlit and confirm saved results appear before a live
   refresh completes.
8. Verify cancellation, partial listings, final ranking, application links,
   and tailoring advice in the deployed UI.

## Remaining limitations

- Background task state is process-local. Restarts lose active progress, and
  multiple app instances do not coordinate refreshes.
- First-time users still wait for live collection if the scheduled catalog has
  not populated PostgreSQL.
- Schema creation currently occurs at application startup instead of through
  versioned migrations.
- PostgreSQL stores vectors as JSONB for ChromaDB hydration rather than using a
  native vector type for database-side similarity search.
- Portal markup can change and break either scraper.
- There is no distributed refresh lease, retry dashboard, refresh-health
  history, metrics, or alerting.
- Session embedding reuse is implemented locally; restarts/session resets discard
  those private vectors.
- The fixed 70/30 score is not calibrated against labeled hiring outcomes.
- `PyPDF2` emits a deprecation warning and should eventually be replaced with
  `pypdf`.

## Recommended next engineering work

1. Add distributed refresh leases or coalescing so Streamlit and scheduled
   workers do not scrape the same city simultaneously.
2. Introduce versioned PostgreSQL migrations and a least-privilege runtime
   database role.
3. Add portal health, refresh age, job-count, failure, and API-cost telemetry.
4. **Implemented locally:** cache resume embeddings by a private session content
   fingerprint; see the October 8 changes above.
5. **Evaluation tooling implemented; calibration pending:** review representative
   resume/job relevance labels, collect measured ASU features when the service is
   available, and assess held-out ranking quality before changing weights or
   adding an LLM-based judge.

## Safe Git handoff

To continue from the pushed implementation:

```powershell
git fetch origin
git switch asu-exp
git pull --ff-only origin asu-exp
```

Do not commit `.env`, `.streamlit/secrets.toml`, `CODEBASE_CONTEXT.md`, resumes,
generated caches, ChromaDB data, virtual environments, or credentials.
