"""Local and PostgreSQL storage for shared job-catalog state."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from config import CACHE_DIR, DATABASE_URL
from job_identity import deduplicate_jobs


@dataclass(frozen=True)
class CitySnapshot:
    city: str
    refreshed_at: datetime
    jobs: List[Dict]


class JobStore(ABC):
    """Persistence contract shared by request and scheduled workers."""

    @abstractmethod
    def get_city_snapshot(self, city: str) -> Optional[CitySnapshot]:
        pass

    @abstractmethod
    def replace_city_jobs(self, city: str, jobs: List[Dict]) -> None:
        pass

    @abstractmethod
    def clear(self, city: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def list_snapshots(self) -> List[CitySnapshot]:
        pass

    def load_embeddings(self, content_hashes: Dict[str, str]) -> Dict[str, List[float]]:
        """Return shared embeddings whose stored hashes match the request."""
        return {}

    def save_embeddings(
        self,
        embeddings: Dict[str, Tuple[str, List[float]]],
    ) -> None:
        """Persist embeddings for reuse by other application instances."""


class LocalJsonJobStore(JobStore):
    """Development fallback using the existing per-city JSON files."""

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = Path(cache_dir)

    def _cache_path(self, city: str) -> Path:
        safe_name = city.lower().replace(" ", "_").replace("/", "_")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / f"jobs_{safe_name}.json"

    def get_city_snapshot(self, city: str) -> Optional[CitySnapshot]:
        path = self._cache_path(city)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return CitySnapshot(
                city=data.get("city", city),
                refreshed_at=datetime.fromisoformat(data["cached_at"]),
                jobs=deduplicate_jobs(data.get("jobs", [])),
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def replace_city_jobs(self, city: str, jobs: List[Dict]) -> None:
        normalized_jobs = deduplicate_jobs(jobs)
        data = {
            "city": city,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "job_count": len(normalized_jobs),
            "jobs": normalized_jobs,
        }
        path = self._cache_path(city)
        temporary_path = path.with_suffix(f".{uuid4().hex}.tmp")
        try:
            temporary_path.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8",
            )
            os.replace(temporary_path, path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def clear(self, city: Optional[str] = None) -> None:
        if city:
            path = self._cache_path(city)
            if path.exists():
                path.unlink()
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        for path in self.cache_dir.glob("jobs_*.json"):
            path.unlink()

    def list_snapshots(self) -> List[CitySnapshot]:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        snapshots = []
        for path in self.cache_dir.glob("jobs_*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                city = data.get("city", path.stem)
                snapshot = self.get_city_snapshot(city)
                if snapshot:
                    snapshots.append(snapshot)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        return snapshots


class PostgresJobStore(JobStore):
    """Shared durable storage using a standard PostgreSQL database."""

    def __init__(self, database_url: str):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL storage requires psycopg[binary]. Install requirements.txt."
            ) from exc

        self._psycopg = psycopg
        self.database_url = database_url
        self._ensure_schema()

    def _connect(self):
        return self._psycopg.connect(self.database_url)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS job_catalog (
                    job_id TEXT PRIMARY KEY,
                    city TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS job_catalog_city_idx
                ON job_catalog (city)
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS job_city_refresh (
                    city TEXT PRIMARY KEY,
                    refreshed_at TIMESTAMPTZ NOT NULL,
                    job_count INTEGER NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS job_embedding_cache (
                    job_id TEXT PRIMARY KEY REFERENCES job_catalog(job_id)
                        ON DELETE CASCADE,
                    content_hash TEXT NOT NULL,
                    embedding JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

    def get_city_snapshot(self, city: str) -> Optional[CitySnapshot]:
        with self._connect() as connection:
            refresh = connection.execute(
                "SELECT refreshed_at FROM job_city_refresh WHERE city = %s",
                (city,),
            ).fetchone()
            if not refresh:
                return None
            rows = connection.execute(
                "SELECT payload FROM job_catalog WHERE city = %s ORDER BY job_id",
                (city,),
            ).fetchall()
        return CitySnapshot(
            city=city,
            refreshed_at=refresh[0],
            jobs=deduplicate_jobs([row[0] for row in rows]),
        )

    def replace_city_jobs(self, city: str, jobs: List[Dict]) -> None:
        from psycopg.types.json import Jsonb

        normalized_jobs = deduplicate_jobs(jobs)
        job_ids = [job["job_id"] for job in normalized_jobs]
        refreshed_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (city,),
            )
            if job_ids:
                connection.execute(
                    "DELETE FROM job_catalog WHERE city = %s AND NOT (job_id = ANY(%s))",
                    (city, job_ids),
                )
                connection.executemany(
                    """
                    INSERT INTO job_catalog (job_id, city, payload, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (job_id) DO UPDATE SET
                        city = EXCLUDED.city,
                        payload = EXCLUDED.payload,
                        updated_at = NOW()
                    """,
                    [
                        (job["job_id"], city, Jsonb(job))
                        for job in normalized_jobs
                    ],
                )
            else:
                connection.execute("DELETE FROM job_catalog WHERE city = %s", (city,))
            connection.execute(
                """
                INSERT INTO job_city_refresh (city, refreshed_at, job_count)
                VALUES (%s, %s, %s)
                ON CONFLICT (city) DO UPDATE SET
                    refreshed_at = EXCLUDED.refreshed_at,
                    job_count = EXCLUDED.job_count
                """,
                (city, refreshed_at, len(normalized_jobs)),
            )

    def clear(self, city: Optional[str] = None) -> None:
        with self._connect() as connection:
            if city:
                connection.execute("DELETE FROM job_catalog WHERE city = %s", (city,))
                connection.execute("DELETE FROM job_city_refresh WHERE city = %s", (city,))
            else:
                connection.execute("DELETE FROM job_catalog")
                connection.execute("DELETE FROM job_city_refresh")

    def list_snapshots(self) -> List[CitySnapshot]:
        with self._connect() as connection:
            cities = connection.execute(
                "SELECT city FROM job_city_refresh ORDER BY city"
            ).fetchall()
        return [
            snapshot
            for (city,) in cities
            if (snapshot := self.get_city_snapshot(city)) is not None
        ]

    def load_embeddings(self, content_hashes: Dict[str, str]) -> Dict[str, List[float]]:
        if not content_hashes:
            return {}
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT job_id, content_hash, embedding
                FROM job_embedding_cache
                WHERE job_id = ANY(%s)
                """,
                (list(content_hashes),),
            ).fetchall()
        return {
            job_id: embedding
            for job_id, content_hash, embedding in rows
            if content_hashes.get(job_id) == content_hash
        }

    def save_embeddings(
        self,
        embeddings: Dict[str, Tuple[str, List[float]]],
    ) -> None:
        if not embeddings:
            return
        from psycopg.types.json import Jsonb

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO job_embedding_cache
                    (job_id, content_hash, embedding, updated_at)
                SELECT %s, %s, %s, NOW()
                WHERE EXISTS (
                    SELECT 1 FROM job_catalog WHERE job_id = %s
                )
                ON CONFLICT (job_id) DO UPDATE SET
                    content_hash = EXCLUDED.content_hash,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                [
                    (job_id, content_hash, Jsonb(embedding), job_id)
                    for job_id, (content_hash, embedding) in embeddings.items()
                ],
            )


@lru_cache(maxsize=1)
def get_job_store() -> JobStore:
    """Return the configured shared store or the local development fallback."""
    if DATABASE_URL:
        return PostgresJobStore(DATABASE_URL)
    return LocalJsonJobStore()
