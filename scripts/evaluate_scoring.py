"""Evaluate municipal-job rankings without changing runtime weights.

Default execution is network-free (keyword baseline). Use --collect-features
explicitly to measure ASU cosine similarities, then --features for offline replay.
"""

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from matching_scoring import (  # noqa: E402
    calculate_keyword_overlap, combine_match_score,
    prepare_job_text, prepare_resume_text,
)

DEFAULT_DATASET = PROJECT_ROOT / "tests/fixtures/scoring_benchmark.json"


def dataset_fingerprint(dataset):
    # Include the exact prepared inputs so embedding-text changes invalidate replay.
    source = {"dataset": dataset,
              "profile_texts": {p["id"]: prepare_resume_text(p) for p in dataset["profiles"]},
              "job_texts": {j["id"]: prepare_job_text(j) for j in dataset["jobs"]}}
    content = json.dumps(source, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def validate_dataset(dataset):
    if dataset.get("schema_version") != 1:
        raise ValueError("Unsupported dataset schema")
    profiles, jobs = dataset["profiles"], dataset["jobs"]
    if not profiles or not jobs:
        raise ValueError("At least one profile and job are required")
    profile_ids = {profile["id"] for profile in profiles}
    job_ids = {job["id"] for job in jobs}
    if len(profile_ids) != len(profiles) or len(job_ids) != len(jobs):
        raise ValueError("Profile/job IDs must be unique")
    expected = {(profile_id, job_id) for profile_id in profile_ids for job_id in job_ids}
    actual = set()
    for row in dataset["relevance"]:
        key = (row["profile_id"], row["job_id"])
        grade = row["grade"]
        if key in actual or key not in expected:
            raise ValueError("Duplicate or unknown relevance pair")
        if isinstance(grade, bool) or not isinstance(grade, int) or not 0 <= grade <= 3:
            raise ValueError("Relevance grades must be integers from zero to three")
        actual.add(key)
    if actual != expected:
        raise ValueError("Every profile/job pair must be labeled; missing labels are not negatives")


def validate_features(dataset, features):
    if features.get("schema_version") != 1:
        raise ValueError("Unsupported feature schema")
    if features.get("dataset_sha256") != dataset_fingerprint(dataset):
        raise ValueError("Feature snapshot does not match this dataset")
    expected = {(r["profile_id"], r["job_id"]) for r in dataset["relevance"]}
    values = {}
    for row in features["pairs"]:
        key = (row["profile_id"], row["job_id"])
        value = row["semantic_similarity"]
        if key in values or key not in expected:
            raise ValueError("Duplicate or unknown feature pair")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not -1 <= value <= 1:
            raise ValueError("Semantic similarity must be finite and in [-1, 1]")
        values[key] = value
    if set(values) != expected:
        raise ValueError("Feature snapshot must cover every labeled pair")
    return values


def cosine_similarity(left, right):
    if not left or len(left) != len(right) or not all(math.isfinite(v) for v in left + right):
        raise ValueError("Invalid embedding vectors")
    norm_left = math.sqrt(sum(v * v for v in left))
    norm_right = math.sqrt(sum(v * v for v in right))
    if norm_left == 0 or norm_right == 0:
        raise ValueError("Zero embeddings cannot be evaluated")
    value = sum(a * b for a, b in zip(left, right)) / (norm_left * norm_right)
    return min(1.0, max(-1.0, value))


def collect_features(dataset, generate, configuration):
    """Embed each synthetic input once; persist IDs/similarities, never vectors."""
    validate_dataset(dataset)

    def embed(text):
        vector = [float(v) for v in generate(text)]
        if len(vector) != configuration["dimensions"]:
            raise ValueError("Provider returned an unexpected embedding size")
        return vector

    profiles = {p["id"]: embed(prepare_resume_text(p)) for p in dataset["profiles"]}
    jobs = {j["id"]: embed(prepare_job_text(j)) for j in dataset["jobs"]}
    pairs = [
        {"profile_id": r["profile_id"], "job_id": r["job_id"],
         "semantic_similarity": cosine_similarity(profiles[r["profile_id"]], jobs[r["job_id"]])}
        for r in dataset["relevance"]
    ]
    return {"schema_version": 1, "dataset_sha256": dataset_fingerprint(dataset),
            "source": "ASU embeddings", "embedding_configuration": configuration, "pairs": pairs}


def ranking_metrics(rows, k):
    """Linear-gain NDCG and expected precision with averaged score ties.

    Pairwise accuracy gives half credit to score ties between unequal grades.
    Grades >= 2 count as relevant for precision; NDCG uses all grades.
    """
    ordered = sorted(rows, key=lambda row: row["score"], reverse=True)
    cutoff = min(k, len(ordered))
    dcg = 0.0
    relevant_at_k = 0.0
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end]["score"] == ordered[start]["score"]:
            end += 1
        group = ordered[start:end]
        average_grade = sum(row["grade"] for row in group) / len(group)
        average_relevant = sum(row["grade"] >= 2 for row in group) / len(group)
        for rank in range(start, min(end, cutoff)):
            dcg += average_grade / math.log2(rank + 2)
            relevant_at_k += average_relevant
        start = end
    ideal = sorted((r["grade"] for r in rows), reverse=True)[:cutoff]
    idcg = sum(grade / math.log2(rank + 2) for rank, grade in enumerate(ideal))
    concordance = []
    for index, left in enumerate(rows):
        for right in rows[index + 1:]:
            if left["grade"] == right["grade"]:
                continue
            delta = (left["score"] - right["score"]) * (left["grade"] - right["grade"])
            concordance.append(1.0 if delta > 0 else 0.5 if delta == 0 else 0.0)
    return {"ndcg_at_k": dcg / idcg if idcg else None,
            "precision_at_k": relevant_at_k / cutoff if cutoff else None,
            "pairwise_accuracy": sum(concordance) / len(concordance) if concordance else None}


