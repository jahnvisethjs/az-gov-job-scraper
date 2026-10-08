# Scoring evaluation and session embedding reuse

Last updated: 2026-10-08

## Session resume embeddings (item 4)

Each Streamlit session owns one `ResumeEmbeddingCache`. The cached-results pass
and its background refresh receive the same object through the search service
and matcher. New `JobRAG` instances can reuse the vector without accessing
Streamlit state from worker threads.

The key is a session-secret HMAC of the exact prepared embedding text plus the
ASU base URL, provider, model and dimensions. Changing role/location search
context therefore changes the key. Relevant profile edits and session reset
clear the vector and rotate the secret. Only one completed vector is retained;
no resume text, embedding, or fingerprint is written to shared storage or disk.
The object is not shared between sessions or held in a global Streamlit cache.

Concurrent requests for identical inputs share one generation. Failed, invalid,
or cancelled generations are not cached. Clearing while an HTTP request is in
flight returns immediately, and that request cannot repopulate the cleared
cache. In-flight HTTP cancellation still follows the existing timeout behavior.

When structured resume parsing is unavailable, prepared embedding text includes
the extracted resume text instead of failing on a missing parse.

## Scoring evaluation (item 5)

Runtime and evaluation share `matching_scoring.py` for text preparation, keyword
overlap and the hybrid formula. Runtime weights remain **70% cosine similarity
and 30% keyword overlap**. The score remains a retrieval heuristic.

`tests/fixtures/scoring_benchmark.json` contains six synthetic candidate profiles,
12 municipal-job examples and all 72 relevance judgments. It covers office
support, analytics, IT support, accounting, engineering and recreation, including
seniority gaps, missing mandatory credentials, failed parsing, negation and
misleading keyword mentions. Grades range from 0 (unrelated) to 3 (strong fit).
Labels are assistant-authored judgments, not independently reviewed hiring data.

The evaluation reports per-profile rankings and macro averages of:

- Linear-gain NDCG@k for graded relevance.
- Precision@k, treating grades 2 and 3 as relevant.
- Pairwise ordering accuracy for pairs with different grades.

Score ties are averaged for NDCG and precision; pairwise ties receive half
credit. Queries with no positive relevance have undefined NDCG and are excluded
from its macro average. The report ranks the complete fixture corpus before
runtime title/city filtering or score thresholds. Metric conventions follow
[the scikit-learn NDCG documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.ndcg_score.html).

### Network-free keyword diagnostic

```powershell
python scripts/evaluate_scoring.py --output data/evaluation/keyword-baseline.json
```

October 8, 2026 baseline, k=3:

| Metric | Keyword-only diagnostic |
|---|---:|
| Mean NDCG@3 | 0.9327 |
| Mean precision@3 | 0.4907 |
| Mean pairwise ordering accuracy | 0.8818 |

These are **keyword-only** results. They do not measure the current hybrid
scorer or the ASU embedding model. Automated tests use mocked vectors only to
verify evaluation mechanics; their results are not model-quality evidence.

### Measure the current model and replay offline

Feature collection explicitly contacts ASU and uses API quota: six profile
embeddings plus 12 job embeddings, with possible provider retries. It does not
contact job portals, PostgreSQL or the Chroma index.

```powershell
python scripts/evaluate_scoring.py --collect-features data/evaluation/asu-features.json --output data/evaluation/asu-baseline.json
python scripts/evaluate_scoring.py --features data/evaluation/asu-features.json --output data/evaluation/replay.json
```

The feature snapshot records model configuration and ID-keyed measured cosine
similarities, without storing vectors or input text. A fingerprint of the
dataset and exact prepared embedding inputs prevents replay against changed
inputs. Missing, duplicate, nonfinite or out-of-range features are rejected.
Generated feature snapshots and reports under `data/evaluation/` are ignored by
Git. The default dataset is entirely synthetic.

Measured replay compares the current 70/30 formula with keyword-only,
semantic-only, and semantic weights of 0.3, 0.5 and 0.9. It never edits runtime
weights. The live attempt on October 8, 2026 reached ASU after network approval
but failed with a server HTTP error after the provider's three attempts. No
measured feature snapshot or hybrid report was produced.

### Calibration still needs evidence

Have independent reviewers grade representative resume/job pairs, with clear
rubrics for required credentials, seniority and transferable skills. Separate
weight-development examples from held-out evaluation examples. Compare ranking
metrics and challenge-case performance on that held-out set before selecting
weights or adding an LLM judge. No change to weights is justified by this small
synthetic diagnostic or its keyword-only baseline.

## Validation

All cache and metric tests run without network calls. Cache tests cover session
isolation, changed profile/search/model inputs, foreground/background propagation,
same-input concurrency, cancellation, failure retries, and clearing during a
request. Metric tests verify perfect/reversed rankings, tie handling, fixture
completeness and rejection of mismatched replay snapshots.
