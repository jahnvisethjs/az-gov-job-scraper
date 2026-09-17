"""Tests for persistent, incremental job embedding updates."""

from rag.rag_engine import (
    EMBEDDING_HASH_KEY,
    JobRAG,
    _job_embedding_hash,
)
from job_identity import ensure_job_id


def _job(job_id, city, title, description="Description"):
    job = {
        "job_id": job_id,
        "city": city,
        "title": title,
        "description": description,
        "requirements": "Python",
        "url": f"https://example.com/{job_id}",
    }
    ensure_job_id(job)
    return job


class FakeCollection:
    def __init__(self, records=None):
        self.records = records or {}
        self.deleted = []
        self.upserted = []
        self.updated = []

    def get(self, include=None):
        return {
            "ids": list(self.records),
            "metadatas": [record["metadata"] for record in self.records.values()],
        }

    def delete(self, ids):
        self.deleted.extend(ids)
        for job_id in ids:
            self.records.pop(job_id, None)

    def update(self, ids, metadatas):
        self.updated.extend(ids)
        for job_id, metadata in zip(ids, metadatas):
            self.records[job_id]["metadata"] = metadata

    def upsert(self, documents, embeddings, ids, metadatas):
        self.upserted.extend(ids)
        for job_id, document, embedding, metadata in zip(
            ids, documents, embeddings, metadatas
        ):
            self.records[job_id] = {
                "document": document,
                "embedding": embedding,
                "metadata": metadata,
            }


class FakeProvider:
    def __init__(self):
        self.batches = []

    def generate_embeddings_batch(self, texts, progress_callback=None, **kwargs):
        self.batches.append(list(texts))
        embeddings = []
        for index, _text in enumerate(texts, start=1):
            embeddings.append([float(index)])
            if progress_callback:
                progress_callback(index, len(texts))
        return embeddings


def _rag(collection):
    rag = object.__new__(JobRAG)
    rag.collection = collection
    rag.llm_provider = FakeProvider()
    return rag


def test_incremental_index_embeds_only_new_or_changed_jobs():
    unchanged = _job("tempe-1", "Tempe", "Developer")
    changed_before = _job("tempe-2", "Tempe", "Analyst", "Old description")
    changed_after = _job("tempe-2", "Tempe", "Analyst", "New description")
    stale = _job("tempe-old", "Tempe", "Expired role")
    other_city = _job("mesa-1", "Mesa", "Planner")

    records = {}
    for job in (unchanged, changed_before, stale, other_city):
        records[job["job_id"]] = {
            "metadata": {
                **job,
                EMBEDDING_HASH_KEY: _job_embedding_hash(job),
            }
        }

    collection = FakeCollection(records)
    rag = _rag(collection)
    new_job = _job("tempe-3", "Tempe", "Engineer")
    progress = []

    update = rag.add_jobs(
        [unchanged, changed_after, new_job],
        scope_cities=["Tempe"],
        progress_callback=lambda completed, total: progress.append((completed, total)),
    )

    assert update.embedded == 2
    assert update.unchanged == 1
    assert update.removed == 1
    assert collection.deleted == [stale["job_id"]]
    assert set(collection.upserted) == {
        changed_after["job_id"],
        new_job["job_id"],
    }
    assert collection.updated == [unchanged["job_id"]]
    assert other_city["job_id"] in collection.records
    assert progress == [(1, 2), (2, 2)]


def test_incremental_index_reuses_embeddings_after_new_rag_instance():
    job = _job("phoenix-1", "Phoenix", "Engineer")
    collection = FakeCollection()

    first_rag = _rag(collection)
    first = first_rag.add_jobs([job], scope_cities=["Phoenix"])

    second_rag = _rag(collection)
    second = second_rag.add_jobs([job], scope_cities=["Phoenix"])

    assert first.embedded == 1
    assert second.embedded == 0
    assert second.unchanged == 1
    assert second_rag.llm_provider.batches == []