def evaluate(dataset, features=None, k=3):
    validate_dataset(dataset)
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer")
    similarities = validate_features(dataset, features) if features is not None else None
    profiles = {p["id"]: p for p in dataset["profiles"]}
    jobs = {j["id"]: j for j in dataset["jobs"]}
    weights = [0.0, 0.3, 0.5, 0.7, 0.9, 1.0] if similarities is not None else [0.0]
    variants = []
    for weight in weights:
        by_profile = defaultdict(list)
        for relevance in dataset["relevance"]:
            profile_id, job_id = relevance["profile_id"], relevance["job_id"]
            overlap = calculate_keyword_overlap(jobs[job_id], profiles[profile_id])
            semantic = similarities[(profile_id, job_id)] if similarities is not None else 0.0
            score = combine_match_score(semantic, overlap, weight)
            by_profile[profile_id].append({**relevance, "score": score,
                                          "semantic_similarity": semantic if similarities is not None else None,
                                          "keyword_overlap": overlap})
        per_profile = []
        for profile_id, rows in by_profile.items():
            per_profile.append({"profile_id": profile_id,
                                "category": profiles[profile_id].get("category", "unspecified"),
                                **ranking_metrics(rows, k),
                                "ranking": sorted(rows, key=lambda r: (-r["score"], r["job_id"]))})
        macro = {}
        for metric in ("ndcg_at_k", "precision_at_k", "pairwise_accuracy"):
            values = [row[metric] for row in per_profile if row[metric] is not None]
            macro[metric] = sum(values) / len(values) if values else None
        name = "keyword_only" if weight == 0 else "semantic_only" if weight == 1 else "runtime_70_30" if weight == 0.7 else f"semantic_weight_{weight:.1f}"
        variants.append({"name": name, "semantic_weight": weight, "macro_metrics": macro,
                         "per_profile": per_profile})
    return {"dataset": dataset["name"], "dataset_sha256": dataset_fingerprint(dataset),
            "label_source": dataset["label_source"], "profile_count": len(profiles),
            "job_count": len(jobs), "pair_count": len(dataset["relevance"]), "k": k,
            "mode": "measured_semantic_features" if features is not None else "keyword_only_diagnostic",
            "feature_source": features.get("source") if features is not None else None,
            "embedding_configuration": features.get("embedding_configuration") if features is not None else None,
            "limitations": dataset.get("limitations", []) + [
                "Synthetic judgments are not independently reviewed hiring labels.",
                "Weight sweep is exploratory on this set, not held-out calibration.",
                "Scores are retrieval heuristics, not interview/offer probabilities.",
                "Score ties are averaged in metrics; displayed ranking breaks ties by job ID.",
                "Evaluation ranks the full fixture corpus before runtime city/title filters and thresholds.",
            ] + ([] if features is not None else ["Hybrid/semantic performance was not measured; collect ASU features first."]),
            "runtime_weights_changed": False, "variants": variants}


def write_json(filename, value):
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--features", type=Path, help="Replay measured similarities without network calls")
    mode.add_argument("--collect-features", type=Path, help="Call ASU embeddings and save a feature snapshot (uses API quota)")
    parser.add_argument("--output", type=Path, help="Save a detailed evaluation report")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()
    try:
        dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
        validate_dataset(dataset)
        if args.k < 1:
            raise ValueError("k must be a positive integer")
        features = None
        if args.features:
            features = json.loads(args.features.read_text(encoding="utf-8"))
        elif args.collect_features:
            from config import (ASU_AI_API_KEY, ASU_AI_BASE_URL, ASU_AI_EMBEDDINGS_MODEL,
                                ASU_AI_EMBEDDINGS_PROVIDER, ASU_AI_EMBEDDINGS_DIMENSIONS)
            from rag.asu_ai_provider import ASUAIProvider
            if not ASU_AI_API_KEY:
                parser.error("ASU_AI_API_KEY is required for feature collection")
            provider = ASUAIProvider(api_key=ASU_AI_API_KEY)
            configuration = {"base_url": ASU_AI_BASE_URL, "provider": ASU_AI_EMBEDDINGS_PROVIDER,
                             "model": ASU_AI_EMBEDDINGS_MODEL, "dimensions": ASU_AI_EMBEDDINGS_DIMENSIONS}
            features = collect_features(dataset, lambda text: provider.generate_embedding_sync(
                text, model=configuration["model"], provider=configuration["provider"],
                dimensions=configuration["dimensions"]), configuration)
            write_json(args.collect_features, features)
        result = evaluate(dataset, features, args.k)
        if args.output:
            write_json(args.output, result)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        # Provider responses may contain sensitive details; print no payloads.
        parser.exit(1, f"Evaluation failed ({type(exc).__name__}); check dataset/features and API configuration.\n")
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        detail = f"HTTP {status}" if status is not None else type(exc).__name__
        parser.exit(1, f"Feature collection failed ({detail}); no report produced.\n")
    summary = {key: result[key] for key in ("dataset", "mode", "profile_count", "job_count", "pair_count", "k")}
    summary["metrics"] = {v["name"]: v["macro_metrics"] for v in result["variants"]}
    print(json.dumps(summary, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
