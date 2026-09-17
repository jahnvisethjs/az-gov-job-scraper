"""Run one minimal text-generation request through the configured ASU model."""

import asyncio
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import ASU_AI_BASE_URL, ASU_AI_MODEL  # noqa: E402
from rag.asu_ai_provider import ASUAIProvider  # noqa: E402


async def main() -> int:
    api_key = os.getenv("ASU_AI_API_KEY")
    if not api_key:
        print("ASU_AI_API_KEY is not configured.", file=sys.stderr)
        return 1

    provider = ASUAIProvider(
        api_key=api_key,
        base_url=ASU_AI_BASE_URL,
        model=ASU_AI_MODEL,
    )

    try:
        response = await provider.generate_content("Reply with exactly: OK")
    except Exception as exc:
        print(f"ASU query failed: {exc}", file=sys.stderr)
        return 1

    if response.strip() != "OK":
        print(f"ASU query returned an unexpected response: {response!r}", file=sys.stderr)
        return 1

    print(f"ASU query succeeded with model {ASU_AI_MODEL}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
