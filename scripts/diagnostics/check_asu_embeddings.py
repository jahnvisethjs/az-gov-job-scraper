"""Validate the configured ASU embeddings endpoint with one small request."""

import math
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import (  # noqa: E402
    ASU_AI_BASE_URL,
    ASU_AI_EMBEDDINGS_DIMENSIONS,
    ASU_AI_EMBEDDINGS_MODEL,
    ASU_AI_EMBEDDINGS_PROVIDER,
)
from rag.asu_ai_provider import ASUAIProvider  # noqa: E402


def main() -> int:
    api_key = os.getenv("ASU_AI_API_KEY")
    if not api_key:
        print("ASU_AI_API_KEY is not configured.", file=sys.stderr)
        return 1

    provider = ASUAIProvider(api_key=api_key, base_url=ASU_AI_BASE_URL)

    try:
        embedding = provider.generate_embedding_sync(
            "Arizona government employment",
            model=ASU_AI_EMBEDDINGS_MODEL,
            provider=ASU_AI_EMBEDDINGS_PROVIDER,
            dimensions=ASU_AI_EMBEDDINGS_DIMENSIONS,
        )
    except Exception as exc:
        print(f"ASU embeddings request failed: {exc}", file=sys.stderr)
        return 1

    is_valid = (
        isinstance(embedding, list)
        and len(embedding) == ASU_AI_EMBEDDINGS_DIMENSIONS
        and all(isinstance(value, (int, float)) and math.isfinite(value) for value in embedding)
    )
    if not is_valid:
        actual_size = len(embedding) if isinstance(embedding, list) else "not a list"
        print(f"Invalid embedding response; size={actual_size}.", file=sys.stderr)
        return 1

    print(
        "ASU embeddings succeeded: "
        f"provider={ASU_AI_EMBEDDINGS_PROVIDER}, "
        f"model={ASU_AI_EMBEDDINGS_MODEL}, "
        f"dimensions={len(embedding)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
