"""Network-free scoring metrics and reproducible benchmark validation."""

import json
import math
from unittest.mock import Mock

import pytest

from matching_scoring import combine_match_score, prepare_resume_text
from scripts.evaluate_scoring import (
    DEFAULT_DATASET, collect_features, cosine_similarity,
    evaluate, ranking_metrics, validate_dataset,
)


@pytest.fixture
def dataset():
    return json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))


def test_runtime_formula_and_unparsed_resume_fallback():
    assert combine_match_score(0.8, 0.5) == pytest.approx(71)
    assert combine_match_score(-0.5, 0) == pytest.approx(-35)
    assert "synthetic resume" in prepare_resume_text({"resume_parsed": None, "resume_text": "synthetic resume"})


@pytest.mark.parametrize("values", [(float("nan"), 0, .7), (1.1, 0, .7), (0, -1, .7), (0, 0, 2)])
def test_invalid_scores_are_rejected(values):
    with pytest.raises(ValueError):
        combine_match_score(*values)


def test_perfect_and_reversed_ranking_metrics():
    rows = [{"score": 3, "grade": 3}, {"score": 2, "grade": 2}, {"score": 1, "grade": 0}]
    metrics = ranking_metrics(rows, 2)
    assert metrics == {"ndcg_at_k": 1, "precision_at_k": 1, "pairwise_accuracy": 1}
    reversed_rows = [{**r, "score": -r["score"]} for r in rows]
    metrics = ranking_metrics(reversed_rows, 2)
    assert metrics["pairwise_accuracy"] == 0
    assert metrics["precision_at_k"] == .5
    assert metrics["ndcg_at_k"] == pytest.approx((2 / math.log2(3)) / (3 + 2 / math.log2(3)))


def test_score_ties_average_relevance_and_do_not_depend_on_fixture_order():
    rows = [{"score": 1, "grade": 3}, {"score": 1, "grade": 0}]
    expected = {"ndcg_at_k": .5, "precision_at_k": .5, "pairwise_accuracy": .5}
    assert ranking_metrics(rows, 1) == expected
    assert ranking_metrics(list(reversed(rows)), 1) == expected
    assert ranking_metrics([{"score": 1, "grade": 0}], 3)["ndcg_at_k"] is None


def test_default_benchmark_is_complete_and_reports_only_keyword_diagnostic(dataset):
    validate_dataset(dataset)
    report = evaluate(dataset)
    assert report["pair_count"] == 72
    assert report["mode"] == "keyword_only_diagnostic"
    assert [v["name"] for v in report["variants"]] == ["keyword_only"]
    assert any("not measured" in limitation for limitation in report["limitations"])
    assert report["runtime_weights_changed"] is False


def test_feature_collection_and_replay_use_each_input_once(dataset):
    # Deliberately mocked vectors: metric mechanics, not real model quality.
    generate = Mock(return_value=[1, 0])
    features = collect_features(dataset, generate, {"dimensions": 2, "model": "mock"})
    features["source"] = "mock vectors for test only"
    assert generate.call_count == len(dataset["profiles"]) + len(dataset["jobs"])
    assert "synthetic resume" not in json.dumps(features)
    report = evaluate(dataset, features)
    assert report["mode"] == "measured_semantic_features"
    assert report["feature_source"] == "mock vectors for test only"
    assert "runtime_70_30" in [v["name"] for v in report["variants"]]
    assert len(report["variants"]) == 6
    keyword = report["variants"][0]
    assert keyword["macro_metrics"] == evaluate(dataset)["variants"][0]["macro_metrics"]
    assert all(0 <= value <= 1 for value in keyword["macro_metrics"].values())


@pytest.mark.parametrize("mutation", ["missing_label", "duplicate_label", "invalid_grade"])
def test_incomplete_or_ambiguous_labels_are_rejected(dataset, mutation):
    if mutation == "missing_label":
        dataset["relevance"].pop()
    elif mutation == "duplicate_label":
        dataset["relevance"].append(dataset["relevance"][0])
    else:
        dataset["relevance"][0]["grade"] = -1
    with pytest.raises(ValueError):
        evaluate(dataset)


@pytest.mark.parametrize("mutation", ["stale", "missing", "duplicate", "nan", "out_of_range"])
def test_feature_snapshots_cannot_silently_mismatch_dataset(dataset, mutation):
    features = collect_features(dataset, lambda _: [1, 0], {"dimensions": 2})
    if mutation == "stale":
        dataset["jobs"][0]["description"] += "changed"
    elif mutation == "missing":
        features["pairs"].pop()
    elif mutation == "duplicate":
        features["pairs"].append(features["pairs"][0])
    else:
        features["pairs"][0]["semantic_similarity"] = float("nan") if mutation == "nan" else 2
    with pytest.raises(ValueError):
        evaluate(dataset, features)


def test_feature_collection_rejects_invalid_embeddings(dataset):
    with pytest.raises(ValueError):
        collect_features(dataset, lambda _: [0, 0], {"dimensions": 2})
    with pytest.raises(ValueError):
        collect_features(dataset, lambda _: [1], {"dimensions": 2})
    assert cosine_similarity([1, 0], [0, 1]) == 0
    assert cosine_similarity([1, 0], [-1, 0]) == -1


def test_embedding_text_changes_invalidate_feature_replay(dataset, monkeypatch):
    from scripts import evaluate_scoring
    features = collect_features(dataset, lambda _: [1, 0], {"dimensions": 2})
    original = evaluate_scoring.prepare_resume_text
    monkeypatch.setattr(evaluate_scoring, "prepare_resume_text", lambda p: original(p) + " changed preparation")
    with pytest.raises(ValueError):
        evaluate(dataset, features)
