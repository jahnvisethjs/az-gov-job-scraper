"""One in-memory resume vector per session; no resume text or persistent keys."""

from concurrent.futures import Future, TimeoutError
import hashlib
import hmac
import json
import math
import secrets
from threading import Lock
from typing import Callable, List, Tuple

from progress_events import CancelCheck, raise_if_cancelled


class ResumeEmbeddingCache:
    """Share a vector across foreground/background workers of one session.

    A random session secret protects the content fingerprint from cross-session
    correlation. Generation runs outside the lock so clearing a session never
    waits for an HTTP request. Concurrent requests for the same input coalesce.
    """

    def __init__(self):
        self._secret = secrets.token_bytes(32)
        self._lock = Lock()
        self._revision = 0
        self._entry = None
        self._pending = {}

    def clear(self) -> None:
        with self._lock:
            self._revision += 1
            self._entry = None
            self._pending.clear()
            self._secret = secrets.token_bytes(32)

    def get_or_create(
        self,
        text: str,
        *,
        configuration: Tuple[str, str, str, int],
        create: Callable[[], List[float]],
        cancel_check: CancelCheck = None,
    ) -> List[float]:
        """Reuse only exact embedding input/model matches; never cache failures."""
        raise_if_cancelled(cancel_check)
        source = json.dumps([configuration, text], ensure_ascii=False).encode("utf-8")
        with self._lock:
            key = hmac.new(self._secret, source, hashlib.sha256).digest()
            revision = self._revision
            if self._entry is not None and self._entry[0] == key:
                return list(self._entry[1])
            pending_key = (revision, key)
            future = self._pending.get(pending_key)
            owner = future is None
            if owner:
                future = Future()
                self._pending[pending_key] = future

        if not owner:
            while True:
                raise_if_cancelled(cancel_check)
                try:
                    vector = future.result(timeout=0.1)
                    raise_if_cancelled(cancel_check)
                    return list(vector)
                except TimeoutError:
                    if future.done():
                        # A provider TimeoutError is a failure, not a polling timeout.
                        raise

        try:
            vector = tuple(float(value) for value in create())
            if (len(vector) != configuration[-1]
                    or not all(math.isfinite(value) for value in vector)
                    or not any(vector)):
                raise ValueError("Resume embedding must be a finite, nonzero vector of the configured size")
            raise_if_cancelled(cancel_check)
            with self._lock:
                if self._revision == revision:
                    self._entry = (key, vector)
            future.set_result(vector)
            return list(vector)
        except BaseException as exc:
            future.set_exception(exc)
            raise
        finally:
            with self._lock:
                self._pending.pop(pending_key, None)
