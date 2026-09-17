"""Canonical, deterministic identity helpers for job records."""

import hashlib
import re
from typing import Any, Dict, Iterable, List, MutableMapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


_TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


def canonicalize_job_url(url: Any) -> str:
    """Return a stable URL while retaining identity-bearing query parameters."""
    raw_url = str(url or "").strip()
    if not raw_url:
        return ""

    parsed = urlsplit(raw_url)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    if port and not (
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        hostname = f"{hostname}:{port}"

    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/") or "/"
    query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        normalized_key = key.lower()
        if normalized_key.startswith("utm_") or normalized_key in _TRACKING_QUERY_KEYS:
            continue
        query_items.append((key, value))

    # NEOGOV posting identity is entirely contained in /jobs/{posting_id}.
    if hostname.endswith("governmentjobs.com") and "/jobs/" in path.lower():
        query_items = []

    query = urlencode(sorted(query_items), doseq=True)
    return urlunsplit((scheme, hostname, path, query, ""))


def _normalized_component(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _platform_name(job: MutableMapping[str, Any], canonical_url: str) -> str:
    raw_data = job.get("raw_data")
    if isinstance(raw_data, dict):
        explicit_platform = raw_data.get("platform")
        if explicit_platform:
            return _normalized_component(explicit_platform)

    explicit_platform = job.get("platform")
    if explicit_platform:
        return _normalized_component(explicit_platform)

    hostname = (urlsplit(canonical_url).hostname or "").lower()
    if hostname.endswith("governmentjobs.com") or hostname.endswith("neogov.com"):
        return "neogov"
    if "peoplesoft" in hostname or "hcmprod" in hostname:
        return "peoplesoft"
    return hostname or "unknown"


def stable_job_id(job: MutableMapping[str, Any]) -> str:
    """Generate a stable ID from platform, city, and canonical job identity."""
    canonical_url = canonicalize_job_url(job.get("url"))
    platform = _platform_name(job, canonical_url)
    city = _normalized_component(job.get("city")) or "unknown"

    if canonical_url:
        source_identity = canonical_url.casefold()
    else:
        raw_data = job.get("raw_data")
        raw_data = raw_data if isinstance(raw_data, dict) else {}
        existing_job_id = job.get("job_id")
        if re.fullmatch(r"job_[0-9a-f]{24}", str(existing_job_id or "")):
            existing_job_id = None
        source_id = (
            raw_data.get("posting_id")
            or raw_data.get("source_job_id")
            or job.get("source_job_id")
            or existing_job_id
        )
        if source_id:
            source_identity = f"source:{_normalized_component(source_id)}"
        else:
            fallback_fields = (
                job.get("title"),
                job.get("department"),
                job.get("location"),
            )
            source_identity = "fallback:" + "|".join(
                _normalized_component(value) for value in fallback_fields
            )

    seed = "\x1f".join((platform, city, source_identity))
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
    return f"job_{digest}"


def ensure_job_id(job: MutableMapping[str, Any]) -> str:
    """Canonicalize a mutable job record and assign its deterministic ID."""
    canonical_url = canonicalize_job_url(job.get("url"))
    if canonical_url:
        job["url"] = canonical_url
    job_id = stable_job_id(job)
    job["job_id"] = job_id
    return job_id


def normalize_job(job: MutableMapping[str, Any]) -> Dict[str, Any]:
    """Return a normalized copy without mutating the caller's job record."""
    normalized = dict(job)
    if isinstance(job.get("raw_data"), dict):
        normalized["raw_data"] = dict(job["raw_data"])
    ensure_job_id(normalized)
    return normalized


def normalize_jobs(jobs: Iterable[MutableMapping[str, Any]]) -> List[Dict[str, Any]]:
    """Return normalized copies of all supplied job records."""
    return [normalize_job(job) for job in jobs]


def _record_quality(job: MutableMapping[str, Any]) -> tuple:
    try:
        match_score = float(job.get("match_score") or 0)
    except (TypeError, ValueError):
        match_score = 0.0
    return (
        match_score,
        sum(
            len(str(job.get(field) or ""))
            for field in ("description", "requirements", "department", "salary")
        ),
    )


def deduplicate_jobs(
    jobs: Iterable[MutableMapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Deduplicate by stable ID, retaining the highest-quality record."""
    unique_jobs: Dict[str, Dict[str, Any]] = {}
    for job in normalize_jobs(jobs):
        job_id = job["job_id"]
        current = unique_jobs.get(job_id)
        if current is None or _record_quality(job) > _record_quality(current):
            unique_jobs[job_id] = job
    return list(unique_jobs.values())
